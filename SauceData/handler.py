#!/usr/bin/env python3

# data_output/handler.py

import csv
import io
import json
from tabulate import tabulate

class SauceData:
    def __init__(self, data=[], datatype="simple", output_format='table', output_file=None):
        self.data = data
        self.output_format = output_format
        self.output_file = output_file
        self.datatype = datatype

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

        # Filter out headers that are mapped to None in headerlabels
        if self.headerlabels:
            fieldnames = [self.headerlabels.get(header, header) for header in self.headers if self.headerlabels.get(header, header) is not None]
        else:
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
        
        # Initialize an empty list for the final headers
        final_headers = []

        # Check if header labels should be applied and filter out None mappings
        if self.headerlabels:
            # Apply remapping to headers and skip None mappings
            for header in self.headers:
                new_header = self.headerlabels.get(header, header)
                if new_header is not None:  # Skip headers mapped to None
                    final_headers.append(new_header)
        else:
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

        # Now call tabulate with the correctly prepared data and final_headers
        return tabulate(remapped_data, headers=final_headers, tablefmt="presto")

def generate_headers(data):
    newheaders = []
    for row in data:
        for key in row.keys():
            if key not in newheaders:
                newheaders.append(key)
