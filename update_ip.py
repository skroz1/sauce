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

# update_ip.py
# Module for the updateMyIP command in the sraus project.

import typer
from utils import network
from route53 import route53

def updateMyIP(ctx: typer.Context, hostname: str):
    """
    Update the specified A record with the calling host's current IP.
    """
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
    typer.run(updateMyIP)

