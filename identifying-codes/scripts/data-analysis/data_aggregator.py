# encoding: utf-8
"""
Copyright (C) 2022 Anna L.D. Latour

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

@author: Anna L.D. Latour
@contact: latour@nus.edu.sg
@time: 6/1/22 10:40 AM
@file: data_aggregator.py
@desc: Class for taking the json files that contain experimental data and
       aggregating that data into pandas dataframes for further analysis.
"""

import gzip
import json
import os
import pandas as pd


class DataAggregator:
    def __init__(self,
                 expid: str,
                 exptype: str,
                 json_dir: str,
                 encodings: list = None,
                 k_values: list = None,
                 network_types: list = None,
                 configs: list = None,
                 relevant_fields: dict = None):
        self._expid = expid
        self._exptype = exptype
        self._json_dir = json_dir
        self._encodings = encodings
        self._k_values = k_values
        self._network_types = network_types
        self._configs = configs
        self._relevant_fields = relevant_fields

    def get_data(self):
        if self._exptype == 'encoding':
            return self._read_encoding_results()
        elif self._exptype in ['ilp', 'gis']:
            return self._read_solving_results()
        return False

    def _read_json_contents(self, path_to_file, cnfg='config-0'):
        with gzip.open(path_to_file) as json_file:
            all_instance_data = json.loads(json_file.read())
            data = {'config': cnfg}
            data.update({field: all_instance_data[category][field]
                         for category in self._relevant_fields
                         for field in self._relevant_fields[category]
                         if category in all_instance_data.keys()}
                        )
            return data

    def _read_encoding_results(self):
        data_list = []
        for enc in self._encodings:
            # print('encoding:', enc)
            for k in self._k_values:
                # print('k:', k)
                for network_type in self._network_types:
                    if enc == 'gis':
                        json_dir = f'{self._json_dir}/{self._expid}-{self._exptype}/{enc}/k{k}/{network_type}'
                        # print('json_dir', json_dir)
                        if os.path.isdir(json_dir):
                            for file_name in os.listdir(json_dir):
                                print(file_name)
                                data = self._read_json_contents(f'{json_dir}/{file_name}')
                                data_list.append(data)
                    elif enc == 'ilp':
                        # print("enc = ilp")
                        for cnfg in self._configs:
                            # print("cnfg:", cnfg)
                            json_dir = f'{self._json_dir}/{self._expid}-{self._exptype}/{enc}/{cnfg}/k{k}/{network_type}'
                            # print('ilp json_dir', json_dir)
                            if os.path.isdir(json_dir):
                                for file_name in os.listdir(json_dir):
                                    data = self._read_json_contents(f'{json_dir}/{file_name}',
                                                                    cnfg=cnfg)
                                    data_list.append(data)

        enc_data = pd.DataFrame.from_records(data_list)
        return enc_data

    def _read_solving_results(self):
        data_list = []
        for cnfg in self._configs:
            for k in self._k_values:
                for network_type in self._network_types:
                    json_dir = f'{self._json_dir}/{self._expid}-{self._exptype}/{cnfg}/k{k}/{network_type}'
                    # print('json_dir:', json_dir)
                    if os.path.isdir(json_dir):
                        for file_name in os.listdir(json_dir):
                            data = self._read_json_contents(f'{json_dir}/{file_name}',
                                                            cnfg=cnfg)
                            data['k'] = k
                            data_list.append(data)
        solve_data = pd.DataFrame.from_records(data_list)
        return solve_data
