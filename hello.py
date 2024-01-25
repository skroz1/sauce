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
from utils.logging import get_loggers

# Get the loggers
loggers = get_loggers()

def hello():
    """
    A sample command that prints "Hello, world!".
    """
    loggers['debug'].debug("Executing hello() subcommand")

    print("Hello, world!")

if __name__ == "__main__":
    typer.run(hello)

