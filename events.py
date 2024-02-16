#!/usr/bin/env python3

import typer
from utils.logging import get_loggers
from utils.amazon import get_aws_client
from SauceData.handler import SauceData
from datetime import datetime, timedelta
import json
from botocore.exceptions import ClientError

# Get the loggers
loggers = get_loggers()

app = typer.Typer()

def validate_time_range(start_time: datetime, end_time: datetime):
    """Validate that start_time is before end_time."""
    if start_time >= end_time:
        raise typer.Exit("Start time must be before end time.")

@app.command()
def events(
    ctx: typer.Context,
    start_time: str = typer.Option(
        None,
        help="Start time for the events in 'YYYY-MM-DD HH:MM:SS' format. Defaults to 24 hours ago.",
    ),
    end_time: str = typer.Option(
        None,
        help="End time for the events in 'YYYY-MM-DD HH:MM:SS' format. Defaults to now.",
    ),
):
    loggers['debug'].debug(f"Executing {__name__} subcommand")

    dry_run = ctx.obj["DRY_RUN"]
    quiet = ctx.obj["QUIET"]
    force = ctx.obj["FORCE"]
    output = ctx.obj["OUTPUT"]
    ofile = ctx.obj["OFILE"]

    # Parsing start_time and end_time
    now = datetime.now()
    start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S') if start_time else now - timedelta(days=1)
    end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S') if end_time else now

    # Validate time range
    validate_time_range(start_time, end_time)

    # create the SauceData object
    sauce_data = SauceData()

    # create the cloudtrail client
    ctclient = get_aws_client(ctx, 'cloudtrail')

    loggers['debug'].debug(f"Start time: {start_time}, End time: {end_time}")

    try:
        # Convert start_time and end_time to the string format required by CloudTrail
        start_time_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_time_str = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')

        # Fetch CloudTrail events
        response = ctclient.lookup_events(
            LookupAttributes=[],
            StartTime=start_time,
            EndTime=end_time,
            MaxResults=50  # Adjust as needed
        )

        allevents = []
        # if the response includes the NextToken, fetch the next page of results
        while 'NextToken' in response:
            allevents.extend(response['Events'])
            response = ctclient.lookup_events(
                LookupAttributes=[],
                StartTime=start_time,
                EndTime=end_time,
                NextToken=response['NextToken'],
                MaxResults=50  # Adjust as needed
            )
        
        # append the last page of results
        allevents.extend(response['Events'])

        # parse the event string to json
        for event in allevents:
            event['CloudTrailEvent'] = json.loads(event['CloudTrailEvent'])

        # print the count of events
        typer.echo(f"Found {len(allevents)} events in the time range.")

        # sort by date
        allevents = sorted(allevents, key=lambda event: event['EventTime'])

        # exclude events for one amazon service communicating with another
        # in short, exclude events where the source and the recipient are both AWS services
        allevents = [event for event in allevents if not event['CloudTrailEvent']['userIdentity']['type'] == 'AWSService']

        for event in allevents:
            event_data = {
                'EventId': event['EventId'],
                'Username': event['Username'],
                'EventTime': event['EventTime'].strftime('%Y-%m-%d %H:%M:%S'),
                'awsRegion': event['CloudTrailEvent']['awsRegion'],
                'eventName': event['CloudTrailEvent']['eventName'],
                'eventSource': event['CloudTrailEvent']['eventSource'].split('.')[0],
                'eventType': event['CloudTrailEvent']['eventType'],
                'sourceIPAddress': event['CloudTrailEvent']['sourceIPAddress'],
                'accessKeyId': event['CloudTrailEvent']['userIdentity']['accessKeyId'],
            }
            sauce_data.append(event_data)
            #print (json.dumps(event_data, indent=4, sort_keys=True, default=str))

            # set headerlabels
            sauce_data.headerlabels = {
                'EventId': 'Event ID',
                'Username': 'Username',
                'EventTime': 'Event Time',
                'awsRegion': 'Region',
                'eventName': 'Event',
                'eventSource': 'Source',
                'eventType': 'EventTyp',
                'sourceIPAddress': 'IP',
                'accessKeyId': 'Key ID'
            }

    except ClientError as e:
        loggers['error'].error(f"An AWS ClientError occurred: {e}")
    except Exception as e:
        loggers['error'].error(f"An unexpected error occurred: {e}")

    # print the count of filtered events
    typer.echo(f"Found {len(allevents)} events remaining.")
    # print the count of filtered events
    #print (json.dumps(allevents, indent=4, sort_keys=True, default=str))
    typer.echo( sauce_data )
    
    # Pretty-print the JSON response and sort by EventTime
    #print(json.dumps(allevents, indent=4, sort_keys=True, default=str))

if __name__ == "__main__":
    typer.run(events)

