import boto3
import click
import json
import logging
import os
import requests
import time

from dotenv import load_dotenv
load_dotenv()


SLACK_CHANNEL = os.getenv('SLACK_CHANNEL')
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')


class ContextFilter(logging.Filter):
    def filter(self, record):
        context = getattr(record, 'context')
        record.context = ' - ' + json.dumps(context) if context else ''
        return True

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s%(context)s')

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.addFilter(ContextFilter())

boto3.set_stream_logger('', logging.INFO)

output_file = None

def notify_slack(text):
    if not SLACK_WEBHOOK_URL:
        return

    payload = {
        'text': text,
    }

    if SLACK_CHANNEL:
        payload['channel'] = SLACK_CHANNEL

    requests.post(SLACK_WEBHOOK_URL, json=payload)

def log(message, level=logging.ERROR, **context):
    logger.log(level, message, extra={'context': context})

def get_exit_code(containers):
    for container in containers:
        if  '-cli' in container['name']:
            exit_code = container.get('exitCode')
            if exit_code is None:
                log(f'could not find exit code for {container["name"]}', container=container)
                exit_code = 1
            return exit_code

@click.group()
@click.option('-f', type=click.File('rb'))
def cli(f):
    global output_file
    output_file = f
    pass

@cli.command(context_settings=dict(
    ignore_unknown_options=True,
    help_option_names=[],
))
@click.argument('command', nargs=-1, type=click.UNPROCESSED)
def run(command):
    terraform_output = json.load(output_file)

    if not type(terraform_output) is dict:
        log(f'unable to parse {output_file}')
        exit(1)

    for required_key in ['cluster_id', 'task_definition_arn', 'subnets', 'security_group_id']:
        if not required_key in terraform_output or len(terraform_output[required_key]) == 0:
            log(f'could not find the {required_key}... Aborting')
            exit(1)

    notify_slack(f'`terraecs run {" ".join(command)}` started')

    ecs_client = boto3.client('ecs')
    logs_client = boto3.client('logs')

    task_definition = ecs_client.describe_task_definition(
        taskDefinition=terraform_output['task_definition_arn']
    )

    log_options = task_definition['taskDefinition']['containerDefinitions'][0]['logConfiguration']['options']

    # create new task with command override
    response = ecs_client.run_task(
        cluster=terraform_output['cluster_id'],
        taskDefinition=terraform_output['task_definition_arn'],
        overrides={
            'containerOverrides': [
                {
                    'name': task_definition['taskDefinition']['containerDefinitions'][0]['name'],
                    'command': command,
                },
            ],
        },
        startedBy='terraecs',
        count=1,
        launchType='FARGATE',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': terraform_output['subnets'],
                'securityGroups': [terraform_output['security_group_id']],
                'assignPublicIp': 'DISABLED',
            }
        },
        propagateTags='TASK_DEFINITION',
    )

    task_arn = response['tasks'][0]['taskArn']
    task_id = task_arn.split('/')[-1]

    log(f'launched task: {task_arn}', logging.INFO)

    # fetch and output logs until exit
    next_forward_token = None
    last_status = None
    while True:
        response = ecs_client.describe_tasks(
            cluster=terraform_output['cluster_id'],
            tasks=[task_arn],
        )

        if not last_status == response['tasks'][0]['lastStatus']:
            log(response['tasks'][0]['lastStatus'], logging.INFO)

        last_status = response['tasks'][0]['lastStatus']

        sleep_seconds = 5
        if last_status in ['PROVISIONING', 'PENDING', 'DEPROVISIONING']:
            sleep_seconds = 10
        elif last_status in ['STOPPED', 'RUNNING', 'DEPROVISIONING']:
            get_log_events_kwargs = {
                'logGroupName': log_options['awslogs-group'],
                'logStreamName': f"{log_options['awslogs-stream-prefix']}/{task_definition['taskDefinition']['containerDefinitions'][0]['name']}/{task_id}",
                'startFromHead': True,
            }

            if not next_forward_token is None:
                get_log_events_kwargs['nextToken'] = next_forward_token

            log_events = logs_client.get_log_events(**get_log_events_kwargs)

            next_forward_token = log_events['nextForwardToken']

            if log_events['events']:
                for event in log_events['events']:
                    print(event['message'])

            if last_status == 'STOPPED':
                break

        time.sleep(sleep_seconds)

    exit_code = get_exit_code(response['tasks'][0]['containers'])

    notify_slack(f'`terraecs run {" ".join(command)}` finished with exit code {exit_code}')

    exit(exit_code)

if __name__ == "__main__":
    cli(None)
