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
@time: 5/11/22 12:56 PM
@file: output_parser.py
@desc: Generic Class for parsing the output files of experiment scripts.
"""

import gzip
import json
import lzma
import os
import re
from cnf_parser import CNFparser
from ilp_parser import ILPparser
from cplex_output_parser import CPLEXOutputParser
from encoding_script_output_parser import EncodingScriptOutputParser

class OutputParser:

    def __init__(self, output_file, timeout_file):
        self._output_file = output_file
        self._timeout_file = timeout_file
        self._data = dict()
        self._json_str = ''

        # Parsing patterns for encoder.out and solver.out files:
        self._pat_output_header = {
            'benchmark': re.compile(r'c (Benchmark|Network):\s+(?P<benchmark>[\w\-.]+\.(edges|txt|mtx)(\.gz)?)\s*', re.DOTALL),
            'network_type': re.compile(r'c Network\s*type:\s+(?P<network_type>\w+)\s*', re.DOTALL),
            'setting': re.compile(r'c Setting:\s+setting(?P<setting>\d)\s*', re.DOTALL),
            'timeout': re.compile(r'c Time limit:\s+(?P<timeout>\d+)s\s*', re.DOTALL),
            'timeout_build': re.compile(r'c Build time limit:\s+(?P<timeout_build>\d+) s\s*', re.DOTALL),
            'timeout_encode': re.compile(r'c Encode time limit:\s+(?P<timeout_encode>\d+) s\s*', re.DOTALL),
            'memory_limit': re.compile(r'c Memory limit:\s+(?P<memory_limit>\d+)\s*', re.DOTALL),
            'configuration': re.compile(r'c Configuration:\s+(?P<configuration>\d+)\s*', re.DOTALL),
            'ilp_configuration': re.compile(r'c ILP configuration:\s+(?P<ilp_configuration>config\d+)\s*', re.DOTALL),
            'encoding': re.compile(r'c Encoding:\s+(?P<encoding>(maxsat|ilp|is|independent support))\s*', re.DOTALL),
            'command': re.compile(r'c Command:\s+(?P<command>[\w\-.\\/\s=]+)\s*\n', re.DOTALL),
            'date': re.compile(r'c Date:\s+(?P<date>\d{4}-\d{2}-\d{2})\s*', re.DOTALL),
            'solver_out_file': re.compile(r'c This file:\s+(?P<solver_out_file>[\w\-.\\/]+)\s*', re.DOTALL),
            'EXPID': re.compile(r'c EXPID:\s+(?P<EXPID>\w+)\s*', re.DOTALL),
            'JOBID': re.compile(r'c JOB_*ID:\s+(?P<JOBID>\d+\.\w+)\s*', re.DOTALL),
            'project_dir': re.compile(r'c Project directory:\s+(?P<project_dir>[\w\-\\/]+)\s*', re.DOTALL),
            'repository': re.compile(r'c Repository:\s+(?P<repository>git@github.com:[\w.\-/\\]+\.git)\s*', re.DOTALL),
            'branch': re.compile(r'c Branch:\s+(?P<branch>\w+)\s*', re.DOTALL),
            'commit': re.compile(r'c Commit:\s+(?P<commit>\w+)\s*', re.DOTALL),
        }

        # Parsing patterns for timeout file:
        self._pat_timeout = {
            'signal': re.compile(r'Command terminated by signal (?P<signal>\d+)\s*', re.DOTALL),
            'command': re.compile(r'\s+Command being timed: \"(?P<command>[\w\-\\\/\.\s=]+)\"\s*', re.DOTALL),
            'utime': re.compile(r'\s+User time \(seconds\): (?P<utime>\d+\.\d+)\s*', re.DOTALL),
            'stime': re.compile(r'\s+System time \(seconds\): (?P<stime>\d+\.\d+)\s*', re.DOTALL),
            'percent_cpu': re.compile(r'\s+Percent of CPU this job got: (?P<percent_cpu>\d+(\.\d+)?)%\s*', re.DOTALL),
            'wtime': re.compile(r'\s+Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): (?P<wtime>(\d+:)?\d+:\d+)\s*', re.DOTALL),
            'max_res_set_size': re.compile(r'\s+Maximum resident set size \(kbytes\): (?P<max_res_set_size>\d+)\s*', re.DOTALL),
            'ave_res_set_size': re.compile(r'\s+Average resident set size \(kbytes\): (?P<ave_res_set_size>\d+)\s*', re.DOTALL),
            'page_size': re.compile(r'\s+Page size \(bytes\): (?P<page_size>\d+)\s*', re.DOTALL),
            'exit_status': re.compile(r'\s+Exit status: (?P<exit_status>\d+)\s*', re.DOTALL)
        }

        # Initialise dictionary with parsed data:
        self._data.update({'output_header': {field: None for field in self._pat_output_header.keys()}})
        self._data.update({'timeout_info': {field: None for field in self._pat_timeout.keys()}})

        # Specify datatypes of certain fields:
        self._ints = ['setting', 'timeout', 'timeout_build', 'timeout_encode', 'memory_limit', 'configuration',
                      'max_res_set_size', 'ave_res_set_size', 'page_size', 'exit_status']
        self._floats = ['utime', 'stime', 'percent_cpu']

        self._parse_basics()

    def _convert_data_types(self):
        for group in self._data:
            for field in self._data[group]:
                if field in self._ints and self._data[group][field] is not None:
                    self._data[group][field] = int(self._data[group][field])
                elif field in self._floats and self._data[group][field] is not None:
                    self._data[group][field] = float(self._data[group][field])

    def _parse_line(self, line, groups_patterns):
        for group, patterns in groups_patterns:
            for field, pat in patterns.items():
                m = re.match(pat, line)
                if m is not None:
                    self._data[group][field] = m.group(field)

    def _parse_basics(self):
        with lzma.open(self._output_file, 'rt', encoding='utf-8') as infile:
            print(self._output_file)
            for line in infile.readlines():
                self._parse_line(line, [('output_header', self._pat_output_header)])
        if os.path.exists(self._timeout_file):
            with lzma.open(self._timeout_file, 'rt', encoding='utf-8') as infile:
                for line in infile.readlines():
                    self._parse_line(line, [('timeout_info', self._pat_timeout)])

    def save_results(self, results_file):
        json_str = json.dumps(self._data, indent=4) + "\n"
        json_bytes = json_str.encode('utf-8')
        with gzip.open(results_file, 'w') as rfile:
            rfile.write(json_bytes)


class EncodingOutputParser(OutputParser):
    """
    TODO: Add functionality for determining how long the encoding time was per
    value of k.
    """

    def __init__(self, output_file, timeout_file, network_file, encoding_file, k):
        OutputParser.__init__(self, output_file, timeout_file)

        self._network_file = network_file
        self._encoding_file = encoding_file
        self._k = k

        self._pat_network_data = {
            'type': re.compile(r'[c\\] Type:\s*(?P<type>\w+)\s*', re.DOTALL),
            'twins_removed': re.compile(r'[c\\] Twins removed\?\s*(?P<twins_removed>(yes|no))\s*', re.DOTALL),
            'n_nodes': re.compile(r'[c\\] Number of nodes( \(after preprocess\))?:\s*(?P<n_nodes>\d+)\s*', re.DOTALL),
            'n_edges': re.compile(r'[c\\] Number of edges( \(after preprocess\))?:\s*(?P<n_edges>\d+)\s*', re.DOTALL),
        }
        self._pat_encoding = {
            'setting_full': re.compile(r'[c\\] Setting:\s*(?P<setting_full>\d\. [\w .]+)\s*', re.DOTALL),
            'encoding': re.compile(r'[c\\] Encoding:\s*(?P<encoding>(MaxSAT|ILP|IS|maxsat|ilp|is|independent support))\s*', re.DOTALL),
            'budget': re.compile(r'[c\\] Budget:\s*(?P<budget>(\d+|N/A))\s*', re.DOTALL),
            'k': re.compile(r'[c\\] k:\s*(?P<k>\d+)\s*', re.DOTALL),
            'approach': re.compile(r'[c\\] Approach:\s*(?P<approach>(one|two)-step)\s*', re.DOTALL),
            'encoding_script': re.compile(r'[c\\] Generated with:\s*(?P<encoding_script>[\w.\-]+)\s*', re.DOTALL),
            'repository': re.compile(r'[c\\] Repository:\s+(?P<repository>git@github.com:[\w.\-/\\]+\.git)\s*', re.DOTALL),
            'branch': re.compile(r'[c\\] Branch:\s+(?P<branch>\w+)\s*', re.DOTALL),
            'commit': re.compile(r'[c\\] Commit:\s+(?P<commit>\w+)\s*', re.DOTALL),
            'machine': re.compile(r'[c\\] Machine:\s+(?P<machine>\w+)\s*', re.DOTALL),
            'date': re.compile(r'[c\\] Date \(YYYY-MM-DD\):\s+(?P<date>\d{4}-\d{2}-\d{2})\s*', re.DOTALL),
        }

        self._data.update({'network_data': {field: None for field in self._pat_network_data.keys()}})
        self._data.update({'encoding_details': {field: None for field in self._pat_encoding.keys()}})
        self._data['network_data']['network_file'] = self._network_file
        self._data['encoding_details']['encoding_file'] = self._encoding_file

        self._ints.extend(['n_nodes', 'n_edges', 'k'])
        self._floats.extend([])

        if self._encoding_file is not None:
            self._parse_encoding()
            if '.cnf.' in self._encoding_file or \
                '.wcnf.' in self._encoding_file or \
                '.gcnf.' in self._encoding_file:
                cnf_type = 'cnf' if '.cnf.' in self._encoding_file \
                    else 'wcnf' if '.wcnf.' in self._encoding_file \
                    else 'gcnf' if '.gcnf.' in self._encoding_file \
                    else ''
                print('cnf_type:', cnf_type, 'for file', self._encoding_file)
                cnf_parser = CNFparser(cnf_file=self._encoding_file,
                                       cnf_type=cnf_type)
                cnf_parser.parse_cnf()
                cnf_data = cnf_parser.get_cnf_data()
                self._data['cnf_data'] = cnf_data
            elif '.lp.' in self._encoding_file:
                ilp_parser = ILPparser(ilp_file=self._encoding_file)
                ilp_parser.parse_ilp()
                ilp_data = ilp_parser.get_ilp_data()
                self._data['ilp_data'] = ilp_data

        if self._data['encoding_details']['k'] is None:
            self._data['encoding_details']['k'] = self._k

        encoding_script_output_parser = EncodingScriptOutputParser(
            self._output_file, int(self._data['encoding_details']['k']))
        encoding_script_output_parser.parse_encoding_script_output()
        encoding_data = encoding_script_output_parser.get_encoding_script_output_data()
        self._data['encoding_details'].update(encoding_data)
        # print("Encoding file:", self._encoding_file)
        # if self._encoding_file is not None:
        #     self._parse_encoding()

        self._convert_data_types()

    def _parse_encoding(self):
        print("PARSING ENCODING")
        with gzip.open(self._encoding_file, 'rt', encoding='utf-8') as infile:
            for line in infile.readlines():
                self._parse_line(line, [('network_data', self._pat_network_data),
                                        ('encoding_details', self._pat_encoding)])


class MaxSATOutputParser(OutputParser):

    def __init__(self, output_file, timeout_file, solver='open-wbo'):
        OutputParser.__init__(self, output_file, timeout_file)

        # Parsing patterns for Problem Statistics
        self._pat_problem_stats = {
            'n_variables': re.compile(r'c \|\s+Number of variables:\s*(?P<n_variables>\d+)[\w\s|]+', re.DOTALL),
            'n_hard_clauses': re.compile(r'c \|\s+Number of hard clauses:\s*(?P<n_hard_clauses>\d+)\s+\|\s*', re.DOTALL),
            'n_soft_clauses': re.compile(r'c \|\s+Number of soft clauses:\s*(?P<n_soft_clauses>\d+)\s+\|\s*', re.DOTALL),
            'parse_time': re.compile(r'c \|\s+Parse time:\s*(?P<parse_time>\d+\.\d+) s\s+\|\s*', re.DOTALL)
        }

        # Parsing patterns for Solver Settings
        self._pat_open_wbo_settings = {
            'algorithm': re.compile(r'c \|\s+Algorithm:\s*(?P<algorithm>\w+)\s+\|\s*', re.DOTALL),
            'partition_strategy': re.compile(r'c \|\s+Partition Strategy:\s*(?P<partition_strategy>\w+)\s+\|\s*', re.DOTALL),
            'graph_type': re.compile(r'c \|\s+Graph Type:\s*(?P<graph_type>\w+)\s+\|\s*', re.DOTALL),
            'n_partitions': re.compile(r'c \|\s+Number of partitions:\s*(?P<n_partitions>\d+)\s+\|\s*', re.DOTALL),
            'soft_partition_ratio': re.compile(r'c \|\s+Soft partition ratio:\s*(?P<soft_partition_ratio>\d+\.\d+)\s+\|\s*', re.DOTALL),
            'cardinality_encoding': re.compile(r'c \|\s+Cardinality Encoding:\s*(?P<cardinality_encoding>\w+)\s+\|\s*', re.DOTALL)
        }
        self._pat_maxhs_settings = {
            'maxhs_version': re.compile(r'c MaxHS (?P<maxhs_version>\d+\.\d+\.\d+)\s*', re.DOTALL),
        }

        self._pat_maxhs_stats = {
            'n_variables': re.compile(r'c Dimacs Vars:\s*(?P<n_variables>\d+)\s*', re.DOTALL),
            'n_hard_clauses': re.compile(r'c HARD: #Clauses =\s*(?P<n_hard_clauses>\d+),.*', re.DOTALL),
            'n_soft_clauses': re.compile(r'c SOFT: #Clauses =\s*(?P<n_soft_clauses>\d+),.*', re.DOTALL),
            'parse_time': re.compile(r'c Parse time:\s*(?P<parse_time>\d+(\.\d+)?)\s*', re.DOTALL),
            'maxhs_mem': re.compile(r'c MEM MB:\s*(?P<maxhs_mem>\d+)\s*', re.DOTALL),
            'maxhs_cpu': re.compile(r'c CPU:\s*(?P<maxhs_cpu>\d+\.\d+)\s*', re.DOTALL),
        }

        if solver == 'open-wbo':
            self._data.update({'open-wbo_stats': {field: None for field in self._pat_problem_stats}})
            self._data.update({'open-wbo_settings': {field: None for field in self._pat_open_wbo_settings}})
        elif solver == 'maxhs':
            self._data.update({'maxhs_settings': {field: None for field in self._pat_maxhs_settings}})
            self._data.update({'maxhs_stats': {field: None for field in self._pat_maxhs_stats}})
        self._data.update({'solution_info': {'optimised_value': 0,
                                             'optimum_found': False,
                                             'solution': None}})

        self._ints.extend(['n_variables', 'n_hard_clauses', 'n_soft_clauses', 'n_partitions', 'optimised_value'])
        self._floats.extend(['parse_time', 'soft_partition_ratio'])

        if solver == 'open-wbo':
            self._parse_openwbo_output()
        elif solver == 'maxhs':
            self._parse_maxhs_output()

        self._convert_data_types()

    def _parse_openwbo_output(self):
        with lzma.open(self._output_file, 'rt', encoding='utf-8') as rfile:
            for line in rfile.readlines():
                self._parse_openwbo_line(line)

    def _parse_openwbo_line(self, line):
        if line.startswith('c'):
            for result_group, pattern_dict in [('problem_stats', self._pat_problem_stats),
                                               ('open-wbo_settings', self._pat_open_wbo_settings)]:
                for field, pat in pattern_dict.items():
                    m = re.match(pat, line)
                    if m is not None:
                        self._data[result_group][field] = m.group(field)
        elif line.startswith('o'):
            _, self._data['solution_info']['optimised_value'] = line.split()
        elif line.startswith('s'):
            if line.find('OPTIMUM FOUND'):
                self._data['solution_info']['optimum_found'] = True
        elif line.startswith('v'):
            self._parse_solution(line)

    def _parse_solution(self, line):
        """ TODO: link solution to the variable map in the MaxSAT input file to retrieve names of nodes in original problem.

        :param line: Solution line from open-wbo output.
        :return: None
        """
        self._data['solution_info']['solution'] = line[2:].strip()

    def _parse_maxhs_output(self):
        with lzma.open(self._output_file, 'rt', encoding='utf-8') as rfile:
            for line in rfile.readlines():
                self._parse_maxhs_line(line)

    def _parse_maxhs_line(self, line):
        if line.startswith('c'):
            for result_group, pattern_dict in [('maxhs_stats', self._pat_maxhs_stats),
                                               ('maxhs_settings', self._pat_maxhs_settings)]:
                for field, pat in pattern_dict.items():
                    m = re.match(pat, line)
                    if m is not None:
                        self._data[result_group][field] = m.group(field)
        elif line.startswith('o'):
            _, self._data['solution_info']['optimised_value'] = line.split()
        elif line.startswith('s'):
            if line.find('OPTIMUM FOUND'):
                self._data['solution_info']['optimum_found'] = True
        elif line.startswith('v'):
            self._parse_solution(line)


class ILPOutputParser(OutputParser):

    def __init__(self, output_file, timeout_file):
        OutputParser.__init__(self, output_file, timeout_file)

        self._pat_rows_cols = re.compile(r'Reduced MIP has (?P<rows>\d+) rows, \d+ columns, and (?P<nonzeros>\d+) nonzeros\.', re.DOTALL)
        self._pat_mip_vars = re.compile(r'Reduced MIP has (?P<bin>\d+) binaries, \d+ generals, \d+ SOSs, and \d+ indicators\.', re.DOTALL)

        self._ints.extend(['n_rows', 'n_binaries', 'n_non_zeros', 'k'])
        self._floats.extend(['optimised_value', 'solution_time', 'deterministic_time'])

        cplex_parser = CPLEXOutputParser(output_file=output_file)
        cplex_parser.parse_cplex_output()
        self._cplex_output_data = cplex_parser.get_cplex_data()
        self._data['cplex_info'] = self._cplex_output_data['cplex_info']
        self._data['solution_info'] = self._cplex_output_data['solution_info']
        self._convert_data_types()
        print(self._data)


class ISOutputParser(OutputParser):

    def __init__(self, output_file, timeout_file):
        OutputParser.__init__(self, output_file, timeout_file)

        # Parsing patterns for Solver Settings
        self._pat_solver_info = {
            'arjun_version': re.compile(r'c Arjun Version:\s*(?P<arjun_version>\w+)\s*', re.DOTALL),
            'cryptominisat_version': re.compile(r'c CryptoMiniSat version\s*(?P<cryptominisat_version>\d+\.\d+\.\d+)\s*', re.DOTALL),
            'seed': re.compile(r'c \[arjun\] using seed:\s*(?P<seed>\d+)\s*', re.DOTALL),
            'arjun_time': re.compile(r'c \[arjun\] finished T:\s*(?P<arjun_time>\d+\.\d+)\s*', re.DOTALL),
        }
        self._set_size_pat = re.compile(r'c \[arjun\] final set size:\s*(?P<opt_val>\d+)[\w\s:.%]+', re.DOTALL)

        self._data.update({'arjun_info': {field: None for field in self._pat_solver_info.keys()}})
        self._data.update({'solution_info': {'optimised_value': -1,
                                             'solution': None}})

        k_pat = re.compile(r'(\/[\w-]+)+\/config(-)?\d\/k(?P<k>\d+)\/.+', re.DOTALL)
        print("get k from output file:", output_file)
        m = re.match(k_pat, output_file)
        if m is not None:
            self._data['solution_info']['k'] = int(m.group('k'))

        self._ints.extend(['seed', 'optimised_value'])

        self._parse_arjun_output()
        self._convert_data_types()

    def _parse_arjun_output(self):
        read_solution = False
        with lzma.open(self._output_file, 'rt', encoding='utf-8') as rfile:
            for line in rfile.readlines():
                if line.startswith('c ind'):
                    solution = [elt for elt in line.replace('c ind ', '').split()][:-1]
                    self._data['solution_info']['solution'] = ' '.join(solution)
                    read_solution = True
                elif line.startswith('c'):
                    for field, pat in self._pat_solver_info.items():
                        m = re.match(pat, line)
                        if m is not None:
                            self._data['arjun_info'][field] = m.group(field)
                    if read_solution:
                        m = re.match(self._set_size_pat, line)
                        if m is not None:
                            self._data['solution_info']['optimised_value'] = m.group('opt_val')



