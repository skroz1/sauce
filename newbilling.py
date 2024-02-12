#!/usr/bin/enb python3

import typer
import logging
from boto3.session import Session
from SauceData.handler import SauceData
from typing import Optional
from utils.amazon import get_aws_session, get_aws_client
from datetime import datetime, timedelta

from utils.utilities import get_last_day_of_month, format_time_period

from babel.numbers import format_currency

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

    # Fetch usage by service
    service_usage = usage_by_service(ce_client, start_of_month, today.strftime('%Y-%m-%d'))
    
    # create a SauceData object and populate it with service_usage
    sd = SauceData()
    # for each service create a new dict, populate it with the usage data by day


    # Convert the service_usage data into a format that can be easily displayed
    # This part can be customized based on how you want to display the data (e.g., using SauceData for tabulation)
    for service, daily_data in service_usage.items():
        print(f"Service: {service}")
        for daily in daily_data:
            print(f"  Date: {daily['Date']}, Amount: ${float(daily['Amount']):.2f}")
        print("-" * 40)  # Separator for readability

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