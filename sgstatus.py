#!/usr/bin/env python3

import typer
import boto3
from tabulate import tabulate
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from utils.logging import get_loggers

# Get the loggers
loggers = get_loggers()

def sgstatus(ctx: typer.Context):
    loggers['debug'].debug(f"Executing {__name__} subcommand")

    try:
        # Create a Boto3 client for AWS Storage Gateway
        sgclient = boto3.client('storagegateway')

        # Get a list of all storage gateways
        response = sgclient.list_gateways()

        # Extract the list of storage gateways
        gateways = response['Gateways']

        gwdata = []
        headers = ['GatewayId', 'Name', 'OpState', 'State', 'Interfaces',  'GatewayType', 'EndpointType' ]

        # Iterate over each storage gateway
        for gateway in gateways:
            # Get the gateway ARN
            gateway_arn = gateway['GatewayARN']

            # Describe the gateway information
            gateway_info = sgclient.describe_gateway_information(GatewayARN=gateway_arn)

            #print (gateway)
            # Extract the required data from gateway and gateway_info
            data = {
                'Id': gateway['GatewayId'],
                'Name': gateway['GatewayName'],
                'OpState': gateway['GatewayOperationalState'],
                'State': gateway_info['GatewayState'],
                'Network': ', '.join([interface['Ipv4Address'] for interface in gateway_info['GatewayNetworkInterfaces']]),  # Fix: Corrected syntax error and joined the IP addresses
                'Type': gateway_info['GatewayType'],
                'Endpoint Type': gateway_info['EndpointType']
            }

            # Append the data to gwdata
            gwdata.append(data)

        # Print the gwdata
        #print(gwdata)

    except NoCredentialsError:
        typer.echo("No AWS credentials found. Please configure them properly.")
    except PartialCredentialsError:
        typer.echo("Incomplete AWS credentials. Please check your configuration.")
    except ClientError as e:
        typer.echo(f"AWS Connection Error: {e}")

    headers_dict = dict(zip(headers, headers))
    print(tabulate(gwdata, headers_dict, tablefmt="presto"))
if __name__ == "__main__":
    typer.run(sgstatus)
