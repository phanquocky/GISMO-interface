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
@time: 7/7/22 12:54 PM
@file: cnf_parser.py
@desc: Class for parsing the CNFs that encode Identifying Codes problems.
"""

import gzip


class CNFparser:
    def __init__(self, cnf_file, cnf_type=''):
        """

        :param cnf_file: File containing CNF in DIMACS format
        :param cnf_type: Choose from:
                            - cnf   (standard CNF)
                            - gcnf  (grouped CNF)
        """
        assert cnf_type != '', "Please specify cnf type, choose from ['cnf', 'gcnf']."
        self._cnf_file = cnf_file
        self._cnf_type = cnf_type

        self._top = -1

        self._data = {
            'n_vars': -1, 'n_Pvars': -1, 'n_Avars': -1,
            'n_groups': -1,
            'n_clauses': -1, 'n_clauses_duplicates_removed': -1,
            'n_hard_clauses': -1, 'n_soft_clauses': -1}

    def get_cnf_data(self):
        return self._data

    def parse_cnf(self):
        clauses = set()
        with gzip.open(self._cnf_file, 'rt', encoding='utf-8') as infile:
            n_groups = 0
            n_hard_clauses = 0
            n_soft_clauses = 0

            for line in infile.readlines():

                # Get basic CNF info:
                if line.startswith('p'):
                    if self._cnf_type == 'wcnf':
                        _, _, n_vars, n_clauses, top = line.split()
                        self._data['n_vars'] = int(n_vars)
                        self._data['n_clauses'] = int(n_clauses)
                        self._top = int(top)
                    else:
                        _, _, n_vars, n_clauses = line.split()
                        self._data['n_vars'] = int(n_vars)
                        self._data['n_clauses'] = int(n_clauses)

                # Get size of set of interest for grouped CNF
                elif self._cnf_type == 'gcnf' and line.startswith('c ind'):
                    # the "-3" is to correct for the "c def" at the start of the
                    # line and the "0" at the end of it
                    self._data['n_Pvars'] = len(set(line.split())) - 3

                # Count number of groups
                elif self._cnf_type == 'gcnf' and line.startswith('c grp'):
                    n_groups += 1

                # Count number of hard clauses
                elif self._cnf_type == 'wcnf' and line.startswith(str(self._top) + ' '):
                    n_hard_clauses += 1

                # Count number of soft clauses
                elif self._cnf_type == 'wcnf' and \
                    not line.startswith('c') and \
                    not line.startswith('p') and \
                    not line.startswith(str(self._top) + ' '):
                    n_soft_clauses += 1

                if self._cnf_type == 'gcnf' and \
                    self._data['n_vars'] > -1 and \
                    self._data['n_clauses'] > -1 and \
                    n_groups > 0 and \
                    not line.startswith('c grp'):
                    print('Breaking')
                    break

                # # Remove duplicate clauses in the unweighted CNF encoding
                # if self._cnf_type == 'gcnf' and \
                #         not line.startswith('c') and \
                #         not line.startswith('p'):
                #     clauses.add(' '.join([elt for elt in sorted(line.split()[:-1])]))

            self._data['n_groups'] = n_groups
            if self._cnf_type == 'wcnf':
                self._data['n_hard_clauses'] = n_hard_clauses
                self._data['n_soft_clauses'] = n_soft_clauses

            # Compute number of auxiliary variables
            if self._cnf_type == 'gcnf':
                self._data['n_Avars'] = self._data['n_vars'] - self._data['n_Pvars']

            # # Count the number of clauses when you have removed duplicates
            # self._data['n_clauses_duplicates_removed'] = len(clauses)