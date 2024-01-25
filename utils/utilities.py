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
import datetime


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

def fit_table_columns(terminal_width, data, headers, mincol, extwidth=3):
    """
    Fit the table columns to the terminal width.

    Parameters:
    terminal_width (int): The width of the terminal.
    data (list): The data to be displayed in the table.
    headers (list): The headers for the table.
    mincol (int): The minimum number of columns to display on the left. Used for service name, totals, etc.
    extwidth (int): The extra width to add to each column to account for the table borders.

    Returns:
    tuple: A tuple of fitted data list and headers for tabulation.
    """
    if len(headers) < mincol:
        raise ValueError("Not enough columns in data to satisfy mincol requirement")

    def column_width(col):
        max_length = max(len(str(item)) for item in col)
        return max_length + 2  # Adding space for padding

    new_data = [row[:mincol] for row in data]
    new_headers = headers[:mincol]
    width_debug_row = ['Width']  # Debug row to show the width of each column

    total_width = sum(column_width(col) + extwidth for col in zip(*new_data)) + len(new_headers) - 1

    remaining_cols = list(range(mincol, len(headers)))[::-1]

    for i in remaining_cols:
        col = [row[i] for row in data]
        col_width = column_width(col) + extwidth

        if total_width + col_width > terminal_width:
            break

        for row, item in zip(new_data, col):
            row.append(item)
        new_headers.append(headers[i])
        width_debug_row.append(str(col_width))
        total_width += col_width

    # debug row
    #new_data.append(width_debug_row)

    return new_data, new_headers

# convert bytes to other units
def convert_bytes(size_in_bytes, unit="gib"):
    unit = unit.lower()
    units = {
        "kb": 1000,
        "kib": 1024,
        "mb": 1000**2,
        "mib": 1024**2,
        "gb": 1000**3,
        "gib": 1024**3,
        "tb": 1000**4,
        "tib": 1024**4,
        "pb": 1000**5,
        "pib": 1024**5,
        "eb": 1000**6,
        "eib": 1024**6,
    }

    if unit in units:
        return size_in_bytes / units[unit]
    else:
        raise ValueError("Unrecognized unit. Use one of: 'KB', 'KiB', 'MB', 'MiB', 'GB', 'GiB', 'TB', 'TiB', 'PB', 'PiB', 'EB', 'EiB'.")
