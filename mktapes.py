#!/usr/bin/env python3

import typer
from utils.utilities import get_terminal_width, fit_table_columns, convert_bytes, convert_size_to_bytes
from utils.logging import get_loggers
from utils.amazon import build_arn, get_region_from_arn

import boto3
import argparse
import os
import re
from botocore.exceptions import ClientError, BotoCoreError
import configparser

# Get the loggers
loggers = get_loggers()

app = typer.Typer()
MAXERROR = 10
TAPE_STORAGE_FILE = os.path.expanduser("~/.awstapes")
DEFAULT_TAPE_POOL = "DEEP_ARCHIVE"
COUNT_HARD_LIMIT = 10

# Function to read the stored barcodes
def read_stored_barcodes():
    if os.path.exists(TAPE_STORAGE_FILE):
        with open(TAPE_STORAGE_FILE, "r") as file:
            return [line.strip().split(",") for line in file.readlines()]
    return []

# Function to write a new barcode to the storage file
def write_stored_barcode(barcode, region, tape_pool):
    with open(TAPE_STORAGE_FILE, "a") as file:
        file.write(f"{barcode},{region},{tape_pool}\n")

# Function to get the list of tapes and update the storage file
def list_and_update_tapes(client, prefix, region):
    stored_barcodes = read_stored_barcodes()
    tapes = client.list_tapes()
    tape_barcodes = [(tape['TapeBarcode'], tape.get('PoolId', DEFAULT_TAPE_POOL)) for tape in tapes['TapeInfos'] if tape['TapeBarcode'].startswith(prefix)]
    tape_barcodes += [(barcode, tape_pool) for barcode, stored_region, tape_pool in stored_barcodes if stored_region == region and barcode.startswith(prefix)]
    updated_barcodes = sorted(set(tape_barcodes))

    # Update the storage file with the fetched tapes
    for barcode, tape_pool in updated_barcodes:
        if not any(barcode == b and region == r for b, r, _ in stored_barcodes):
            write_stored_barcode(barcode, region, tape_pool)

    return updated_barcodes

# Function to identify the next tape in sequence
def next_tape_in_sequence(last_tape, prefix):
    if not last_tape:
        return f"{prefix}000001"

    last_number_hex = last_tape[0][len(prefix):]  # last_tape is now a tuple (barcode, tape_pool)
    next_number = int(last_number_hex, 16) + 1
    next_number_hex = f"{next_number:06X}"
    return f"{prefix}{next_number_hex}"

# Function to create tapes
def create_tapes(client, count, barcode_prefix, gateway_arn, size_in_bytes, tape_pool, dry_run, region):
    tape_barcodes = list_and_update_tapes(client, barcode_prefix, region)
    last_tape = tape_barcodes[-1] if tape_barcodes else None
    last_tape_pool = last_tape[1] if last_tape else tape_pool

    # Create the number of tapes requested
    for _ in range(count):
        error_count = 0
        while error_count < MAXERROR:
            try:
                barcode = next_tape_in_sequence(last_tape, barcode_prefix)
                last_tape = (barcode, last_tape_pool)  # Update the last tape for the next iteration

                if dry_run:
                    print(f"Tape to be created: Barcode: {barcode}, Pool: {last_tape_pool}")
                else:
                    response = client.create_tape_with_barcode(
                        GatewayARN=gateway_arn,
                        TapeSizeInBytes=size_in_bytes,
                        TapeBarcode=barcode,
                        PoolId=last_tape_pool
                    )
                    print(f"Created tape with barcode: {barcode}, Pool: {last_tape_pool}, ARN: {response['TapeARN']}")
                    write_stored_barcode(barcode, region, last_tape_pool)
                break
            except ClientError as e:
                if e.response['Error']['Code'] == 'InvalidGatewayRequestException' and 'BarcodeAlreadyInUse' in str(e):
                    print(f"Barcode {barcode} already in use. Trying next barcode.")
                    error_count += 1
                    write_stored_barcode(barcode, region, last_tape_pool)  # Record the conflict barcode
                else:
                    raise
            except BotoCoreError as e:
                # Handle other boto core errors
                print(f"An unexpected error occurred: {e}")
                raise

@app.command()
def mktapes(
        ctx: typer.Context,
        count: int = typer.Option(1, help="Number of tapes to create (max 10)"),
        prefix: str = typer.Option(None, help="Barcode prefix (1-4 characters)"),
        gateway_arn: str = typer.Argument(None, help="ARN of the Gateway"),
        pool: str = typer.Option(None, help="Tape pool to use"),
        size_in_bytes: int = typer.Option(None, help="Size of the tape in bytes"),
    ):
    """
    Interact with AWS Storage Gateway to manage tapes.
    """
    # Get variables from the context
    dry_run = ctx.obj["DRY_RUN"]
    quiet = ctx.obj["QUIET"]
    force = ctx.obj["FORCE"]
    
    # process config
    config = ctx.obj["CONFIG"]
    
    if config:
        # Use values from config as fallback
        gateway_arn = gateway_arn or config.get('mktapes', 'default_gateway_arn', fallback=None)
        prefix = prefix or config.get('mktapes', 'default_prefix', fallback="TAPE")
        tape_pool = pool or config.get('mktapes', 'tape_pool', fallback=DEFAULT_TAPE_POOL)
    else:
        # Use defaults
        gateway_arn = gateway_arn or None
        prefix = prefix or "TAPE"
        tape_pool = pool or DEFAULT_TAPE_POOL

    # Validate and process gateway ARN
    if gateway_arn:
        if not gateway_arn.startswith("arn:"):
            if re.match("^sgw-[A-F0-9]{8,}$", gateway_arn):
                region = get_region_from_arn(ctx.obj["CONFIG"].get("default", "region", fallback="us-east-1"))
                gateway_arn = build_arn("storagegateway", "gateway", gateway_arn, region=region)
            else:
                raise typer.BadParameter("Gateway ARN or ID is not valid.")
    else:
        # If gateway_arn is not provided, raise an error
        raise typer.BadParameter("Gateway ARN or ID is required.")

    # work out the tape size    
    tape_size = config.get('mktapes', 'default_tape_size')

    # Check the format of tape_size
    if isinstance(tape_size, str) and " " in tape_size:
        size_parts = tape_size.split(" ")
        if len(size_parts) == 2:
            try:
                size_int = int(size_parts[0])
                size_str = size_parts[1]
                size_in_bytes = convert_size_to_bytes(size_int, size_str)
            except ValueError:
                pass
    else:
        size_in_bytes = tape_size

    # Determine region
    region = get_region_from_arn(gateway_arn)

    # Validate the count
    if count < 1 or count > COUNT_HARD_LIMIT:
        raise typer.BadParameter(f"Count must be between 1 and {COUNT_HARD_LIMIT}.")

    """
    # Print some debug info and exit
    print (f"count: {count}")
    print (f"prefix: {prefix}")
    print (f"gateway_arn: {gateway_arn}")
    print (f"size_in_bytes: {size_in_bytes}")
    print (f"tape_pool: {tape_pool}")

    return
    """
    # Create the boto3 client
    try:
        client = boto3.client('storagegateway', region_name=region)
        create_tapes(client, count, prefix, gateway_arn, size_in_bytes, tape_pool, dry_run, region)
    except ClientError as e:
        typer.echo(f"Error connecting to AWS: {e}", err=True)
    except BotoCoreError as e:
        # Handle other boto core errors
        typer.echo(f"An unexpected error occurred: {e}", err=True)
