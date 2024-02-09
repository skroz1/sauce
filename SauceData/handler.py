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

    # output to csv.  if headerlabels is set, use it to remap the headers
    def _str_csv(self):
        if not self.data:
            return ""
        output = io.StringIO()
        
        # Determine the correct fieldnames after applying any header label remapping
        fieldnames = self.headers if not self.headerlabels else [self.headerlabels.get(header, header) for header in self.headers]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in self.data:
            # Remap the row keys based on self.headerlabels
            remapped_row = {self.headerlabels.get(field, field): value for field, value in row.items()}
            # Ensure the remapped row only includes keys that are in the writer's fieldnames
            writer.writerow({key: remapped_row[key] for key in fieldnames if key in remapped_row})
        
        return output.getvalue()

    # output to a table.  if headerlabels is set, use it to remap the headers
    def _str_table(self):
        if not self.data:
            return ""
        
        # Directly use self.headers if no remapping is required
        headers = self.headers

        # Check if header labels should be applied
        if self.headerlabels:
            # Apply remapping to headers
            headers = [self.headerlabels.get(h, h) for h in headers]

        # Prepare the data for tabulation, remapping keys according to self.headerlabels
        remapped_data = []
        for row in self.data:
            # Apply remapping to each row's keys
            remapped_row = {self.headerlabels.get(k, k): v for k, v in row.items()}
            # Ensure the remapped row is ordered according to the remapped headers
            ordered_row = [remapped_row[h] for h in headers if h in remapped_row]
            remapped_data.append(ordered_row)
        
        # Convert headers to the format expected by tabulate when dealing with a list of lists
        headers = headers if self.headerlabels else "keys"

        # Now call tabulate with the correctly prepared data and headers
        return tabulate(remapped_data, headers=headers, tablefmt="presto")
   

def generate_headers(data):
    newheaders = []
    for row in data:
        for key in row.keys():
            if key not in newheaders:
                newheaders.append(key)
