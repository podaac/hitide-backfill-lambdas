# pylint: disable=too-many-locals

"""lambda handler for converting sqs message to stepfunction message"""

import json
import uuid
import os
import logging
import math
import multiprocessing as mp
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def create_single_step(cma_message, step_arn, client):
    """function to create a single step function"""

    new_execution_name = str(uuid.uuid4())
    cma_message['cumulus_meta']['execution_name'] = new_execution_name
    logger.info(cma_message)
    client.start_execution(
        stateMachineArn=step_arn,
        name=new_execution_name,
        input=json.dumps(cma_message),
    )


def create_stepfunctions(process_num_messages, sqs_url, sqs_client, client,  tig_step_arn,
                         forge_step_arn, dmrpp_step_arn, visibility_timeout, conn=None):
    """multi process function to create all step functions"""

    for _ in range(process_num_messages):
        sqs_messages = sqs_client.receive_message(QueueUrl=sqs_url, VisibilityTimeout=visibility_timeout,
                                                  WaitTimeSeconds=20, AttributeNames=['All'])

        for message in sqs_messages.get('Messages'):

            execution_times = message.get('Attributes').get('ApproximateReceiveCount')
            message_handle = message.get('ReceiptHandle')

            cma_message = json.loads(json.loads(message.get('Body')).get('Message'))
            run_tig = cma_message.get('tig')
            run_forge = cma_message.get('forge')
            run_dmrpp = cma_message.get('dmrpp')
            cma_message["sqs_data"] = {
                "execution_times": execution_times,
                "handle": message_handle
            }

            if run_tig:
                create_single_step(cma_message, tig_step_arn, client)

            if run_forge:
                create_single_step(cma_message, forge_step_arn, client)

            if run_dmrpp:
                create_single_step(cma_message, dmrpp_step_arn, client)

    if conn:
        conn.close()


def lambda_handler(event, context):  # pylint: disable=unused-argument
    """lambda handler for converting sqs message to stepfunction message"""

    forge_step_arn = os.environ.get("FORGE_STEP_ARN")
    tig_step_arn = os.environ.get("TIG_STEP_ARN")
    dmrpp_step_arn = os.environ.get("DMRPP_STEP_ARN")
    sqs_url = os.environ.get("SQS_URL")
    region = os.environ.get('region', 'us-west-2')

    ssm_throttle_limit_name = os.environ.get('SSM_THROTTLE_LIMIT')
    ssm = boto3.client('ssm', region_name=region)
    ssm_throttle_limit = ssm.get_parameter(
        Name=ssm_throttle_limit_name, WithDecryption=True
    )
    max_processing_messages = int(ssm_throttle_limit['Parameter']['Value'])

    client = boto3.client('stepfunctions')

    sqs_client = boto3.client('sqs')
    queue_attributes = sqs_client.get_queue_attributes(QueueUrl=sqs_url, AttributeNames=["All"])

    num_invis_message = queue_attributes.get('Attributes').get('ApproximateNumberOfMessagesNotVisible')
    messages_in_queue = int(queue_attributes.get('Attributes').get('ApproximateNumberOfMessages'))
    process_num_total_messages = min(messages_in_queue, max_processing_messages - int(num_invis_message))
    visibility_timeout = int(os.environ.get('VISIBILITY_TIMEOUT', '1200'))

    logger.info('num messages processing : %s', num_invis_message)
    logger.info('num messages in queue  : %s', messages_in_queue)
    logger.info('num messages to process: %s', process_num_total_messages)

    process_messages_list = [math.ceil(process_num_total_messages/2), math.floor(process_num_total_messages/2)]

    if process_num_total_messages > 0:

        parent_connections = []
        processes = []

        for process_num_messages in process_messages_list:
            if process_num_messages > 0:
                parent_conn, child_conn = mp.Pipe()
                parent_connections.append(parent_conn)

                process = mp.Process(target=create_stepfunctions, args=(process_num_messages, sqs_url,
                                     sqs_client, client, tig_step_arn, forge_step_arn, dmrpp_step_arn,
                                     visibility_timeout, child_conn))
                processes.append(process)

        for process in processes:
            process.start()

        # make sure that all processes have finished
        for process in processes:
            process.join()
