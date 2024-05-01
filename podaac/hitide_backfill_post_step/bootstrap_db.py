"""lambda handler to generate user and tables for backfill database"""

import pymysql
import sqlalchemy
from .models import Base
from . import utils


def create_user(host, root_user, root_pass, new_user, user_pass, db_name):
    """Function to create database user and grant permission to db"""

    cnx = pymysql.connect(
        host=host,
        port=3306,
        user=root_user,
        password=root_pass
    )

    create_user_sql = f"CREATE USER IF NOT EXISTS {new_user} IDENTIFIED BY '{user_pass}'"
    grant_access_sql = f"GRANT DELETE, INSERT, SELECT, UPDATE ON {db_name}.* TO '{new_user}'"

    mycursor = cnx.cursor()
    mycursor.execute(create_user_sql)
    mycursor.execute(grant_access_sql)

    cnx.close()


def lambda_handler(event, context):  # pylint: disable=unused-argument, disable-msg=too-many-locals
    """main function for lambda to execute"""

    DB_USER_NAME, DB_USER_PASS, DB_HOST, DB_NAME, REGION = utils.get_db_info()  # pylint: disable=unused-variable
    DB_ROOT_USER, DB_ROOT_PASS = utils.get_db_root_info()

    print("Creating User .....")
    create_user(DB_HOST, DB_ROOT_USER, DB_ROOT_PASS, DB_USER_NAME, DB_USER_PASS, DB_NAME)

    db_url = f'mysql+pymysql://{DB_ROOT_USER}:{DB_ROOT_PASS}@{DB_HOST}/{DB_NAME}'
    engine = sqlalchemy.create_engine(db_url)

    print("Creating Tables .....")
    Base.metadata.create_all(engine)
    print("Finished deploying database user and tables")

    # Create DMRPP columns for existing database that didn't have before
    try:
        connection = engine.connect()
        query = "ALTER TABLE `hitidebackfilldb`.`cli_execution` ADD COLUMN `dmrpp_success` INT(11) NULL DEFAULT NULL, ADD COLUMN `dmrpp_fails` INT(11) NULL DEFAULT NULL;"
        connection.execute(query)
    except Exception as ex:  # pylint: disable=broad-except
        print(ex)
        print("DMRPP columns exists")
    finally:
        connection.close()

    # Create needs_recount columns for existing database that didn't have before
    try:
        connection = engine.connect()
        query = "ALTER TABLE `hitidebackfilldb`.`cli_execution` ADD COLUMN `needs_recount` TinyInt(1) NOT NULL DEFAULT 0;"
        connection.execute(query)
    except Exception as ex:  # pylint: disable=broad-except
        print(ex)
        print("needs_recount columns exists")
    finally:
        connection.close()
