#!/usr/bin/env python3

import unittest
import json
from handler import SauceData, get_terminal_width
import sys
import os

class TestSauceData(unittest.TestCase):
    def setUp(self):
        # Create test data with at least ten rows and ten columns
        self.headerlabels = {    "key1": "Key 1",
                                 "key2": "Key 2",
                                 "key3": "Key 3",
                                 "key4": "Key 4",
                                 "key5": "Key 5",
                                 "key6": "Key 6",
                                 "key7": "Key 7",
                                 "key8": "Key 8",
                                 "key9": "Key 9",
                                 "key10": "Key 10" }
        self.test_data = [
                            {
                            "key2": "nonimperiousness Imojean",
                            "key9": "Dvina multistate",
                            "key6": "Mahaska flowerer carinulate",
                            "key4": "unprotestingly",
                            "key8": "misdeemful rubberizes",
                            "key5": "Gaullism",
                            "key1": "stifles econometrician",
                            "key3": "rustler",
                            "key7": "Tbi halieutically",
                            "key10": "orange-tree"
                            },
                            {
                            "key5": "cicer torrentiality waer",
                            "key7": "acarari Wellston nonamazement",
                            "key8": "stut",
                            "key6": "homogentisic",
                            "key3": "spleeniest Laurita subopaquely",
                            "key2": "twie Laveta Iriartea",
                            "key1": "self-doubt berwick",
                            "key10": "Kikai Thelma Galeorchis",
                            "key9": "effemination tensely TMIS",
                            "key4": "Grote"
                            },
                            {
                            "key6": "protopresbyter",
                            "key4": "mullocky unduteous",
                            "key5": "crocodility somatotropin",
                            "key1": "carneau vifda pairer",
                            "key2": "intelligent",
                            "key9": "jazzbow unmunificent",
                            "key8": "acromiodeltoid",
                            "key7": "snodly instrokes",
                            "key3": "weenong strade lense",
                            "key10": "omnipotences unablative"
                            },
                            {
                            "key2": "subalary micromelus",
                            "key1": "reattendance monoglycerid dismalness",
                            "key9": "Mattox Remoboth",
                            "key8": "Phylactolaema playa",
                            "key3": "unmissionized wynds",
                            "key5": "consistorial messalian Titanichthys",
                            "key10": "membranous gotta slopping",
                            "key4": "buttermouth Lenten",
                            "key7": "taxidermize grantsmanship",
                            "key6": "naloxone redisable cabinet-maker"
                            },
                            {
                            "key9": "misstopping brazenfacedly",
                            "key5": "octonarius glowed",
                            "key8": "clubwood crenels",
                            "key6": "transvectant",
                            "key3": "Camille cutlassfishes",
                            "key2": "pranidhana",
                            "key10": "man-child chlorinators",
                            "key4": "Anicetus Kraul nondictatorially",
                            "key1": "hitched juridical",
                            "key7": "Caltha accentors"
                            },
                            {
                            "key3": "whimper",
                            "key7": "lampads",
                            "key6": "mancando",
                            "key2": "hirudins Achaia",
                            "key8": "Garald boroughlet neighborer",
                            "key9": "hypoxemia",
                            "key10": "nonconscientious bamboo fuddlement",
                            "key5": "antivice",
                            "key1": "nonindustrious",
                            "key4": "Hattiesburg"
                            },
                            {
                            "key8": "DOM Pheny",
                            "key6": "focalisation",
                            "key3": "workbooks caffetannin Scitamineae",
                            "key5": "Hokiang antifoggant",
                            "key2": "thermotical archaeologically",
                            "key4": "Grider",
                            "key1": "ascii Ardoch tahanun",
                            "key10": "hansel shaksheer",
                            "key7": "hematobium taboring precompensate",
                            "key9": "Kreigs countertime ingratefully"
                            },
                            {
                            "key4": "pyroxyle spectroscopy barringer",
                            "key2": "inferrible apostolicalness",
                            "key9": "Wolfsburg outgain Roderfield",
                            "key8": "word-group forwork",
                            "key5": "Brahmany Trudy",
                            "key7": "pyrographer dinettes",
                            "key10": "Scotchify shallow-forded",
                            "key6": "combatter unspecifiedly skillfulnesses",
                            "key1": "respirator puffing",
                            "key3": "hydromagnetics"
                            },
                            {
                            "key1": "sonometer",
                            "key7": "misdiagnosed",
                            "key9": "Heywood morga carefulnesses",
                            "key8": "praetextae",
                            "key5": "angelically Musca heterogynous",
                            "key2": "Aecidiomycetes nonpurifying",
                            "key10": "twi-form taxology",
                            "key4": "tinhorn",
                            "key6": "rowboats lathyrism",
                            "key3": "aswail Cathartidae"
                            },
                            {
                            "key3": "requiteless democratising serendipitous",
                            "key8": "outdistances lestobiotic",
                            "key4": "hurting pandoors",
                            "key7": "herbage slidderness ironman",
                            "key1": "cartwheel",
                            "key9": "revilements",
                            "key10": "ultrabelieving endoabdominal self-glorified",
                            "key2": "undon unmercenarily specula",
                            "key5": "peritonealize Dondi cyclothurine",
                            "key6": "redolences Valerlan"
                            }
                        ]

    # test: verify that the data is appended correctly
    def test_append(self):
        # Create an instance of SauceData
        sauce_data = SauceData()

        # Append test data to SauceData
        for row in self.test_data:
            sauce_data.append(row)

        # Verify that the data is appended correctly
        self.assertEqual(len(sauce_data.data), len(self.test_data))
        self.assertEqual(sauce_data.data[-1], self.test_data[-1])

    # test: verify _str_json returns a json string
    def test_str_json(self):
        # Create an instance of SauceData with test data
        sauce_data = SauceData(data=self.test_data, output_format="json")

        # Convert to JSON string and back again
        json_str = str(sauce_data)
        rejson = json.loads(json_str)

        # compare the original data to the rejson
        self.assertEqual(rejson, self.test_data)

    # test: verify _str_csv returns a csv string
    def test_str_csv(self):
        # Create an instance of SauceData with test data
        sauce_data = SauceData(data=self.test_data, output_format="csv")

        # Convert to CSV string
        csv_str = str(sauce_data)

        # re-read the csv into an array of dicts, using the header row as key names
        csv_lines = csv_str.splitlines()
        csv_lines = [line.split(",") for line in csv_lines]
        csv_lines = [line for line in csv_lines if line]
        csv_header = csv_lines[0]
        csv_data = csv_lines[1:]
        csv_data = [dict(zip(csv_header, line)) for line in csv_data]

        # Verify that the CSV string is generated correctly
        self.assertEqual(csv_data, self.test_data)

    # test: verify _str_csv returns a csv string with custom headers
    def test_str_csv_with_labels(self):
        # Create an instance of SauceData with test data
        sauce_data = SauceData(data=self.test_data, output_format="csv")
        sauce_data.headerlabels = self.headerlabels

        # Convert to CSV string
        csv_str = str(sauce_data)

        # lint the csv string
        csv_lines = csv_str.splitlines()
        csv_lines = [line.split(",") for line in csv_lines]
        csv_lines = [line for line in csv_lines if line]

        # this test doesn't actually verify the csv string is correct, just that it's valid csv
        # todo: re-ingest the csv string and compare to the original data

        # Verify that the CSV string is generated correctly
        #self.assertEqual(csv_str, 'col1,col2,col3,col4,col5,col6,col7,col8,col9,col10\nvalue1,value2,value3,value4,value5,value6,value7,value8,value9,value10\n')

    # test: verify _str_table returns a string and truncates the table if it's too wide.  Default headers
    def test_str_table(self):
        # Create an instance of SauceData with test data
        sauce_data = SauceData(data=self.test_data, output_format="table")

        # Convert to table string
        table_str = str(sauce_data)
        # get the width of the longest line in table_str
        terminal_width = get_terminal_width()
        table_lines = table_str.splitlines()
        table_width = max(len(line) for line in table_lines)

        # verify the width of the table is less than or equal to the terminal width
        self.assertLessEqual(table_width, terminal_width)

    # test: verify _str_table returns a string and truncates the table if it's too wide.  Custom headers
    def test_str_table_with_labels(self):
        # Create an instance of SauceData with test data
        sauce_data = SauceData(data=self.test_data, output_format="table")
        sauce_data.headerlabels = self.headerlabels

        # Convert to table string
        table_str = str(sauce_data)
        # get the width of the longest line in table_str
        terminal_width = get_terminal_width()
        table_lines = table_str.splitlines()
        table_width = max(len(line) for line in table_lines)

        # verify the width of the table is less than or equal to the terminal width
        self.assertLessEqual(table_width, terminal_width)

if __name__ == '__main__':
    unittest.main()