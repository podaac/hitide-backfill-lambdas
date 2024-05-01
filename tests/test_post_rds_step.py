from sqlalchemy.orm import Session
import sqlalchemy
import podaac.hitide_backfill_post_step.models as models
from sqlalchemy.orm import Session
import unittest
import pytest
import podaac.hitide_backfill_post_step.lambda_handler as lambda_handler
import podaac.hitide_backfill_post_step.utils as utils
import json
import boto3
from moto import mock_aws

from mock import patch
import os

from sqlalchemy.orm import sessionmaker


engine = None
account_id = None
region = os.environ.get("REGION")

simple_definition = (
    '{"Comment": "An example of the Amazon States Language using a choice state.",'
    '"StartAt": "DefaultState",'
    '"States": '
    '{"DefaultState": {"Type": "Fail","Error": "DefaultStateError","Cause": "No Matches!"}}}'
)

def overwrite_get_engine(db_user_name, db_user_pass, db_host, db_name):

    global engine
    engine = sqlalchemy.create_engine("sqlite://", echo=True)
    models.Base.metadata.create_all(engine)
    return engine

def overwrite_close_connections(engine):
   pass

def generate_input(step_arn, status):

    lambda_input = {
        "Records": [
            {"body":
                json.dumps(
                    {"detail": {
                            "input": json.dumps({
                                "cumulus_meta": {
                                    "execution_name": "12345"
                                },
                                "execution_times": 1,
                                "payload": {
                                    "granules": [
                                        {
                                            "cmrConceptId": "FAKE_CMR_CONCEPT_ID",
                                            "granuleId": "FAKE_GRANULE_ID",
                                            "dataType": "FAKE_COLLECTION"
                                        }
                                    ]
                                },
                                "meta": {
                                    "collection": {
                                        "version": "1.0"
                                    }
                                },
                                "cli_params": {
                                    "uuid": '12345',
                                    "granule_start": "2014-10-10T06:40:00.000Z",
                                    "granule_end": "2014-10-10T06:40:00.000Z"
                                },
                                "sqs_data": {
                                    "execution_times": 1
                                }
                            }),
                            "status": status,
                            "stateMachineArn": step_arn,
                            "startDate": 1000,
                            "stopDate": 1000
                        }
                    }
                )
             }
        ]
    }
    return lambda_input

@mock_aws
class TestHitideBackfillPostStep(unittest.TestCase):

    def setup_method(self, method):
        """set up aws resources for test"""

        client = boto3.client("ssm", region_name=region)

        client.put_parameter(
            Name="user", Description="A test parameter", Value="value", Type="String"
        )
        client.put_parameter(
            Name="pass", Description="A test parameter", Value="value", Type="String"
        )
        client.put_parameter(
            Name="db_name", Description="A test parameter", Value="value", Type="String"
        )
        client.put_parameter(
            Name="db_host", Description="A test parameter", Value="value", Type="String"
        )

        self.client = boto3.client("stepfunctions", region_name=region)
        
        response = self.client.create_state_machine(
            name="tig", definition=str(simple_definition), roleArn=self._get_default_role()
        )
        self.tig_state_machine_arn = response["stateMachineArn"]

        response = self.client.create_state_machine(
            name="forge", definition=str(simple_definition), roleArn=self._get_default_role()
        )
        self.forge_state_machine_arn = response["stateMachineArn"]

        sqs = boto3.resource('sqs', region_name=region)
        self.queue = sqs.create_queue(QueueName='test_queue')

    def _get_account_id(self):
        global account_id
        if account_id:
            return account_id
        sts = boto3.client("sts", region_name=region)
        identity = sts.get_caller_identity()
        account_id = identity["Account"]
        return account_id

    def _get_default_role(self):
        return "arn:aws:iam::" + self._get_account_id() + ":role/unknown_sf_role"

    def teardown_method(self, method):
        """clean up and dispose memory database"""

        if engine:
            engine.dispose()

        self.client.delete_state_machine(stateMachineArn=self.tig_state_machine_arn)
        self.client.delete_state_machine(stateMachineArn=self.forge_state_machine_arn)
        self.queue.delete()

    def test_forge_success(self):

        utils.get_engine = overwrite_get_engine
        utils.close_connections = overwrite_close_connections
        test_input = generate_input(self.forge_state_machine_arn, 'SUCCEEDED')
        lambda_handler.lambda_handler(test_input, None)

        if engine:
            with Session(engine) as session:
                cli = session.query(models.CliExecutions).filter_by(uuid=12345).count()
                step = session.query(models.StepExecution).filter_by(granule="FAKE_CMR_CONCEPT_ID", sf_type="FORGE", status="SUCCEEDED").count()
                granule = session.query(models.Granule).filter_by(cmr_concept_id="FAKE_CMR_CONCEPT_ID").count()

            assert cli == 1
            assert step == 1
            assert granule == 1

    def test_tig_success(self):

        utils.get_engine = overwrite_get_engine
        utils.close_connections = overwrite_close_connections
        test_input = generate_input(self.tig_state_machine_arn, 'SUCCEEDED')
        lambda_handler.lambda_handler(test_input, None)

        if engine:
            with Session(engine) as session:
                cli = session.query(models.CliExecutions).filter_by(uuid=12345).count()
                step = session.query(models.StepExecution).filter_by(granule="FAKE_CMR_CONCEPT_ID", sf_type="TIG", status="SUCCEEDED").count()
                granule = session.query(models.Granule).filter_by(cmr_concept_id="FAKE_CMR_CONCEPT_ID").count()

            assert cli == 1
            assert step == 1
            assert granule == 1

    def test_forge_fail(self):

        utils.get_engine = overwrite_get_engine
        utils.close_connections = overwrite_close_connections
        test_input = generate_input(self.forge_state_machine_arn, 'FAILED')
        lambda_handler.lambda_handler(test_input, None)

        if engine:
            with Session(engine) as session:
                cli = session.query(models.CliExecutions).filter_by(uuid=12345).count()
                step = session.query(models.StepExecution).filter_by(granule="FAKE_CMR_CONCEPT_ID", sf_type="FORGE", status="FAILED").count()
                granule = session.query(models.Granule).filter_by(cmr_concept_id="FAKE_CMR_CONCEPT_ID").count()

            assert cli == 1
            assert step == 1
            assert granule == 1

    def test_tig_fail(self):

        utils.get_engine = overwrite_get_engine
        utils.close_connections = overwrite_close_connections
        test_input = generate_input(self.tig_state_machine_arn, 'FAILED')
        lambda_handler.lambda_handler(test_input, None)

        if engine:
            with Session(engine) as session:
                cli = session.query(models.CliExecutions).filter_by(uuid=12345).count()
                step = session.query(models.StepExecution).filter_by(granule="FAKE_CMR_CONCEPT_ID", sf_type="TIG", status="FAILED").count()
                granule = session.query(models.Granule).filter_by(cmr_concept_id="FAKE_CMR_CONCEPT_ID").count()

            assert cli == 1
            assert step == 1
            assert granule == 1

