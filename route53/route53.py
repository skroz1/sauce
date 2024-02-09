#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError

def get_route53_client():
    """
    Initialize and return a Route53 client.
    :return: Route53 client object.
    :raises: NoCredentialsError if AWS credentials are not found.
    """
    try:
        return boto3.client('route53')
    except NoCredentialsError as e:
        raise RuntimeError("AWS credentials not found: Please configure them properly.")

def get_hosted_zone_id(client, domain):
    """
    Find the Zone ID for the given domain.
    :param client: Route53 client object.
    :param domain: Domain as a string.
    :return: Zone ID as a string.
    :raises: ValueError if no hosted zone found for the domain.
    """
    try:
        response = client.list_hosted_zones_by_name(DNSName=domain)
        for zone in response['HostedZones']:
            if zone['Name'][:-1] == domain:  # Remove trailing dot
                return zone['Id']
        raise ValueError(f"No hosted zone found for domain: {domain}")
    except EndpointConnectionError as e:
        raise RuntimeError(f"Error connecting to AWS Route53: {e}")

def query_route53(client, zone_id, hostname):
    """
    Check if the A record for the provided hostname exists.
    :param client: Route53 client object.
    :param zone_id: Zone ID as a string.
    :param hostname: Hostname as a string.
    :return: IP address if A record exists, None otherwise.
    :raises: ClientError for AWS API errors.
    """
    try:
        response = client.list_resource_record_sets(HostedZoneId=zone_id)
        for record_set in response['ResourceRecordSets']:
            if record_set['Type'] == 'A' and record_set['Name'][:-1] == hostname:
                return record_set.get('ResourceRecords', [{}])[0].get('Value')
        return None
    except ClientError as e:
        raise RuntimeError(f"Error querying AWS Route53: {e}")

def update_route53_A(client, zone_id, hostname, ip, dry_run, quiet):
    """
    Update or create the A record for the hostname.
    :param client: Route53 client object.
    :param zone_id: Zone ID as a string.
    :param hostname: Hostname as a string.
    :param ip: IP address as a string.
    :param dry_run: Boolean indicating if this is a dry run.
    :param quiet: Boolean indicating if output should be suppressed.
    :raises: ClientError for AWS API errors.
    """
    change_batch = {
        'Changes': [{
            'Action': 'UPSERT',
            'ResourceRecordSet': {
                'Name': hostname,
                'Type': 'A',
                'TTL': 300,
                'ResourceRecords': [{'Value': ip}]
            }
        }]
    }
    if dry_run:
        if not quiet:
            print(f"Dry run: Would have updated {hostname} with IP {ip}")
    else:
        try:
            client.change_resource_record_sets(HostedZoneId=zone_id, ChangeBatch=change_batch)
            if not quiet:
                print(f"Success: {hostname} updated with {ip}")
        except ClientError as e:
            raise RuntimeError(f"Error updating AWS Route53: {e}")
