#!/usr/bin/env python3

# update_ip.py
# Module for the updatemyip command in the sauce project.

import typer
from utils import network
from route53 import route53
from utils.logging import get_loggers

# Get the loggers
loggers = get_loggers()

def updatemyip(ctx: typer.Context, hostname: str):
    """
    Update the specified A record with the calling host's current IP.
    """
    loggers['debug'].debug("Executing updatemyip() subcommand")

    dry_run = ctx.obj["DRY_RUN"]
    quiet = ctx.obj["QUIET"]
    force = ctx.obj["FORCE"]

    try:
        public_ip = network.get_public_ip()
        if network.is_private_ip(public_ip) and not force:
            raise ValueError("Obtained IP is a private address. Use --force to override.")

        hostname, domain_appended = network.validate_hostname(hostname)
        if domain_appended and not quiet:
            typer.echo(f"Warning: Domain part not found in hostname. Using system domain: {hostname.split('.', 1)[1]}")

        client = route53.get_route53_client()
        domain = hostname.split('.', 1)[1]
        zone_id = route53.get_hosted_zone_id(client, domain)
        existing_ip = route53.query_route53(client, zone_id, hostname)

        if existing_ip == public_ip:
            if not quiet:
                typer.echo("Success. No update required.")
        else:
            route53.update_route53_A(client, zone_id, hostname, public_ip, dry_run, quiet)

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)

if __name__ == "__main__":
    typer.run(updatemyip)

