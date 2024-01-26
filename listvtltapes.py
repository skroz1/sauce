#!/usr/bin/env python3
#
# name - desc
#
# Copyright (C) 2014 Scott F. Crosby <skroz1@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import typer
import boto3
from tabulate import tabulate
from utils.utilities import get_terminal_width, fit_table_columns, convert_bytes
from utils.logging import get_loggers
from botocore.exceptions import ClientError
import sys
from datetime import datetime

app = typer.Typer()

def list_tapes(gateway_arns=None):
    tapes = []
    headers = ["TapeBarcode", "TapeCreatedDate", "TapeSizeInBytes", "TapeStatus", "TapeUsedInBytes", "PoolId", "Worm", "PoolEntryDate", "GatewayARN"]

    client = boto3.client('storagegateway')
    response = client.list_tapes()
    for tape_info in response['TapeInfos']:
        tape_arn = tape_info['TapeARN']

        # Process only tapes that have an associated GatewayARN
        if 'GatewayARN' in tape_info:
            try:
                tape_response = client.describe_tapes(GatewayARN=tape_info['GatewayARN'], TapeARNs=[tape_arn])
                tape_data = tape_response['Tapes'][0]
                if gateway_arns is None or gateway_arns == [] or tape_info['GatewayARN'] in gateway_arns:
                    tapes.append([
                        tape_data['TapeBarcode'],
                        tape_data['TapeCreatedDate'],
                        tape_data['TapeSizeInBytes'],
                        tape_data['TapeStatus'],
                        tape_data['TapeUsedInBytes'],
                        tape_data['PoolId'],
                        tape_data['Worm'],
                        tape_data['PoolEntryDate'],
                        tape_info['GatewayARN']
                    ])
            except ClientError as e:
                print(f"Failed to retrieve tape details for {tape_arn}: {e}", file=sys.stderr)
                continue
        else:
            try:
                tape_response = client.describe_tape_archives(TapeARNs=[tape_arn])
                tape_data = tape_response['TapeArchives'][0]
                tapes.append([
                    tape_data['TapeBarcode'],
                    tape_data['TapeCreatedDate'],
                    tape_data['TapeSizeInBytes'],
                    tape_data['TapeStatus'],
                    tape_data['TapeUsedInBytes'],
                    tape_data['PoolId'],
                    tape_data['Worm'],
                    tape_data['PoolEntryDate'],
                    None
                ])
            except ClientError as e:
                print(f"Failed to retrieve tape archive details for {tape_arn}: {e}", file=sys.stderr)
                continue

    return headers, tapes

# Format the tape data to be a bit more readable
def format_tape_data(headers, tapes, units="GiB"):
    modified_headers = headers.copy()
    modified_tapes = []

    # Convert TapeCreatedDate and PoolEntryDate to date and time only
    for tape in tapes:
        if isinstance(tape[1], str):
            tape[1] = datetime.fromisoformat(tape[1])
        tape[1] = tape[1].strftime("%Y-%m-%d %H:%M")  # Format to date and time only

        if isinstance(tape[7], str):
            tape[7] = datetime.fromisoformat(tape[7])
        tape[7] = tape[7].strftime("%Y-%m-%d %H:%M")  # Format to date and time only

        # convert the GatewayARN to just the gateway ID if defined
        if tape[8] is not None:
            tape[8] = tape[8].split('/')[-1]



        # Convert TapeSizeInBytes and TapeUsedInBytes to specified units
        tape[2] = format(convert_bytes(tape[2], units), ".1f")
        tape[4] = format(convert_bytes(tape[4], units), ".1f")
        
        modified_tapes.append(tape)

    # Modify the corresponding header name in headers to reflect the new units
    modified_units = units[0].capitalize() + units[1:-1] + units[-1].capitalize()
    modified_headers[2] = modified_headers[2].replace("Bytes", modified_units)
    modified_headers[4] = modified_headers[4].replace("Bytes", modified_units)
    modified_headers[8] = "Gateway"
    return modified_headers, modified_tapes

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
    headers, tapes = list_tapes(gateway_arns)
    #headers = ["Tape Barcode", "Created Date", "Size in Bytes", "Status", "Used Bytes", "Pool ID", "WORM", "Pool Entry Date", "Tape ARN", "Gateway ARN"]

    # Format the data for tabulation
    #terminal_width = get_terminal_width()
    #formatted_data, formatted_headers = fit_table_columns(terminal_width, tapes, headers, mincol=1, extwidth=3)

    # Display the table
    m_headers, m_tapes = format_tape_data(headers, tapes)
    print(tabulate(m_tapes, m_headers, tablefmt="presto"))

if __name__ == "__main__":
    app()
