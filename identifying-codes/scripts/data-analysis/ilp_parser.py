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
@time: 7/22/22 12:33 PM
@file: ilp_parser.py
@desc: Class for parsing ILP programs.
"""

import gzip
import re

class ILPparser:
    def __init__(self, ilp_file):
        """

        :param ilp_file: File containing ILP program.

        """

        self._ilp_file = ilp_file
        self._data = {
            'n_vars': -1, 'n_binaries': -1, 'n_generals': -1,
            'n_alo_csts': -1, 'n_detection_csts': -1, 'n_uniqueness_csts': -1,
            'n_csts': -1}

        self._alo_pat = re.compile(r' a(?P<idx>\d+):\s*y\d+ .+', re.DOTALL)
        self._detection_pat = re.compile(r' d(?P<idx>\d+):\s*- x\d+ .+', re.DOTALL)
        self._uniqueness_pat = re.compile(r' u(?P<idx>\d+):\s*x\d+ .+', re.DOTALL)

    def get_ilp_data(self):
        return self._data

    def parse_ilp(self):
        with gzip.open(self._ilp_file, 'rb') as infile:
            n_alo_csts = 0
            n_detection_csts = 0
            n_uniqueness_csts = 0
            n_binaries = 0
            n_generals = 0
            counting_binaries = False
            counting_generals = False
            for line in infile.readlines():
                l = line.decode('utf-8')
                if l.startswith(' a'):
                    m = re.match(self._alo_pat, l)
                    if m is not None:
                        n_alo_csts = max(n_alo_csts, int(m.group('idx')))
                elif l.startswith(' d'):
                    m = re.match(self._detection_pat, l)
                    if m is not None:
                        n_detection_csts = max(n_detection_csts, int(m.group('idx')))
                elif l.startswith(' u'):
                    m = re.match(self._uniqueness_pat, l)
                    if m is not None:
                        n_uniqueness_csts = max(n_uniqueness_csts, int(m.group('idx')))
                elif 'Binaries' in l and not counting_binaries:
                    counting_binaries = True
                    continue
                elif counting_binaries and 'Generals' not in l:
                    n_binaries = n_binaries + len(l.split())
                    continue
                elif counting_binaries and 'Generals' in l and not counting_generals:
                    counting_generals = True
                    counting_binaries = False
                    continue
                elif counting_generals and 'End' not in l:
                    n_generals = n_generals + len(l.split())
                    continue
                elif 'End' in l:
                    counting_generals = False

            n_alo_csts = n_alo_csts + 1
            n_detection_csts = n_detection_csts + 1
            n_uniqueness_csts = n_uniqueness_csts + 1

            self._data['n_binaries'] = n_binaries
            self._data['n_generals'] = n_generals
            n_vars = n_binaries + n_generals
            self._data['n_vars'] = n_vars
            self._data['n_alo_csts'] = n_alo_csts
            self._data['n_detection_csts'] = n_detection_csts
            self._data['n_uniqueness_csts'] = n_uniqueness_csts
            n_csts = n_alo_csts + n_detection_csts + n_uniqueness_csts
            self._data['n_csts'] = n_csts
