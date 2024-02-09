#!/usr/bin/env python3

import configparser
import os
from pathlib import Path
import typer

from utils.logging import get_loggers

# Get the loggers
loggers = get_loggers()

app = typer.Typer()

def conceal_key(key):
    """
    Conceal the key by showing only the last four characters.
    """
    if key:
        return '*' * (len(key) - 4) + key[-4:]
    else:
        return ''

@app.command()
def configure(
    ctx: typer.Context,
    setting: str = typer.Argument(None, help="Configuration in the format variable=value."),
    section: str = typer.Option("global", "--section", "-s", help="The section of the config file to edit."),
    delete: str = typer.Option(None, "--delete", "-d", help="Delete a specific configuration key.")
):
    """
    Interactively configure AWS credentials and default region, set a specific configuration, or delete a configuration key.
    """
    loggers['debug'].debug("Executing configure() subcommand")
    config = configparser.ConfigParser()
    config_file_path = ctx.obj.get('CONFIG_FILE', os.path.join(Path.home(), ".sauce"))

    # Check if the config file already exists
    if os.path.exists(config_file_path):
        config.read(config_file_path)

    if section not in config:
        config[section] = {}

    if delete:
        if delete in config[section]:
            del config[section][delete]
        else:
            typer.echo(f"Key '{delete}' not found in section '{section}'.", err=True)
            raise typer.Exit(code=1)
    elif setting:
        # Split setting into key and value
        if '=' in setting:
            key, value = setting.split('=', 1)
            config[section][key] = value
        else:
            typer.echo("Invalid setting format. Use 'variable=value'.", err=True)
            raise typer.Exit(code=1)
    else:
        # Interactive configuration
        if section == "global":
            current_access_key = config[section].get('aws_access_key', '')
            current_secret_key = config[section].get('aws_secret_access_key', '')
            entered_access_key = typer.prompt("AWS Access Key", default=conceal_key(current_access_key))
            entered_secret_key = typer.prompt("AWS Secret Access Key", default=conceal_key(current_secret_key), hide_input=True)
            config[section]['aws_access_key'] = current_access_key if entered_access_key == conceal_key(current_access_key) else entered_access_key
            config[section]['aws_secret_access_key'] = current_secret_key if entered_secret_key == conceal_key(current_secret_key) else entered_secret_key
            default_region = config[section].get('region', 'us-east-1')
            config[section]['region'] = typer.prompt("Default region name", default=default_region)

    # Write the configuration to file
    with open(config_file_path, 'w') as configfile:
        config.write(configfile)

    typer.echo(f"Configuration saved to {config_file_path}.")

if __name__ == "__main__":
    app()
