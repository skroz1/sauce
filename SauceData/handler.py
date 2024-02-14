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
                table_format="presto",
                prioritize_columns=[]

    ):
        # verify the imported data is a list of dictionaries
        try:
            # Ensure data is a list of dictionaries
            if not all(isinstance(item, dict) for item in data):
                raise ValueError("All items in the data list must be dictionaries.")
            self.data = data
        except Exception as e:
            raise ValueError(f"Invalid data: {e}")

        #self.data = data
        self.output_format = output_format
        self.output_file = output_file
        self.datatype = datatype
        
        # the minimum number of columns to display on the left
        # why is this needed again?
        self.mincol = 0

        # Truncate the table if it's too wide by default
        self.width = get_terminal_width()
        self.truncate = True
        
        self.prioritize_columns = prioritize_columns

        # verify the table format is valid
        if table_format not in tabletypes:
            raise ValueError(f"Invalid table format: {table_format}")
        self.table_format = table_format

        self.headers = generate_headers(data) or []
        self.headerlabels = {}
    
    def append(self, newdata):
        if not isinstance(newdata, dict):
            raise ValueError(f"Data must be a dictionary, not {type(newdata).__name__}")
        
        for key in newdata.keys():
            if key not in self.headers:
                self.headers.append(key)
        
        self.data.append(newdata)

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
        
        # Initial headers based on data keys
        final_headers = self.headers[:]

        # Apply header labels, dropping columns with None value
        final_headers = [self.headerlabels.get(header, header) for header in final_headers if self.headerlabels.get(header, header) is not None]

        # Prioritize columns, ensuring prioritized columns come first
        # Note: Prioritization happens after dropping columns flagged with None
        prioritized_headers = [col for col in self.prioritize_columns if col in final_headers]
        other_headers = [col for col in final_headers if col not in self.prioritize_columns]
        final_headers = prioritized_headers + other_headers

        # Convert data to a list of lists format, considering dropped columns
        remapped_data = []
        for row in self.data:
            row_data = [row.get(header, '') for header in self.headers if self.headerlabels.get(header, header) is not None]
            remapped_data.append(row_data)

        # Fit the table columns to the terminal width if truncate is enabled
        if self.truncate:
            remapped_data, adjusted_final_headers = fit_table_columns(self.width, remapped_data, final_headers, self.mincol)
            # Adjust headers in line with the data after truncation
            final_headers = [final_headers[i] for i in range(len(adjusted_final_headers))]

        # Generate table string with tabulate
        return tabulate(remapped_data, headers=final_headers, tablefmt=self.table_format)

    def sort_data(self, sort_by):
        """
        Sorts the data based on specified columns and directions.

        Parameters:
        sort_by (list of tuples): Each tuple contains the column name followed by the sort direction ('asc' or 'desc').
        """
        if not sort_by:
            return  # No sorting if sort_by is empty or None

        # Build a list of keys for sorting, with reverse flags for each key based on sort direction
        sort_keys = [(lambda row, key=key: row.get(key, ""), reverse) for key, direction in sort_by for reverse in (direction.lower() == 'desc',)]
        
        self.data.sort(key=lambda row: tuple(key(row) for key, reverse in sort_keys), reverse=any(reverse for _, reverse in sort_keys))

    def filter_data(self, conditions):
        """
        Filters the data based on specified conditions with error handling.

        Parameters:
        conditions (list of functions): Each function takes a row (dict) as input and returns True if the row meets the condition.
        """
        if not conditions:
            return  # No filtering if conditions are empty or None

        filtered_data = []
        for row in self.data:
            try:
                if all(condition(row) for condition in conditions):
                    filtered_data.append(row)
            except Exception as e:
                print(f"Error applying filter conditions to row {row}: {e}")
        self.data = filtered_data


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

def fit_table_columns(terminal_width, data, headers, mincol, extwidth=5):
    """
    Adjust columns to fit within the terminal width for data formatted as a list of lists.

    Parameters:
    terminal_width (int): The width of the terminal.
    data (list of lists): The data to be displayed in the table, each sublist is a row.
    headers (list): The headers for the table.
    mincol (int): The minimum number of columns to display on the left.
    extwidth (int): The extra width to add to each column to account for padding and spacing.

    Returns:
    tuple: Adjusted data (list of lists) and headers (list) fitting within the terminal width.
    """
    # Determine the width of each column based on content
    col_widths = [max(len(str(item)) for item in col) + extwidth for col in zip(*data, headers)]

    # Start with the minimum required columns
    total_width = sum(col_widths[:mincol])
    included_cols = mincol

    # Add more columns as space allows
    for width in col_widths[mincol:]:
        if total_width + width <= terminal_width:
            included_cols += 1
            total_width += width
        else:
            break

    # Adjust headers and data based on included columns
    adjusted_headers = headers[:included_cols]
    adjusted_data = [row[:included_cols] for row in data]

    return adjusted_data, adjusted_headers
