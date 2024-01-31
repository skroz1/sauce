#!/usr/bin/env python3
#
# name - desc
#
# Copyright (C) 2014 Scott F. Crosby <skroz1@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
import sys
import typer
import configparser
from pathlib import Path
import logging
from utils.logging import setup_logging

# import commands
from seskey import seskey
from updatemyip import updatemyip
from configure import configure
from listvtltapes import listvtltapes
from mktapes import mktapes
from billing import billing
from status import status

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
    force: bool = typer.Option(False, "--force", "-f", help="Force update even if not recommended.")
):
    ctx.ensure_object(dict)

    # Read config file
    config = read_config(config_file)
    ctx.obj["CONFIG"] = config

    # Determine log directory and initialize logging
    log_dir = logdir or config.get('logging', 'logdir', fallback=os.path.join(Path.home(), '.saucelogs'))
    # Initialize logging
    setup_logging(log_dir)

    # Get the specific logger configured for command line logging
    cmdline_logger = logging.getLogger('cmdline')

    # Log the command line arguments using the specific logger
    cmdline_logger.info('Command Line: ' + ' '.join(sys.argv))

    ctx.obj["LOG_DIR"] = log_dir
    ctx.obj["DRY_RUN"] = dry_run
    ctx.obj["QUIET"] = quiet
    ctx.obj["FORCE"] = force

app.command()(seskey)
app.command()(updatemyip)
app.command()(configure)
app.command()(listvtltapes)
app.command()(mktapes)
app.command()(billing)
app.command()(status)

if __name__ == "__main__":
    app()
