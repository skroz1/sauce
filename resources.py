#!/usr/bin/env python3

import typer
from utils.logging import get_loggers
from utils.amazon import get_aws_client
from SauceData.handler import SauceData

app = typer.Typer()
loggers = get_loggers()

@app.command()
def resources(ctx: typer.Context):
    resources = []

    # EC2 Instances
    ec2_client = get_aws_client(ctx, 'ec2')
    instances = ec2_client.describe_instances()
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            resources.append({
                'Service': 'EC2',
                'Name': instance.get('InstanceId'),
                'Region': ec2_client.meta.region_name,
                'ARN': f"arn:aws:ec2:{ec2_client.meta.region_name}:{ctx.obj['ACCOUNT_ID']}:instance/{instance.get('InstanceId')}"
            })

    # S3 Buckets
    s3_client = get_aws_client(ctx, 's3')
    buckets = s3_client.list_buckets()
    for bucket in buckets['Buckets']:
        resources.append({
            'Service': 'S3',
            'Name': bucket['Name'],
            #'Region': 'Global',  # S3 buckets are global, but they are hosted in specific regions
            'Region': buckets.get('LocationConstraint', 'us-east-1'),  # S3 buckets are global, but they are hosted in specific regions
            'ARN': f"arn:aws:s3:::{bucket['Name']}"
        })

    # IAM Roles
    iam_client = get_aws_client(ctx, 'iam')
    roles = iam_client.list_roles()
    for role in roles['Roles']:
        resources.append({
            'Service': 'IAM',
            'Name': role['RoleName'],
            'Region': 'Global',
            'ARN': role['Arn']
        })

    # Storage Gateway
    sg_client = get_aws_client(ctx, 'storagegateway')
    sg_gateways = sg_client.list_gateways()
    for gateway in sg_gateways['Gateways']:
        resources.append({
            'Service': 'Storage Gateway',
            'Name': gateway['GatewayName'],
            'Region': sg_client.meta.region_name,
            'ARN': gateway['GatewayARN']
        })

    # route53
    route53_client = get_aws_client(ctx, 'route53')
    hosted_zones = route53_client.list_hosted_zones()
    for zone in hosted_zones['HostedZones']:
        resources.append({
            'Service': 'Route 53',
            'Name': zone['Name'],
            'Region': 'Global',
            'ARN': zone['Id']
        })

    # workmail
    workmail_client = get_aws_client(ctx, 'workmail')
    organizations = workmail_client.list_organizations()
    for org in organizations['OrganizationSummaries']:
        resources.append({
            'Service': 'WorkMail',
            'Name': org['Name'],
            'Region': 'Global',
            'ARN': org['OrganizationId']
        })

        

    # Format and display the information using SauceData
    sauce_data = SauceData(data=resources, output_format=ctx.obj['OUTPUT'], output_file=ctx.obj['OFILE'])
    print(sauce_data)

if __name__ == "__main__":
    typer.run(list_resources)
