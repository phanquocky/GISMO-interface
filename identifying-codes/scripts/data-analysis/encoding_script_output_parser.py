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
@time: 17 Oct 2022
@file: encoding_script_output_parser.py
@desc: Class for parsing the output files from the encoding experiments.
"""

import lzma
import re

class EncodingScriptOutputParser:
    def __init__(self, output_file, k):
        """

        :param output_file: File containing the output of the
                            encode_network.py script.

        """

        self._output_file = output_file
        self._k = k
        self._data = {
            'building_successful': True,
            'building_t/o': False, 'building_m/o': False,
            'encoding_successful': True,
            'encoding_t/o': False, 'encoding_m/o': False,
        }

        self._pat_encoding = {
            't_wallclock_building': re.compile(r'\d{4}-\d{2}-\d{2}, \d{2}h\d{2}m\d{2}s: Building took (?P<t_wallclock_building>\d+\.\d+) wallclock seconds\.', re.DOTALL),
            't_process_building': re.compile(r'\d{4}-\d{2}-\d{2}, \d{2}h\d{2}m\d{2}s: Building took (?P<t_process_building>\d+\.\d+) CPU seconds\.', re.DOTALL),
            't_wallclock_encoding': re.compile(r'\d{4}-\d{2}-\d{2}, \d{2}h\d{2}m\d{2}s: Encoding took (?P<t_wallclock_encoding>\d+\.\d+) wallclock seconds for k = \d+\.', re.DOTALL),
            't_process_encoding': re.compile(r'\d{4}-\d{2}-\d{2}, \d{2}h\d{2}m\d{2}s: Encoding took (?P<t_process_encoding>\d+\.\d+) CPU seconds for k = \d+\.', re.DOTALL),
            't_limit': re.compile(r'c Time limit:\s+(?P<t_limit>\d+) s', re.DOTALL),
            'm_limit': re.compile(r'c Memory limit:\s+(?P<m_limit>\d+)', re.DOTALL),
        }

        self._data.update({field: None for field in self._pat_encoding.keys()})

        self._alo_pat = re.compile(r' a(?P<idx>\d+):\s*y\d+ .+', re.DOTALL)
        self._detection_pat = re.compile(r' d(?P<idx>\d+):\s*- x\d+ .+', re.DOTALL)
        self._uniqueness_pat = re.compile(r' u(?P<idx>\d+):\s*x\d+ .+', re.DOTALL)

        self._ints = ['t_limit', 'm_limit']
        self._floats = ['t_wallclock_building', 't_process_building',
                        't_wallclock_encoding', 't_process_encoding']

    def get_encoding_script_output_data(self):
        return self._data

    def _convert_data_types(self):
        for field in self._data:
            if field in self._ints and self._data[field] is not None:
                self._data[field] = int(self._data[field])
            elif field in self._floats and self._data[field] is not None:
                self._data[field] = float(self._data[field])

    def _parse_line(self, line, patterns):
        for field, pat in patterns.items():
                m = re.match(pat, line)
                if m is not None:
                    self._data[field] = m.group(field)

    def parse_encoding_script_output(self):
        with lzma.open(self._output_file, 'rt', encoding='utf-8') as infile:
            building_successful = True
            encoding_successful = True
            for l in infile.readlines():
                if 'Building FAILED' in l:
                    building_successful = False
                    continue
                elif 'Encoding FAILED' in l:
                    encoding_successful = False
                    continue
                elif building_successful and \
                        ('MemoryError' in l or '1001: Out of memory' in l):
                    encoding_successful = False
                    self._data['encoding_m/o'] = True
                    break
                else:
                    self._parse_line(l, self._pat_encoding)
            self._data['building_successful'] = building_successful
            self._data['encoding_successful'] = encoding_successful

            self._convert_data_types()

            if not building_successful:
                self._data['t_wallclock_building'] = None
                self._data['t_process_building'] = None

            if not encoding_successful:
                self._data['t_wallclock_encoding'] = None
                self._data['t_process_encoding'] = None
