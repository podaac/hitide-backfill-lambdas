"""
==============
test_hitide_backfill_sqs_to_step.py
==============

Test lambda handler creates stepfunction execution.
"""

import os
import unittest
import boto3
import json
from moto import mock_sts, mock_stepfunctions, mock_sqs, mock_ssm
from podaac.hitide_backfill_sqs_to_step import lambda_handler
import multiprocessing as mp

region = "us-west-2"
simple_definition = (
    '{"Comment": "An example of the Amazon States Language using a choice state.",'
    '"StartAt": "DefaultState",'
    '"States": '
    '{"DefaultState": {"Type": "Fail","Error": "DefaultStateError","Cause": "No Matches!"}}}'
)
account_id = None

step_input = {
    "cumulus_meta": {
    },
    "tig": True,
    "forge": True,
    "dmrpp": True
}

@mock_ssm
@mock_sqs
@mock_stepfunctions
@mock_sts
class TestHitideBackfillSqsToStep(unittest.TestCase):

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

    def setup_method(self, method):
        self.client = boto3.client("stepfunctions", region_name=region)
        name = "forge_tig"
        response = self.client.create_state_machine(
            name=name, definition=str(simple_definition), roleArn=self._get_default_role()
        )
        self.state_machine_arn = response["stateMachineArn"]

        sqs = boto3.resource('sqs', region_name=region)
        self.queue = sqs.create_queue(QueueName='test_queue')

        self.ssm_client = boto3.client("ssm", region_name="us-west-2")
        self.ssm_client.put_parameter(
            Name="throttle_limit", Description="A test parameter", Value="1", Type="String"
        )
        mp.set_start_method('fork', force=True)

    def teardown_method(self, method):
        self.client.delete_state_machine(stateMachineArn=self.state_machine_arn)
        self.queue.delete()
        self.ssm_client.delete_parameter(Name="throttle_limit")

    def test_create_stepfunctions(self):

        step_input['forge'] = True
        step_input['tig'] = True
        step_input['dmrpp'] = True

        body = json.dumps({'Message': json.dumps(step_input)})
        sqs_input = {'Records': [{'body': body}]}

        self.queue.send_message(MessageBody=body)
        self.queue.send_message(MessageBody=body)

        process_num_messages = 1
        sqs_url = os.environ.get("SQS_URL")
        sqs_client = boto3.client('sqs')
        client = boto3.client('stepfunctions')
        tig_step_arn = self.state_machine_arn
        forge_step_arn = self.state_machine_arn
        dmrpp_step_arn = self.state_machine_arn
        visibility_timeout = 1500
        conn = None
        lambda_handler.create_stepfunctions(process_num_messages, sqs_url, sqs_client, client, tig_step_arn, forge_step_arn, dmrpp_step_arn, visibility_timeout, conn)

        executions = self.client.list_executions(stateMachineArn=self.state_machine_arn)
        execution_arn = executions.get('executions')[0].get('executionArn')
        execution_description = self.client.describe_execution(executionArn=execution_arn)
        execution_input = json.loads(execution_description.get('input'))

        assert len(executions.get('executions')) == 3
        assert execution_input['cumulus_meta']['execution_name']

    def test_no_create_stepfunctions(self):

        step_input['forge'] = False
        step_input['tig'] = False
        step_input['dmrpp'] = False

        body = json.dumps({'Message': json.dumps(step_input)})
        sqs_input = {'Records': [{'body': body}]}

        self.queue.send_message(MessageBody=body)

        process_num_messages = 1
        sqs_url = os.environ.get("SQS_URL")
        sqs_client = boto3.client('sqs')
        client = boto3.client('stepfunctions')
        tig_step_arn = self.state_machine_arn
        forge_step_arn = self.state_machine_arn
        dmrpp_step_arn = self.state_machine_arn
        visibility_timeout = 1500
        conn = None
        lambda_handler.create_stepfunctions(process_num_messages, sqs_url, sqs_client, client, tig_step_arn, forge_step_arn, dmrpp_step_arn, visibility_timeout, conn)

        executions = self.client.list_executions(stateMachineArn=self.state_machine_arn)
        assert len(executions.get('executions')) == 0


if __name__ == '__main__':
    unittest.main()