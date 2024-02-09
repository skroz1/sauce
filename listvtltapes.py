#!/usr/bin/env python3

import typer
import boto3
#from tabulate import tabulate
from utils.utilities import get_terminal_width, fit_table_columns, convert_bytes
from utils.logging import get_loggers
from utils.amazon import get_aws_session, get_aws_client
from botocore.exceptions import ClientError
import sys
from datetime import datetime
from SauceData.handler import SauceData

app = typer.Typer()

def list_tapes(ctx:typer.Context, gateway_arns: str=None) -> SauceData:
    tapes = SauceData()
    #headers = ["TapeBarcode", "TapeCreatedDate", "TapeSizeInBytes", "TapeStatus", "TapeUsedInBytes", "PoolId", "Worm", "PoolEntryDate", "GatewayARN"]

    #client = boto3.client('storagegateway')
    client = get_aws_client(ctx, 'storagegateway')
    response = client.list_tapes()
    for tape_info in response['TapeInfos']:
        tape_arn = tape_info['TapeARN']

        # Process only tapes that have an associated GatewayARN
        if 'GatewayARN' in tape_info:
            try:
                tape_response = client.describe_tapes(GatewayARN=tape_info['GatewayARN'], TapeARNs=[tape_arn])
                tape_data = tape_response['Tapes'][0]
                if gateway_arns is None or gateway_arns == [] or tape_info['GatewayARN'] in gateway_arns:
                    tapes.append({
                        'TapeBarcode': tape_data['TapeBarcode'],
                        'TapeCreatedDate': tape_data['TapeCreatedDate'],
                        'TapeSizeInBytes': tape_data['TapeSizeInBytes'],
                        'TapeStatus': tape_data['TapeStatus'],
                        'TapeUsedInBytes': tape_data['TapeUsedInBytes'],
                        'PoolId': tape_data['PoolId'],
                        'Worm': tape_data['Worm'],
                        'PoolEntryDate': tape_data['PoolEntryDate'],
                        'GatewayARN': tape_info['GatewayARN']
                    })
            except ClientError as e:
                print(f"Failed to retrieve tape details for {tape_arn}: {e}", file=sys.stderr)
                continue
        else:
            try:
                tape_response = client.describe_tape_archives(TapeARNs=[tape_arn])
                tape_data = tape_response['TapeArchives'][0]
                tapes.append({
                    'TapeBarcode': tape_data['TapeBarcode'],
                    'TapeCreatedDate': tape_data['TapeCreatedDate'],
                    'TapeSizeInBytes': tape_data['TapeSizeInBytes'],
                    'TapeStatus': tape_data['TapeStatus'],
                    'TapeUsedInBytes': tape_data['TapeUsedInBytes'],
                    'PoolId': tape_data['PoolId'],
                    'Worm': tape_data['Worm'],
                    'PoolEntryDate': tape_data['PoolEntryDate'],
                    'GatewayARN': None
                })
            except ClientError as e:
                print(f"Failed to retrieve tape archive details for {tape_arn}: {e}", file=sys.stderr)
                continue

    # build the header labels
    tapes.headerlabels = {
        "TapeBarcode": "Tape Barcode",
        "TapeCreatedDate": "Created Date",
        "TapeSizeInBytes": "Size in Bytes",
        "TapeStatus": "Status",
        "TapeUsedInBytes": "Used Bytes",
        "PoolId": "Pool ID",
        "Worm": "WORM",
        "PoolEntryDate": "Pool Entry Date",
        "GatewayARN": "Gateway ARN"
    }

    return tapes

def format_tape_data(data: SauceData, units: str = "GiB"):
    modified_headers = data.headerlabels.copy()
    modified_tapes = []

    # Convert TapeCreatedDate and PoolEntryDate to date and time only
    for tape in data.data:
        if isinstance(tape['TapeCreatedDate'], str):
            tape['TapeCreatedDate'] = datetime.fromisoformat(tape['TapeCreatedDate'])
        tape['TapeCreatedDate'] = tape['TapeCreatedDate'].strftime("%Y-%m-%d %H:%M")  # Format to date and time only

        if isinstance(tape['PoolEntryDate'], str):
            tape['PoolEntryDate'] = datetime.fromisoformat(tape['PoolEntryDate'])
        tape['PoolEntryDate'] = tape['PoolEntryDate'].strftime("%Y-%m-%d %H:%M")  # Format to date and time only

        # convert the GatewayARN to just the gateway ID if defined
        if tape['GatewayARN'] is not None:
            tape['GatewayARN'] = tape['GatewayARN'].split('/')[-1]

        # Convert TapeSizeInBytes and TapeUsedInBytes to specified units
        tape['TapeSizeInBytes'] = format(convert_bytes(tape['TapeSizeInBytes'], units), ".1f")
        tape['TapeUsedInBytes'] = format(convert_bytes(tape['TapeUsedInBytes'], units), ".1f")

        modified_tapes.append(tape)

    # Modify the corresponding header name in headers to reflect the new units
    modified_units = units[0].capitalize() + units[1:-1] + units[-1].capitalize()
    modified_headers['TapeSizeInBytes'] = modified_headers['TapeSizeInBytes'].replace("Bytes", modified_units)
    modified_headers['TapeUsedInBytes'] = modified_headers['TapeUsedInBytes'].replace("Bytes", modified_units)
    modified_headers['GatewayARN'] = "Gateway"

    data.data = modified_tapes
    data.headerlabels = modified_headers
    return True

@app.command()
def listvtltapes(
    ctx: typer.Context,
    gateway_arns: list[str] = typer.Argument(default=None, help="Zero or more gateway ARNs/IDs to list tapes for.")
):
    """
    List tapes in the AWS Tape Gateway Virtual Tape Library.
    If gateway ARNs are provided, list tapes for those gateways.
    If no gateway ARNs are provided, list all tapes in the region.
    """

    # create SauceData object
    tapedata = list_tapes(ctx, gateway_arns)

    # set the output format if OUTPUT is defined in ctx
    if "OUTPUT" in ctx.obj and ctx.obj["OUTPUT"] is not None:
        tapedata.output_format = ctx.obj["OUTPUT"]

    # Format the data for tabulation
    terminal_width = get_terminal_width()
    #formatted_data, formatted_headers = fit_table_columns(terminal_width, tapes, headers, mincol=1, extwidth=3)

    # debug.  dump the contents of tapes without invoking the _str_ method
    #print(tapedata.data)
    #print(tapedata.headers)

    # Display the table
    #m_headers, m_tapes = format_tape_data(headers, tapes)
    if not format_tape_data(tapedata):
        typer.echo("Failed to format tape data.")
        return
    #print(tapedata.data)
    #print(tapedata.headers)
    #print(tapedata.headerlabels)

    #tapedata.output_format = "table"
    typer.echo (tapedata)

    #print(tabulate(m_tapes, m_headers, tablefmt="presto"))

if __name__ == "__main__":
    app()
