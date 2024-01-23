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

# utilities.py
# This module provides various utility functions for the sraus project.

import calendar
import shutil

def get_terminal_width():
    """
    Return the width of the terminal window, if possible.

    Returns:
    int: Width of the terminal or default value 80 if not determinable.
    """
    try:
        return shutil.get_terminal_size().columns
    except AttributeError:
        # Default width if the terminal size cannot be determined
        return 80

def get_last_day_of_month(year, month):
    """
    Return the last day of the specified month and year.

    Parameters:
    year (int): The year.
    month (int): The month.

    Returns:
    int: The last day of the month.
    """
    _, last_day = calendar.monthrange(year, month)
    return last_day

def format_time_period(year, month):
    """
    Return the start and end dates for the given year and month.

    Parameters:
    year (int): The year.
    month (int): The month.

    Returns:
    tuple: A tuple containing the start and end dates in 'YYYY-MM-DD' format.
    """
    last_day = get_last_day_of_month(year, month)
    start_date = first_day_of_month(year, month)
    end_date = f"{year}-{month:02d}-{last_day}"
    return start_date, end_date
