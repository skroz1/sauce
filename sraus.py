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

# import commands
from hello import hello         # for testing
from ses_key import seskey
from update_ip import updateMyIP
from configure import configure

app = typer.Typer()

def read_config(config_path):
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

@app.callback()
def main(
    ctx: typer.Context,
    config_file: str = typer.Option(
        os.path.join(Path.home(), ".sraus"),
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

    # Logging configuration
    log_dir = logdir or config.get('logging', 'logdir', fallback=os.path.join(Path.home(), '.srauslogs'))
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError as e:
            typer.echo(f"Error creating log directory {log_dir}: {e}", err=True)
            raise typer.Exit(code=1)

    log_file = os.path.join(log_dir, 'cmdline.log')
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')

    # Log the command line arguments
    logging.info('Command Line: ' + ' '.join(sys.argv))

    ctx.obj["LOG_DIR"] = log_dir
    ctx.obj["DRY_RUN"] = dry_run
    ctx.obj["QUIET"] = quiet
    ctx.obj["FORCE"] = force

app.command()(hello)
app.command()(seskey)
app.command()(updateMyIP)
app.command()(configure)

if __name__ == "__main__":
    app()
