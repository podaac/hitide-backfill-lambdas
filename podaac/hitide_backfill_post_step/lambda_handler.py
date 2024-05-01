"""lambda handler for processing result of step function execution"""

import json
import os
import datetime
import logging
import boto3
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from dateutil import parser
from . import models
from . import utils


DB_USER_NAME = DB_USER_PASS = DB_HOST = DB_NAME = REGION = None

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):  # pylint: disable=unused-argument, disable-msg=too-many-locals
    """main function for lambda to execute"""

    logger.info(event)

    global DB_USER_NAME
    global DB_USER_PASS
    global DB_HOST
    global DB_NAME
    global REGION

    if not (DB_USER_NAME and DB_USER_PASS and DB_HOST and DB_NAME and REGION):
        DB_USER_NAME, DB_USER_PASS, DB_HOST, DB_NAME, REGION = utils.get_db_info()

    engine = utils.get_engine(DB_USER_NAME, DB_USER_PASS, DB_HOST, DB_NAME)

    for record in event.get('Records'):

        message = json.loads(record.get('body'))

        step_retry = int(os.environ.get("STEP_RETRY"))
        tig_step_arn = os.environ.get("TIG_STEP_ARN")
        forge_step_arn = os.environ.get("FORGE_STEP_ARN")
        dmrpp_step_arn = os.environ.get("DMRPP_STEP_ARN")
        sqs_url = os.environ.get("SQS_URL")

        detail = message.get('detail')
        cma_input = json.loads(detail.get('input'))

        status = detail.get('status')
        granule = cma_input.get('payload').get('granules')[0]
        cmr_concept_id = granule.get('cmrConceptId')
        granule_id = granule.get('granuleId')
        collection_short_name = granule.get('dataType')
        collection_version = cma_input.get('meta').get('collection').get('version')
        execution_name = cma_input.get('cumulus_meta').get('execution_name')
        step_arn = detail.get('stateMachineArn')
        cli_params = cma_input.get('cli_params')
        sqs_data = cma_input.get('sqs_data')
        execution_times = int(sqs_data.get('execution_times'))

        sf_epoch_start_time = detail.get('startDate')/1000
        sf_epoch_end_time = detail.get('stopDate')/1000

        sf_start_time = datetime.datetime.fromtimestamp(sf_epoch_start_time)
        sf_end_time = datetime.datetime.fromtimestamp(sf_epoch_end_time)

        cli_execution_start_time = cli_params.get('cmr_search_start')
        cli_execution_end_time = cli_params.get('cmr_search_end')

        if cli_execution_start_time:
            cli_execution_start_time = parser.parse(cli_execution_start_time)

        if cli_execution_end_time:
            cli_execution_end_time = parser.parse(cli_execution_end_time)

        cli_execution_uuid = cli_params.get('uuid')
        cli_execution_username = cli_params.get('username')
        granule_start_time = parser.parse(cli_params.get('granule_start'))
        granule_end_time = parser.parse(cli_params.get('granule_end'))

        if step_arn == tig_step_arn:
            sf_type = "TIG"
        elif step_arn == forge_step_arn:
            sf_type = "FORGE"
        elif step_arn == dmrpp_step_arn:
            sf_type = "DMRPP"

        with Session(engine) as session:

            if cli_execution_uuid is not None:
                cli_execution = cli_execution_get_or_create(session, cli_execution_uuid, cli_execution_username, collection_short_name,
                                                            collection_version, cli_execution_start_time, cli_execution_end_time)
            else:
                logger.error('Execution uuid is NONE failed to record in database')

            if cmr_concept_id is not None and cli_execution_uuid is not None:
                granule = granule_get_or_create(session, cmr_concept_id, collection_short_name, collection_version, granule_id, granule_start_time, granule_end_time)
            else:
                logger.error('CMR concept id is NONE failed to record in database')

            if execution_name is not None and cli_execution_uuid is not None:
                step_execution_create_or_update(session, execution_name, granule.cmr_concept_id, cli_execution_uuid, sf_type, status, sf_start_time, sf_end_time)
            else:
                logger.error('Execution name is NONE failed to record in database')

            if status == "SUCCEEDED" and cli_execution_uuid and cli_execution:
                if sf_type == "TIG":
                    cli_execution.tig_success += 1
                elif sf_type == "FORGE":
                    cli_execution.forge_success += 1
                elif sf_type == "DMRPP" and cli_execution_uuid:
                    cli_execution.dmrpp_success += 1

            elif status == "FAILED" and execution_times >= step_retry and cli_execution:
                if sf_type == "TIG" and cli_execution_uuid:
                    cli_execution.tig_fails += 1
                elif sf_type == "FORGE" and cli_execution_uuid:
                    cli_execution.forge_fails += 1
                elif sf_type == "DMRPP" and cli_execution_uuid:
                    cli_execution.dmrpp_fails += 1

            if cli_execution:
                cli_execution.last_updated = func.current_timestamp()  # pylint: disable=not-callable
                cli_execution.needs_recount = True

            session.commit()

        # Dispose of engine to make sure all mysql connections are closed
        utils.close_connections(engine)

        # Retry at the end so if anything fail above won't keep retriggering
        sqs_client = boto3.client('sqs')

        if status == "FAILED":

            try:
                sqs_client.change_message_visibility(
                    QueueUrl=sqs_url,
                    ReceiptHandle=sqs_data.get('handle'),
                    VisibilityTimeout=0
                )
            except Exception as ex:  # pylint: disable=broad-except
                logger.error(ex)

        elif status == "SUCCEEDED":

            try:
                sqs_client.delete_message(
                    QueueUrl=sqs_url,
                    ReceiptHandle=sqs_data.get('handle'),
                )
            except Exception as ex:  # pylint: disable=broad-except
                logger.error(ex)


def cli_execution_get_or_create(session, execution_uuid, username, short_name, version, start, end):
    """Get or create cli execution in database"""

    args = {
        "uuid": execution_uuid,
        "username": username,
        "collection_short_name": short_name,
        "collection_version": version,
        "cmr_search_start": start,
        "cmr_search_end": end
    }

    instance = session.query(models.CliExecutions).filter_by(uuid=execution_uuid).with_for_update().first()
    if not instance:
        new_execution = models.CliExecutions(**args)
        session.add(new_execution)
        session.commit()
        return new_execution

    return instance


def step_execution_create_or_update(session, execution_name, cmr_concept_id, cli_execution, sf_type, status, start, stop):
    """Create or update step function execution in database"""

    args = {
        "execution_name": execution_name,
        "granule": cmr_concept_id,
        "cli_execution": cli_execution,
        "sf_type": sf_type,
        "status": status,
        "execution_start": start,
        "execution_stop": stop
    }

    instance = session.query(models.StepExecution).filter_by(granule=cmr_concept_id, sf_type=sf_type, cli_execution=cli_execution).first()

    if not instance:
        new_execution = models.StepExecution(**args)
        session.add(new_execution)
        session.commit()
        return new_execution

    instance.execution_name = execution_name
    instance.cli_execution = cli_execution
    instance.status = status
    instance.execution_start = start
    instance.execution_stop = stop
    session.commit()
    return instance


def granule_get_or_create(session, cmr_concept_id, short_name, version, granule_id, start, end):
    """Get or Create granule in database"""

    args = {
        "cmr_concept_id": cmr_concept_id,
        "collection_short_name": short_name,
        "collection_version": version,
        "granule_id": granule_id,
        "granule_start": start,
        "granule_end": end
    }

    instance = session.query(models.Granule).filter_by(cmr_concept_id=cmr_concept_id).first()
    if not instance:
        new_granule = models.Granule(**args)
        session.add(new_granule)
        session.commit()
        return new_granule

    return instance
