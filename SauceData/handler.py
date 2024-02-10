#!/usr/bin/env python3

# data_output/handler.py

import csv
import io
import json
import shutil
from tabulate import tabulate

# valid table formats for tabulate
tabletypes = [ "plain", "simple", "github", "grid", "fancy_grid", "pipe", "orgtbl", "jira",
    "presto", "pretty", "psql", "rst", "mediawiki", "moinmoin", "youtrack", "html",
    "unsafehtml", "latex", "latex_raw", "latex_booktabs", "latex_longtable", "textile", "tsv" ]

class SauceData:
    def __init__(self, data=[], 
                datatype="simple", 
                output_format='table', 
                output_file=None, 
                table_format="presto"
    ):

        self.data = data
        self.output_format = output_format
        self.output_file = output_file
        self.datatype = datatype
        
        # the minimum number of columns to display on the left
        # why is this needed again?
        self.mincol = 0

        # Truncate the table if it's too wide by default
        self.width = get_terminal_width()
        self.truncate = True
            
        # verify the table format is valid
        if table_format not in tabletypes:
            raise ValueError(f"Invalid table format: {table_format}")
        self.table_format = table_format

        self.headers = generate_headers(data) or []
        self.headerlabels = {}
    
    def append(self, newdata):
        #self.data.append(newdata)
        # verify newdata is a dict and return ValueError if not
        if not isinstance(newdata, dict):
            raise ValueError(f"Data must be a dictionary, not {type(newdata)}")
        
        # check headers.  any headers in newdata but not in self.headers should be added to 
        # self.headers
        for key in newdata.keys():
            if key not in self.headers:
                self.headers.append(key)
        # append newdata to self.data
        self.data.append(newdata)
        return self.data

    def __str__(self):
        if self.output_file:
            raise ValueError("Cannot convert to string when an output file is specified.")
        if self.output_format == 'json':
            return self._str_json()
        elif self.output_format == 'csv':
            return self._str_csv()
        elif self.output_format == 'table':
            return self._str_table()
        else:
            raise ValueError(f"Unsupported output format: {self.output_format}")

    # just dump the data as a json string.  This ignores the headerlabels
    def _str_json(self):
        return json.dumps(self.data, indent=4)

    def _str_csv(self):
        if not self.data:
            return ""
        output = io.StringIO()

        # Initialize fieldnames as an empty list
        fieldnames = []

        # Check if header labels should be applied and filter out None mappings
        if self.headerlabels:
            # Iterate over the keys of headerlabels to preserve the order
            for key in self.headerlabels.keys():
                # Check if the key is in headers and the mapping is not None
                if key in self.headers and self.headerlabels[key] is not None:
                    # Append the mapping to fieldnames
                    fieldnames.append(self.headerlabels[key])
                elif key not in self.headers and self.headerlabels[key] is not None:
                    # If the key is not in headers but has a non-None mapping, consider including it
                    # This line is optional and depends on your requirements
                    fieldnames.append(self.headerlabels[key])
        else:
            # If there are no header labels, use the original headers
            fieldnames = self.headers

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for row in self.data:
            # Prepare data row, considering headerlabels remapping and skipping None mappings
            remapped_row = {}
            for field, value in row.items():
                # Skip fields mapped to None
                if self.headerlabels.get(field, field) is None:
                    continue
                new_key = self.headerlabels.get(field, field) if field in self.headerlabels else field
                remapped_row[new_key] = value

            # Write the row to CSV, ensuring only included keys are written
            filtered_row = {key: remapped_row[key] for key in fieldnames if key in remapped_row}
            writer.writerow(filtered_row)

        return output.getvalue()

    # output to a table.  if headerlabels is set, use it to remap the headers
    def _str_table(self):
        if not self.data:
            return ""
        
        # Initialize final_headers as an empty list
        final_headers = []

        # Check if header labels should be applied and filter out None mappings
        if self.headerlabels:
            # Iterate over the headerlabels dict to preserve key order
            for header_label_key in self.headerlabels.keys():
                # Check if the current key is in self.headers
                if header_label_key in self.headers:
                    # Get the new header name using the current key
                    new_header = self.headerlabels[header_label_key]
                    # If the new header name is not None, add it to final_headers
                    if new_header is not None:
                        final_headers.append(new_header)
                else:
                    # If the header_label_key is not in self.headers but has a valid mapping, add the mapping
                    if self.headerlabels[header_label_key] is not None:
                        final_headers.append(self.headerlabels[header_label_key])
        else:
            # If there are no header labels, use the original headers
            final_headers = self.headers

        # Prepare the data for tabulation, considering the header labels
        remapped_data = []
        for row in self.data:
            # Initialize an ordered list for the current row according to final_headers
            ordered_row = []
            for original_header in self.headers:
                new_header = self.headerlabels.get(original_header, original_header)
                if new_header in final_headers:
                    # Append the value to ordered_row only if the new_header is not skipped
                    ordered_row.append(row.get(original_header, ''))
            remapped_data.append(ordered_row)

        # Fit the table columns to the terminal width if truncate is enabled
        if self.truncate:
            remapped_data, final_headers = fit_table_columns(self.width, remapped_data, final_headers, mincol=3)

        # Now call tabulate with the correctly prepared data and final_headers
        return tabulate(remapped_data, headers=final_headers, tablefmt=self.table_format)

###
### Helper functions
###
        
def generate_headers(data):
    newheaders = []
    for row in data:
        for key in row.keys():
            if key not in newheaders:
                newheaders.append(key)
    return newheaders

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

# new version of fit_table_columns
def new_fit_table_columns(terminal_width, data, headers, mincol, extwidth=3):
    """
    Fit the table columns to the terminal width for data in the form of an array of dicts.
    
    Parameters:
    terminal_width (int): The width of the terminal.
    data (list of dicts): The data to be displayed in the table, where each row is a dict.
    headers (list): The headers for the table, determining column order.
    mincol (int): The minimum number of columns to display on the left.
    extwidth (int): The extra width to add to each column to account for the table borders.
    
    Returns:
    tuple: A tuple of truncated data (list of dicts) and headers (list).
    """
    if len(headers) < mincol:
        raise ValueError("Not enough columns in data to satisfy mincol requirement")

    def column_width(col_data):
        max_length = max(len(str(item)) for item in col_data)
        return max_length + extwidth

    # Calculate initial widths for mincol columns
    total_width = sum(column_width([row[header] for row in data]) for header in headers[:mincol])
    
    new_data = []
    new_headers = headers[:mincol]

    # Try to add remaining columns if they fit within terminal_width
    for header in headers[mincol:]:
        col_data = [row[header] for row in data]
        col_width = column_width(col_data)

        if total_width + col_width > terminal_width:
            break  # Stop adding columns if next one exceeds terminal_width

        new_headers.append(header)
        total_width += col_width

    # Truncate data dicts based on the new headers
    for row in data:
        truncated_row = {header: row[header] for header in new_headers}
        new_data.append(truncated_row)

    return new_data, new_headers

# old version of fit_table_columns
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
