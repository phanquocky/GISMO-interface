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
@time: 5/12/22 8:48 AM
@file: parse_files.py
@desc: Script for calling the different parsers to parse all the output files
       from our experiments.
"""

import argparse
from datetime import datetime
import os
from output_parser import EncodingOutputParser, \
    ILPOutputParser, ISOutputParser
import pathlib

parser = argparse.ArgumentParser()

required_args = parser.add_argument_group("Required arguments")
required_args.add_argument("--expid", type=str, required=True,
                           help="Experiment ID.")
required_args.add_argument("--exptype", type=str, required=True,
                           choices=["encoding", "ilp", "gis"],
                           help="Experiment type.")

optional_args = parser.add_argument_group("Optional arguments")
optional_args.add_argument("--enctype", type=str, required=False,
                           choices=["ilp", "gis"],
                           help="Encoding type, only applicable if exptype == 'encoding'.")
optional_args.add_argument("--skip_parsed_files", required=False,
                           action="store_true",
                           help="Skip files if they have already been parsed.")

args = parser.parse_args()

LOCAL_PROJECT_DIR = os.getenv('PROJECT_DIR')
DATA_DIR = os.getenv('DATA_DIR')
RESULTS_DIR = DATA_DIR + '/results/{expid}-{exptype}'.format(expid=args.expid, exptype=args.exptype)

OUT_DIR = DATA_DIR + '/exp-data/{expid}-{exptype}'.format(expid=args.expid, exptype=args.exptype)


def makedir(thedir):
    if not os.path.isdir(thedir):
        os.makedirs(thedir)


missing_timeout_files = set()

if args.exptype == 'encoding':
    if args.enctype == 'gis':
        if os.path.isdir(f'{RESULTS_DIR}/{args.enctype}'):
            for k_dir in os.listdir(f'{RESULTS_DIR}/{args.enctype}'):
                if os.path.isdir(f'{RESULTS_DIR}/{args.enctype}/{k_dir}'):
                    for networktype in os.listdir(f'{RESULTS_DIR}/{args.enctype}/{k_dir}'):
                        subdir = f'{RESULTS_DIR}/{args.enctype}/{k_dir}/{networktype}'
                        print(subdir)
                        print(networktype)
                        for file in os.listdir(subdir):
                            out_file = file
                            print(out_file)
                            print('networktype:', networktype)

                            # Check what kind of file we're dealing with and identify
                            # corresponding timeout file:
                            if 'encoder' in file:
                                timeout_file = out_file.replace('encoder', 'timeout')
                            else:
                                continue

                            # Identify corresponding source file:
                            basefile = timeout_file.replace('.timeout.out.xz', '')

                            encoded_dir = f'{DATA_DIR}/instances/{args.enctype}/{k_dir}/{networktype}'
                            network_file = f'{DATA_DIR}/instances/networks/{networktype}/{basefile}'
                            extension = 'gcnf.gz'
                            encoding_file = f'{encoded_dir}/{basefile}.{extension}'
                            print('encoding file', encoding_file)
                            json_subdir = f'{OUT_DIR}/{args.enctype}/{k_dir}/{networktype}'
                            makedir(json_subdir)
                            pathlib.Path(json_subdir).mkdir(parents=True, exist_ok=True)
                            json_file = f'{json_subdir}/{basefile}.{extension}.json.gz'
                            if args.skip_parsed_files and os.path.exists(json_file):
                                continue
                            if not os.path.exists(encoding_file):
                                print("Encoding file does not exist!")
                                encoding_file = None
                            k = int(k_dir.replace('k', ''))
                            output_parser = EncodingOutputParser(f'{subdir}/{out_file}',
                                                                 f'{subdir}/{timeout_file}',
                                                                 network_file,
                                                                 encoding_file,
                                                                 k)
                            output_parser.save_results(json_file)
    elif args.enctype == 'ilp':
        if os.path.isdir(f'{RESULTS_DIR}/ilp'):
            for cnfg in os.listdir(f'{RESULTS_DIR}/ilp'):
                for k_dir in os.listdir(f'{RESULTS_DIR}/ilp/{cnfg}'):
                    if 'setting' in k_dir:
                        continue
                    for networktype in os.listdir(f'{RESULTS_DIR}/ilp/{cnfg}/{k_dir}'):
                        subdir = f'{RESULTS_DIR}/ilp/{cnfg}/{k_dir}/{networktype}'
                        for file in os.listdir(subdir):
                            out_file = file
                            print('outfile:', out_file)

                            # Check what kind of file we're dealing with and identify
                            # corresponding timeout file:
                            if 'encoder' in file:
                                timeout_file = out_file.replace('encoder', 'timeout')
                            else:
                                continue

                            # Identify corresponding source file:
                            basefile = timeout_file.replace('.timeout.out.xz', '')

                            encoded_dir = f'{DATA_DIR}/instances/ilp/{cnfg}/{k_dir}/{networktype}'

                            k = int(k_dir.replace('k', ''))
                            network_file = f'{DATA_DIR}/instances/networks/{networktype}/{basefile}'
                            extension = 'lp.gz'
                            encoding_file = f'{encoded_dir}/{basefile}.{extension}'
                            print('encoding file', encoding_file)
                            json_subdir = f'{OUT_DIR}/ilp/{cnfg}/{k_dir}/{networktype}'
                            makedir(json_subdir)
                            pathlib.Path(json_subdir).mkdir(parents=True, exist_ok=True)
                            json_file = f'{json_subdir}/{basefile}.{extension}.json.gz'
                            if args.skip_parsed_files and os.path.exists(json_file):
                                continue
                            if not os.path.exists(encoding_file):
                                print("Encoding file does not exist!")
                                encoding_file = None
                            output_parser = EncodingOutputParser(f'{subdir}/{out_file}',
                                                                 f'{subdir}/{timeout_file}',
                                                                 network_file,
                                                                 encoding_file,
                                                                 k)
                            output_parser.save_results(json_file)

elif args.exptype in ['ilp', 'gis']:
    for cnfg in os.listdir(RESULTS_DIR):
        if os.path.isdir(f'{RESULTS_DIR}/{cnfg}'):
            for k_dir in os.listdir(f'{RESULTS_DIR}/{cnfg}'):
                if 'setting' in k_dir:
                    continue
                for networktype in os.listdir(f'{RESULTS_DIR}/{cnfg}/{k_dir}'):
                    subdir = f'{RESULTS_DIR}/{cnfg}/{k_dir}/{networktype}'
                    for file in os.listdir(subdir):
                        out_file = file
                        print(out_file)

                        # Check what kind of file we're dealing with and identify
                        # corresponding timeout file:
                        if 'solver' in file:
                            timeout_file = out_file.replace('solver', 'timeout').replace('.cnf.gz', '.cnf')
                            if not os.path.exists(f'{subdir}/{timeout_file}'):
                                print(f"Timeout file {subdir}/{timeout_file} does not exist!")
                                missing_timeout_files.add(f'{subdir}/{timeout_file}')
                        else:
                            continue

                        # Identify corresponding source file:
                        basefile = timeout_file.replace('.timeout.out.xz', '')
                        json_subdir = f'{OUT_DIR}/{cnfg}/{k_dir}/{networktype}'
                        makedir(json_subdir)

                        if args.exptype == 'ilp':
                            json_file = f'{json_subdir}/{basefile}.json.gz'
                            if args.skip_parsed_files and os.path.exists(json_file):
                                continue
                            output_parser = ILPOutputParser(f'{subdir}/{out_file}',
                                                            f'{subdir}/{timeout_file}')
                            output_parser.save_results(json_file)
                        elif args.exptype == 'gis':
                            json_file = f'{json_subdir}/{basefile}.json.gz'
                            if args.skip_parsed_files and os.path.exists(json_file):
                                continue
                            output_parser = ISOutputParser(f'{subdir}/{out_file}',
                                                           f'{subdir}/{timeout_file}')
                            output_parser.save_results(json_file)

print(missing_timeout_files)
today = datetime.now().strftime("%Y-%m-%d")
with open(f'{today}_{args.expid}-{args.exptype}_missing-timeout-files.txt', 'w') as ofile:
    for timeout_file in missing_timeout_files:
        ofile.write(f'{timeout_file}\n')