#!/usr/bin/env python3

import typer
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from utils.logging import get_loggers
from utils.network import get_public_ip

# Get the loggers
loggers = get_loggers()

def status(ctx: typer.Context):
    loggers['debug'].debug(f"Executing {__name__} subcommand")

    try:
        # Initialize boto3 clients
        sts_client = boto3.client('sts')
        cw_client = boto3.client('cloudwatch')  # CloudWatch client for alarms

        # Get caller identity to verify AWS credentials
        identity = sts_client.get_caller_identity()

        # Get CloudWatch alarms status
        alarms_response = cw_client.describe_alarms()

        if not ctx.obj["QUIET"]:
            typer.echo(f"AWS Connection Established. Account ID: {identity['Account']}, ARN: {identity['Arn']}")
            typer.echo(f"Current IP Address: {get_public_ip()}")

            typer.echo("")

            typer.echo("CloudWatch Alarms Status:")
            alarmcount=0
            for alarm in alarms_response['MetricAlarms']:
                alarm_name = alarm['AlarmName']
                alarm_state = alarm['StateValue']
                alarm_reason = alarm['StateReason']
                if alarm_state != 'OK':
                    alarmcount += 1
                    typer.echo(f"Alarm Name: {alarm_name}, State: {alarm_state} Reason: {alarm_reason}")
            if alarmcount == 0:
                typer.echo("No alarms in alarm state.")

    except NoCredentialsError:
        typer.echo("No AWS credentials found. Please configure them properly.")
    except PartialCredentialsError:
        typer.echo("Incomplete AWS credentials. Please check your configuration.")
    except ClientError as e:
        typer.echo(f"AWS Connection Error: {e}")

if __name__ == "__main__":
    typer.run(status)
