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
@time: 8/7/22 8:37 AM
@file: cplex_output_parser.py
@desc: Class for parsing the output files of CPLEX.
"""

import lzma
import re

class CPLEXOutputParser:

    def __init__(self, output_file):
        """

        :param output_file: File containing the output of the cplex script.

        """

        self._output_file = output_file
        self._data = dict()
        self._pat_rows_cols = re.compile(
            r'Reduced MIP has (?P<rows>\d+) rows, \d+ columns, and (?P<nonzeros>\d+) nonzeros\.', re.DOTALL)
        self._pat_mip_vars = re.compile(
            r'Reduced MIP has (?P<bin>\d+) binaries, \d+ generals, \d+ SOSs, and \d+ indicators\.', re.DOTALL)
        self._pat_cplex = {
            'solution_time': re.compile(r'Solution time =\s+(?P<solution_time>\d+\.\d+) sec\.\s+Iterations = \d+\s+Nodes = \d+', re.DOTALL),
            'deterministic_time': re.compile(r'Deterministic time = (?P<deterministic_time>\d+\.\d+) ticks\s+\(\d+\.\d+ ticks/sec\)', re.DOTALL),
        }
        self._pat_solution = {
            'optimised_value': re.compile(r'MIP - Integer optimal solution:\s+Objective =\s+(?P<optimised_value>\d+\.+\d+e\+\d+)', re.DOTALL),
            'k': re.compile(r'c k:\s+(?P<k>\d+)', re.DOTALL)
        }

        self._data.update({'cplex_info': {field: None for field in self._pat_cplex.keys()}})
        self._data.update({'solution_info': {field: None for field in self._pat_solution.keys()}})

    def get_cplex_data(self):
        return self._data

    def parse_cplex_output(self):
        with lzma.open(self._output_file, 'rt', encoding='utf-8') as infile:
            reading_solution = False
            print("SETTING ALL ROWS ELIMINATED")
            self._data['cplex_info']['all_rows_eliminated_during_preprocessing'] = False

            for l in infile.readlines():
                if '1001: Out of memory' in l:
                    self._data['cplex_info']['memout'] = True
                    continue
                if 'All rows and columns eliminated.' in l:
                    self._data['cplex_info']['all_rows_eliminated_during_preprocessing'] = True
                    self._data['cplex_info']['n_rows'] = None
                    self._data['cplex_info']['n_non_zeros'] = None
                    self._data['cplex_info']['n_binaries'] = None
                    continue
                if 'Variable Name' in l:
                    print("Start reading solution")
                    reading_solution = True
                    self._data['solution_info']['solution'] = list()
                    continue
                if reading_solution:
                    if l.startswith('x'):       # We need only the x variables for the solution
                        var, _ = l.split()
                        self._data['solution_info']['solution'].append(var)
                        continue
                if 'Reduced' in l:
                    m = re.match(self._pat_rows_cols, l)
                    if m is not None:
                        self._data['cplex_info']['n_rows'] = m.group('rows')
                        self._data['cplex_info']['n_non_zeros'] = m.group('nonzeros')
                        continue
                    m = re.match(self._pat_mip_vars, l)
                    if m is not None:
                        self._data['cplex_info']['n_binaries'] = m.group('bin')
                        continue
                    continue
                else:
                    for result_group, pattern_dict in [('cplex_info', self._pat_cplex),
                                                       ('solution_info', self._pat_solution)]:
                        for field, pat in pattern_dict.items():
                            m = re.match(pat, l)
                            if m is not None:
                                self._data[result_group][field] = m.group(field)

                if 'memout' not in self._data['cplex_info']:
                    self._data['cplex_info']['memout'] = False

                if 'all_rows_eliminated_during_preprocessing' not in self._data['cplex_info']:
                    print("REACHED")
                    self._data['cplex_info']['all_rows_eliminated_during_preprocessing'] = False
