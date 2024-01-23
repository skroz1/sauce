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

import typer
from hello import hello
from ses_key import seskey
from update_ip import updateMyIP

app = typer.Typer()

@app.callback()
def main(
    ctx: typer.Context,
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Perform a dry run without making any changes."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress all non-error output."),
    force: bool = typer.Option(False, "--force", "-f", help="Force update even if not recommended.")
):
    ctx.ensure_object(dict)
    ctx.obj["DRY_RUN"] = dry_run
    ctx.obj["QUIET"] = quiet
    ctx.obj["FORCE"] = force

app.command()(hello)
app.command()(seskey)
app.command()(updateMyIP)

if __name__ == "__main__":
    app()
