import boto3
import click
import json
import logging

boto3.set_stream_logger('', logging.INFO)

@click.group()
def cli():
    pass

@cli.command()
@click.argument('file', type=click.File('r'))
@click.argument('group')
@click.argument('state')
def run(file, group, state):
    output_file = json.load(file)

    # read all necessary info from output file

    # create new task with command override

    # fetch and output logs until exit

if __name__ == "__main__":
    cli()
