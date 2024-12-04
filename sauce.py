#!/usr/bin/env python3

import os
import sys
import typer
import configparser
from pathlib import Path
import logging
from utils.logging import setup_logging
from typing import Optional
from typing import Optional
from utils.amazon import get_aws_session
import locale

# subcommands
from configure import configure
from billing import billing
from listvtltapes import listvtltapes
from mktapes import mktapes
from resources import resources
from seskey import seskey
from sgstatus import sgstatus
from status import status
from updatemyip import updatemyip
from events import events

# newbilling has its own subcommands and is imported as a separate app
from newbilling import app as newbilling_app

#from utils.output_handler import handle_output  # You will create this module and function



app = typer.Typer()

def read_config(config_path):
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

@app.callback()
def main(
    ctx: typer.Context,
    config_file: str = typer.Option(
        os.path.join(Path.home(), ".sauce"),
        "--config",
        "-c",
        help="Path to the configuration file."
    ),
    logdir: str = typer.Option(
        None,
        "--logdir",
        help="Directory to store log files."
    ),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Perform a dry run without making any changes."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress all non-error output."),
    force: bool = typer.Option(False, "--force", "-f", help="Force update even if not recommended."),
    output_format: str = typer.Option("table", "--output", help="Output format (default: table)."),
    output_file: Optional[str] = typer.Option(None, "--output-file", "-o", help="Output file name (default: STDOUT)."),
    aws_profile: Optional[str] = typer.Option("default", "--profile", help="AWS CLI profile name (default: default).")
):
    ctx.ensure_object(dict)

    # Read config file
    config = read_config(config_file)
    ctx.obj["CONFIG"] = config

    # set up boto3 session
    ctx.obj["AWS_SESSION"] = get_aws_session(ctx) 

    # Determine log directory and initialize logging
    log_dir = logdir or config.get('logging', 'logdir', fallback=os.path.join(Path.home(), '.saucelogs'))
    # Initialize logging
    setup_logging(log_dir)

    # Get the specific logger configured for command line logging
    cmdline_logger = logging.getLogger('cmdline')

    # Log the command line arguments using the specific logger
    cmdline_logger.info('Command Line: ' + ' '.join(sys.argv))

    mylocale = config.get('general', 'locale', fallback=None)
    if not mylocale:
        mylocale = locale.getdefaultlocale()[0] or 'en_US'

    ctx.obj["LOG_DIR"] = log_dir
    ctx.obj["DRY_RUN"] = dry_run
    ctx.obj["QUIET"] = quiet
    ctx.obj["FORCE"] = force
    ctx.obj["OUTPUT"] = output_format
    ctx.obj["OFILE"] = output_file
    ctx.obj["PROFILE"] = aws_profile
    ctx.obj["LOCALE"] = mylocale

app.command()(seskey)
app.command()(updatemyip)
app.command()(configure)
app.command()(listvtltapes)
app.command()(mktapes)
app.command()(billing)
app.command()(resources)
app.command()(status)
app.command()(sgstatus)
app.command()(events)

# again, newbilling has its own subcommands and is imported as a separate app
app.add_typer(newbilling_app, name="newbilling")


if __name__ == "__main__":
    app()
