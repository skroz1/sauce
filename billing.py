#!/usr/bin/env python3

import typer
import os
import sys
import boto3
from botocore.exceptions import NoCredentialsError, BotoCoreError, ClientError
import shutil
import calendar
import argparse
import getpass
import configparser
import json

from tabulate import tabulate
from datetime import datetime

from utils import amazon
from utils import utilities
from utils.logging import get_loggers
from utils.utilities import get_terminal_width, get_last_day_of_month, format_time_period
from utils.amazon import get_aws_session, get_aws_client

app = typer.Typer()

# Get the loggers
loggers = get_loggers()

# Define exit codes
EXIT_CODE_GENERAL_ERROR = 1
EXIT_CODE_AWS_DATA_RETRIEVAL_ERROR = 2

def get_aws_cost_for_period(ctx:typer.Context, start_date, end_date, granularity, group_by=None):
    """
    Retrieve AWS cost and usage data for a specified time period with enhanced exception handling.

    Parameters:
    start_date (str): Start date in 'YYYY-MM-DD' format.
    end_date (str): End date in 'YYYY-MM-DD' format.
    granularity (str): The granularity of the AWS cost data (e.g., 'DAILY').
    group_by (list, optional): The grouping of AWS cost data.

    Returns:
    dict: The response containing cost and usage data.
    """
    client = get_aws_client(ctx, 'ce')

    args = {
        'TimePeriod': {'Start': start_date, 'End': end_date},
        'Granularity': granularity,
        'Metrics': ['UnblendedCost']
    }
    if group_by:
        args['GroupBy'] = group_by

    try:
        response = client.get_cost_and_usage(**args)
        return response
    except BotoCoreError as e:
        print(f"An error occurred while fetching AWS cost data: {e}")
        return None
    except ClientError as e:
        print(f"Client error in AWS request: {e}")
        return None

def detailed_data(response):
    """
    Parse detailed cost data grouped by service from AWS response.

    Parameters:
    response (dict): The response data from AWS Cost Explorer API.

    Returns:
    tuple: A tuple of data list and headers for tabulation.
    """
    service_costs = {}
    total_cost = 0

    for result in response['ResultsByTime']:
        for group in result['Groups']:
            amount = float(group['Metrics']['UnblendedCost']['Amount'])
            if amount > 0:
                keys = ', '.join(group['Keys'])
                service_costs[keys] = service_costs.get(keys, 0) + amount
                total_cost += amount

    # Calculate the maximum length for cost formatting
    max_cost_length = max(len(f"${cost:.2f}") for cost in service_costs.values())

    data = [[service, f"${cost:>{max_cost_length}.2f}"] for service, cost in sorted(service_costs.items(), key=lambda item: item[1])]
    if total_cost > 0:
        data.append(['Total', f"${total_cost:>{max_cost_length}.2f}"])

    headers = ['Service', 'Cost']
    return data, headers

def daily_data(response, now):
    """
    Generate daily cost data for the current month.

    Parameters:
    response (dict): The response data from AWS Cost Explorer API.
    now (datetime): Current datetime object.

    Returns:
    tuple: A tuple of data list and headers for tabulation.
    """
    dates = sorted({result['TimePeriod']['Start'] for result in response['ResultsByTime'] if result['TimePeriod']['Start'] <= now.strftime("%Y-%m-%d")})
    formatted_dates = [datetime.strptime(date, "%Y-%m-%d").strftime("%b-%d") for date in dates]

    total_costs = [0.0] * len(dates)
    for i, date in enumerate(dates):
        for result in response['ResultsByTime']:
            if result['TimePeriod']['Start'] == date:
                total_costs[i] += sum(float(group['Metrics']['UnblendedCost']['Amount']) for group in result['Groups'])

    data = [['Total'] + [f"${cost:.2f}" for cost in total_costs]]
    headers = ['Date'] + formatted_dates
    return data, headers

def table_data(response, now):
    """
    Organize daily cost data by service for the current month into a table format.

    Parameters:
    response (dict): The response data from AWS Cost Explorer API.
    now (datetime): Current datetime object.

    Returns:
    tuple: A tuple of data list and headers for tabulation.
    """
    dates = sorted({result['TimePeriod']['Start'] for result in response['ResultsByTime'] if result['TimePeriod']['Start'] <= now.strftime("%Y-%m-%d")})
    formatted_dates = [datetime.strptime(date, "%Y-%m-%d").strftime("%b-%d") for date in dates]

    service_costs = {date: {} for date in dates}
    service_totals = {}

    for result in response['ResultsByTime']:
        date = result['TimePeriod']['Start']
        for group in result['Groups']:
            service = ', '.join(group['Keys'])
            amount = float(group['Metrics']['UnblendedCost']['Amount'])
            service_costs[date].setdefault(service, 0.0)
            service_costs[date][service] += amount
            service_totals[service] = service_totals.get(service, 0.0) + amount

    data = []
    for service, total in service_totals.items():
        row = [service, f"${total:.2f}"] + [f"${service_costs[date].get(service, 0.0):.2f}" for date in dates]
        data.append(row)

    daily_totals = [sum(service_costs[date].values()) for date in dates]
    data.append(['Total', f"${sum(daily_totals):.2f}"] + [f"${total:.2f}" for total in daily_totals])

    # headers
    headers = ['Service', 'Total'] + formatted_dates

    # Find and remove the 'Tax' row if it exists
    tax_row = None
    for row in data:
        if row[0] == 'Tax':
            tax_row = row
            data.remove(row)
            break

    # Sort data by the 'Total' column in ascending order
    # Skip the header row and the 'Total' row at the end
    sorted_data = sorted(data[:-1], key=lambda x: float(x[1][1:].replace(',', '')))
    
    # Re-insert the 'Tax' row before the 'Total' row if it was found
    if tax_row:
        sorted_data.append(tax_row)

    # Append the 'Total' row at the end
    sorted_data.append(data[-1])

    return sorted_data, headers

def summary_data(current_month_response):
    """
    Calculate and display the total cost for the current month.

    Parameters:
    current_month_response (dict): The response data from AWS Cost Explorer API for the current month.
    """
    current_month_cost = 0.0
    for time_period in current_month_response['ResultsByTime']:
        for group in time_period['Groups']:
            amount = float(group['Metrics']['UnblendedCost']['Amount'])
            current_month_cost += amount

    # Prepare data for summary table
    data = [
        ["Current Month", f"${current_month_cost:.2f}"]
    ]

    # Print summary table
    print(tabulate(data, headers=["Period", "Cost"], tablefmt="plain"))

def fit_table_columns(terminal_width, data, headers, mincol, extwidth=3):
    """
    Fit the table columns to the terminal width.

    Parameters:
    terminal_width (int): The width of the terminal.
    data (list): The data to be displayed in the table.
    headers (list): The headers for the table.
    mincol (int): The minimum number of columns to display on the left. Used for service name, totals, etc.
    extwidth (int): The extra width to add to each column to account for the table borders.
    
    Returns:
    tuple: A tuple of fitted data list and headers for tabulation.
    """
    if len(headers) < mincol:
        raise ValueError("Not enough columns in data to satisfy mincol requirement")

    # why did I do this?
    def column_width(col):
        max_length = max(len(str(item)) for item in col)
        return max_length + 2  # Adding space for padding

    new_data = [row[:mincol] for row in data]
    new_headers = headers[:mincol]
    width_debug_row = ['Width']  # Debug row to show the width of each column

    total_width = sum(column_width(col) + extwidth for col in zip(*new_data)) + len(new_headers) - 1

    remaining_cols = list(range(mincol, len(headers)))[::-1]

    for i in remaining_cols:
        col = [row[i] for row in data]
        col_width = column_width(col) + extwidth

        if total_width + col_width > terminal_width:
            break

        for row, item in zip(new_data, col):
            row.append(item)
        new_headers.append(headers[i])
        width_debug_row.append(str(col_width))
        total_width += col_width

    # debug row
    #new_data.append(width_debug_row)

    return new_data, new_headers

@app.command()
def billing(ctx: typer.Context, format: str = typer.Argument("summary")):
    loggers['debug'].debug(f"Executing {__name__}() subcommand")

    dry_run = ctx.obj["DRY_RUN"]
    quiet = ctx.obj["QUIET"]
    force = ctx.obj["FORCE"]

    # Current date
    now = datetime.now()
    current_month_start, current_month_end = format_time_period(now.year, now.month)

    # AWS Cost Explorer API parameters
    granularity = 'DAILY'
    group_by = [{'Type': 'DIMENSION', 'Key': 'SERVICE'}]

    if format == 'detail':
        current_month_response = get_aws_cost_for_period(ctx, current_month_start, current_month_end, granularity, group_by)
        if current_month_response is None:
            print("Failed to retrieve AWS cost data.", file=sys.stderr)
            sys.exit(EXIT_CODE_AWS_DATA_RETRIEVAL_ERROR)
        data, headers = detailed_data(current_month_response)
        print(tabulate(data, headers, tablefmt="plain"))
    elif format == 'daily':
        current_month_response = get_aws_cost_for_period(ctx, current_month_start, current_month_end, granularity, group_by)
        if current_month_response is None:
            print("Failed to retrieve AWS cost data.", file=sys.stderr)
            sys.exit(EXIT_CODE_AWS_DATA_RETRIEVAL_ERROR)
        data, headers = daily_data(current_month_response, now)
        print(tabulate(data, headers, tablefmt="plain"))
    elif format == 'table':
        current_month_response = get_aws_cost_for_period(ctx, current_month_start, current_month_end, granularity, group_by)
        if current_month_response is None:
            print("Failed to retrieve AWS cost data.", file=sys.stderr)
            sys.exit(EXIT_CODE_AWS_DATA_RETRIEVAL_ERROR)
        data, headers = table_data(current_month_response, now)
        fitted_data, fitted_headers = fit_table_columns(get_terminal_width(), data, headers, mincol=2, extwidth=3)
        print(tabulate(fitted_data, fitted_headers, tablefmt="presto"))
    elif format == 'summary':
        current_month_response = get_aws_cost_for_period(ctx, current_month_start, current_month_end, granularity, group_by)
        if current_month_response is None:
            print("Failed to retrieve AWS cost data.", file=sys.stderr)
            sys.exit(EXIT_CODE_AWS_DATA_RETRIEVAL_ERROR)
        summary_data(current_month_response)

if __name__ == "__main__":
    typer.run(billing)

