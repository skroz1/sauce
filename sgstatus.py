#!/usr/bin/env python3

import typer
import json
import boto3
from tabulate import tabulate
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from utils.logging import get_loggers
from utils.amazon import get_aws_session, get_aws_client
from SauceData.handler import SauceData

# Get the loggers
loggers = get_loggers()

def sgstatus(ctx: typer.Context):
    loggers['debug'].debug(f"Executing {__name__} subcommand")

    # Create a SauceData object
    gwdata = SauceData()

    # set the output format if OUTPUT is defined in ctx
    if "OUTPUT" in ctx.obj and ctx.obj["OUTPUT"] is not None:
        gwdata.output_format = ctx.obj["OUTPUT"]

    try:
        # Create a Boto3 client for AWS Storage Gateway
        sgclient = get_aws_client(ctx, 'storagegateway')

        # Get a list of all storage gateways
        response = sgclient.list_gateways()

        # pretty print the response
        # print(json.dumps(response, indent=2))
        
        # Extract the list of storage gateways
        gateways = response['Gateways']
        gwdata.headerlabels = {
            "GatewayId": "ID",
            "GatewayARN": None,
            "GatewayOperationalState": "OpState",
            "GatewayType": "Type",
            "GatewayName": "Name",
            "HostEnvironment": "Environment",
            "SoftwareVersion": "Version",
        }

        # Iterate over each storage gateway
        for gateway in gateways:
            # Get the gateway ARN
            gateway_arn = gateway['GatewayARN']

            # Describe the gateway information
            gateway_info = sgclient.describe_gateway_information(GatewayARN=gateway_arn)

            # print(json.dumps(gateway_info, indent=2))

            # Extract the required data from gateway and gateway_info
            #data = {
            gwdata.append(gateway)
            """
            gwdata.append({
                'Id': gateway['GatewayId'],
                'Name': gateway['GatewayName'],
                'OpState': gateway['GatewayOperationalState'],
                'State': gateway_info['GatewayState'],
                'Network': ', '.join([interface['Ipv4Address'] for interface in gateway_info['GatewayNetworkInterfaces']]),  # Fix: Corrected syntax error and joined the IP addresses
                'Type': gateway_info['GatewayType'],
                'Endpoint Type': gateway_info['EndpointType']
            })
            """

    except NoCredentialsError:
        typer.echo("No AWS credentials found. Please configure them properly.")
    except PartialCredentialsError:
        typer.echo("Incomplete AWS credentials. Please check your configuration.")
    except ClientError as e:
        typer.echo(f"AWS Connection Error: {e}")

    #headers_dict = dict(zip(headers, headers))
    #print(tabulate(gwdata, headers_dict, tablefmt="presto"))
    print (json.dumps(gwdata.headers, indent=2  ))
    print(gwdata)

if __name__ == "__main__":
    typer.run(sgstatus)
