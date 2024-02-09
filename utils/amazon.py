#!/usr/bin/env python3

import re
import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

def build_arn(service, resource_type, resource_id, partition='aws', region=None):
    """
    Build an AWS ARN for a given resource.

    :param service: The AWS service for this arn
    :param resource_type: Type of the AWS resource (e.g., 'lambda', 's3', 'ec2:instance').
    :param resource_id: The ID of the resource (e.g., 'my-lambda-function', 'my-bucket').
    :param partition: The partition in which the resource is located (default: 'aws').
    :param region: The AWS region (default: None, attempts to read from environment or config, fallback 'us-east-1').
    :return: The ARN string or None if an error occurs.
    """
    # Attempt to determine the region
    if region is None:
        region = boto3.session.Session().region_name or 'us-east-1'

    # Create a boto3 STS client to get the account ID
    sts_client = boto3.client('sts', region_name=region)
    try:
        account_id = sts_client.get_caller_identity()["Account"]
    except NoCredentialsError:
        print("No AWS credentials found. Please configure your AWS credentials.")
        return None
    except ClientError as e:
        print(f"An error occurred accessing AWS STS: {e}")
        return None

    return f"arn:{partition}:{service}:{region}:{account_id}:{resource_type}/{resource_id}"

# Function to get the region from an ARN
def get_region_from_arn(arn):
    """
    Extracts the region from an AWS ARN.

    :param arn: The ARN string from which to extract the region.
    :return: The extracted region as a string, or None if the ARN is malformed.
    """
    try:
        return arn.split(":")[3]
    except IndexError:
        # Handle the case where the ARN is not correctly formatted
        print("Malformed ARN provided.")
        return None

class Arn:
    def __init__(self, arn_str):
        """
        Initialize an Arn object with a given ARN string.

        :param arn_str: ARN string to be parsed
        :raises ValueError: If the ARN string is not properly formatted
        """
        self.arn_str = arn_str
        self.arn = arn_str
        # Regular expression to match and parse an ARN
        arn_regex = r"^arn:([^:]*):([^:]*):([^:]*):([^:]*):([^:/]*)(:?)(.*)$"
        match = re.match(arn_regex, self.arn_str)

        if not match:
            raise ValueError(f"Invalid ARN format: {arn_str}")

        self.partition = match.group(1)
        self.service = match.group(2)
        self.region = match.group(3)
        self.account_id = match.group(4)
        self.resource_type = match.group(5)
        self.resource_id = match.group(7)

    def __str__(self):
        """
        Return the full ARN string.
        """
        return self.arn_str

def check_aws_credentials(debug=False):
    """
    Check if AWS credentials are available and print them if debug mode is enabled.

    Parameters:
    debug (bool): If True, enables debug mode to print AWS Access Key.

    Returns:
    bool: True if AWS credentials are available, False otherwise.
    """
    try:
        boto3.client('sts').get_caller_identity()
        if debug:
            aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
            print(f"Debug: Using AWS Access Key: {aws_access_key}")
        return True
    except NoCredentialsError:
        return False
