"""lambda handler to recount cli execution counts"""

import logging
import sqlalchemy
from sqlalchemy.orm import Session
from . import models
from . import utils

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# pylint: disable=not-callable
def lambda_handler(event, context):  # pylint: disable=unused-argument
    """lambda function to process cli execution recount"""

    logger.info(event)

    DB_USER_NAME, DB_USER_PASS, DB_HOST, DB_NAME, REGION = utils.get_db_info()  # pylint: disable=unused-variable
    engine = utils.get_engine(DB_USER_NAME, DB_USER_PASS, DB_HOST, DB_NAME)

    with Session(engine) as session:

        recount_clis = session.query(models.CliExecutions).filter_by(needs_recount=True)

        for cli in recount_clis:

            dmrpp_fails = session.query(sqlalchemy.func.count(models.StepExecution.execution_name)).filter_by(
                status="FAILED", sf_type="DMRPP", cli_execution=cli.uuid).scalar()
            dmrpp_success = session.query(sqlalchemy.func.count(models.StepExecution.execution_name)).filter_by(
                status="SUCCEEDED", sf_type="DMRPP", cli_execution=cli.uuid).scalar()

            tig_fails = session.query(sqlalchemy.func.count(models.StepExecution.execution_name)).filter_by(
                status="FAILED", sf_type="TIG", cli_execution=cli.uuid).scalar()
            tig_success = session.query(sqlalchemy.func.count(models.StepExecution.execution_name)).filter_by(
                status="SUCCEEDED", sf_type="TIG", cli_execution=cli.uuid).scalar()

            forge_fails = session.query(sqlalchemy.func.count(models.StepExecution.execution_name)).filter_by(
                status="FAILED", sf_type="FORGE", cli_execution=cli.uuid).scalar()
            forge_success = session.query(sqlalchemy.func.count(models.StepExecution.execution_name)).filter_by(
                status="SUCCEEDED", sf_type="FORGE", cli_execution=cli.uuid).scalar()

            cli.dmrpp_fails = dmrpp_fails
            cli.dmrpp_success = dmrpp_success
            cli.tig_fails = tig_fails
            cli.tig_success = tig_success
            cli.forge_fails = forge_fails
            cli.forge_success = forge_success
            cli.needs_recount = False

            session.commit()

    utils.close_connections(engine)
