#!/usr/bin/enb python3

import typer
import logging
import json
from boto3.session import Session
from SauceData.handler import SauceData
from typing import Optional
from utils.amazon import get_aws_session, get_aws_client
from datetime import datetime, timedelta

from utils.utilities import get_last_day_of_month, format_time_period

import locale
from babel.numbers import format_currency, get_territory_currencies
from babel import Locale

app = typer.Typer(help="New AWS billing commands.")



### Utiulity functions
def fetch_current_billing(ce_client, start_date, end_date, granularity='MONTHLY'):
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity=granularity,
            Metrics=['UnblendedCost']
        )
        amount = response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']
        currency = response['ResultsByTime'][0]['Total']['UnblendedCost'].get('Unit', 'USD')  # Default to USD
        return amount, currency
    except Exception as e:
        logging.getLogger('newbilling').error(f"Error fetching current billing: {e}")
        raise

def fetch_cost_forecast(ce_client, start_date, end_date, granularity='MONTHLY'):
    try:
        forecast = ce_client.get_cost_forecast(
            TimePeriod={'Start': start_date, 'End': end_date},
            Metric='UNBLENDED_COST',
            Granularity=granularity
        )
        amount = forecast['Total']['Amount']
        currency = forecast['Total'].get('Unit', 'USD')  # Default to USD
        return amount, currency
    except Exception as e:
        logging.getLogger('newbilling').error(f"Error fetching cost forecast: {e}")
        raise

def format_amount_with_currency(amount: float, currency_code: str, locale: str = 'en_US') -> str:
    """
    Formats a given amount with the appropriate currency symbol.

    Parameters:
    - amount (float): The monetary amount to be formatted.
    - currency_code (str): The ISO 4217 currency code.
    - locale (str): The locale to be used for formatting.

    Returns:
    - str: The formatted currency string.
    """
    try:
        return format_currency(amount, currency_code, locale=locale)
    except Exception as e:
        logging.getLogger('newbilling').warning(f"Failed to format currency: {e}. Falling back to default formatting.")
        # Fallback to a simple format if Babel fails (e.g., unknown currency code)
        return f"{currency_code} {amount:,.2f}"

def usage_by_service(ce_client, start_date: str, end_date: str) -> dict:
    """
    Fetches the usage and cost data grouped by service for a given time range.

    Args:
        ce_client: The AWS Cost Explorer client.
        start_date (str): The start date for the query (inclusive), in 'YYYY-MM-DD' format.
        end_date (str): The end date for the query (inclusive), in 'YYYY-MM-DD' format.

    Returns:
        dict: A dictionary with service names as keys and their respective costs per day as values.
    """
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        service_data = {}
        for result in response['ResultsByTime']:
            date = result['TimePeriod']['Start']
            for group in result['Groups']:
                service_name = group['Keys'][0]
                amount = group['Metrics']['UnblendedCost']['Amount']
                service_data.setdefault(service_name, []).append({'Date': date, 'Amount': amount})
        return service_data
    except Exception as e:
        logging.getLogger('newbilling').error(f"Error fetching usage by service: {e}")
        return {}

def prefill_date_headers(start_date_str: str, end_date_str: str) -> list:
    """
    Generate a list of dates in DD-MMM format for every day between start_date and end_date, inclusive.
    Both start_date and end_date should be strings in the format %Y-%m-%d.

    Args:
    start_date_str (str): The start date in %Y-%m-%d format.
    end_date_str (str): The end date in %Y-%m-%d format.

    Returns:
    list: A list of dates in the specified range in DD-MMM format.
    """
    # Convert strings to datetime objects
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    # Calculate the number of days in the range
    num_days = (end_date - start_date).days + 1
    
    # Generate the list of dates
    date_list = [(start_date + timedelta(days=i)).strftime('%d-%b') for i in range(num_days)]
    
    return date_list

###
### Subcommands
###
@app.command()
def mtd(ctx: typer.Context):
    """
    Get the month-to-date billing summary grouped by service.
    """
    ce_client = get_aws_client(ctx, 'ce')
    
    # Current date considerations
    today = datetime.now()
    year, month = today.year, today.month
    start_of_month, _ = format_time_period(year, month)

    # add one day to today
    tomorrow = today + timedelta(days=1)

    # Fetch usage by service.  specify dates in iso format
    service_usage = usage_by_service(ce_client, start_of_month, tomorrow.strftime('%Y-%m-%d'))

    # Create a SauceData object and pre-fill headers with dates in DD-MMM format
    date_headers = prefill_date_headers(start_of_month, today.strftime('%Y-%m-%d'))
    sauce_data = SauceData(data=[])
    sauce_data.headers = ['Service', 'Total'] + date_headers[::-1]

    # Initialize a dictionary to keep track of total costs per date
    total_costs = {date: 0 for date in date_headers}
    total_costs['Total'] = 0

    # We'll need the currency and locale.  Do this once.
    currency = None
    mylocale = ctx.obj['LOCALE'] or 'en_US'
    
    # Extract and format each row
    for service, daily_data in service_usage.items():
        row = {'Service': service, 'Total': sum(float(daily['Amount']) for daily in daily_data)}
        for daily in daily_data:
            # find the currency unit or default to USD
            # TODO cost forecast gives a currency unit, but cost and usage does not
            if not currency:
                currency = "USD"

            date_str = datetime.strptime(daily['Date'], '%Y-%m-%d').strftime('%d-%b')
            # Convert Amount to a float in the correct currency and add it (unconverted) to the
            # totals
            #row[date_str] = float(daily['Amount'])
            row[date_str] = format_currency(float(daily['Amount']), currency, locale=mylocale)
            total_costs[date_str] += float(daily['Amount'])
            total_costs['Total'] += float(daily['Amount'])
        # Convert the total amount to a formatted currency string
        row['Total'] = format_currency(row['Total'], currency, locale=mylocale)
        sauce_data.append(row)

    # Add the total row
    total_row = {'Service': 'Total', **total_costs}
    # Convert the total amounts to formatted currency strings
    for date, amount in total_row.items():
        if date != 'Service':
            total_row[date] = format_currency(amount, currency, locale=mylocale)

    # Add the total row to the data
    sauce_data.append(total_row)

    # set output format
    sauce_data.output_format=ctx.obj['OUTPUT']

    # sort by total
    sauce_data.sort_data([('Total', 'asc')])

    # finally, print it
    print(sauce_data)

@app.command()
def summary(ctx: typer.Context):
    ce_client = get_aws_client(ctx, 'ce')
    
    # Current date considerations
    today = datetime.now()
    year, month = today.year, today.month
    start_of_month, _ = format_time_period(year, month)  # First day of the month
    
    # Handling the forecast start date based on AWS's earliest supported date
    earliest_supported_start = datetime(2024, 2, 12)  # Adjust based on AWS's constraints
    forecast_start_date = max(today, earliest_supported_start)
    _, forecast_end_date = format_time_period(year, month)  # Last day of the month
    
    # Format dates as strings for the API calls
    forecast_start_date_str = forecast_start_date.strftime('%Y-%m-%d')
    forecast_end_date_str = forecast_end_date

    # Check if adjustment was necessary and log/inform accordingly
    if forecast_start_date > today:
        logging.getLogger('newbilling').info(f"Adjusted forecast start date to {forecast_start_date_str} based on AWS's earliest supported date.")
    
    # Fetch the forecast and current billing including currency
    current_billing, current_currency = fetch_current_billing(ce_client, start_of_month, today.strftime('%Y-%m-%d'))
    cost_forecast, forecast_currency = fetch_cost_forecast(ce_client, forecast_start_date_str, forecast_end_date_str)
    
    # Use the utility function to format the output with the correct currency symbol
    current_spend_formatted = format_amount_with_currency(float(current_billing), current_currency)
    estimated_monthly_spend_formatted = format_amount_with_currency(float(cost_forecast), forecast_currency)

    print(f"Current Spend: {current_spend_formatted}, Estimated Monthly Spend: {estimated_monthly_spend_formatted}")


@app.command()
def newbilling (
#    start_date: str = typer.Option(..., help="Start date in 'YYYY-MM-DD' format"),
#    end_date: str = typer.Option(..., help="End date in 'YYYY-MM-DD' format"),
#    region: str = typer.Option(None, help="AWS Region"),
#    service: str = typer.Option(None, help="Specific AWS service"),
):
    """
    Generate a billing report based on the specified subcommands.
    """

    pass
