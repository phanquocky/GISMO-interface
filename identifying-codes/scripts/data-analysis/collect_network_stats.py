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
@time: 8/10/22 3:30 PM
@file: network_stats.py
@desc: Script for analysing some statistics of our networks.
"""

import gzip
import json
import networkx as nx
import os
from scipy.io import mmread
from statistics import median, mean

LOCAL_PROJECT_DIR = os.getenv('PROJECT_DIR')
DATA_DIR = os.getenv('DATA_DIR')
NETWORK_DIR = f'{DATA_DIR}/instances/networks'
STATS_DIR = f'{DATA_DIR}/exp-data/network-stats'

# The file with relevant networks contains the networks that we consider for the
# experiments. They are selected as real-world networks of varying sizes that
# do not contain any errors in their encoding.
relevant_networks = []
relevant_network_file = f'{LOCAL_PROJECT_DIR}/scripts/data-analysis/relevant_networks.txt'

with open(relevant_network_file, 'r') as infile:
    relevant_networks = [line.replace('\n', '') for line in infile.readlines()]


print(relevant_networks)

networks = []
for network_dir in os.listdir(NETWORK_DIR):
    if os.path.isdir(f'{NETWORK_DIR}/{network_dir}'):
        for network_file in os.listdir(f'{NETWORK_DIR}/{network_dir}'):
            if network_file in relevant_networks:
                networks.append(f'{NETWORK_DIR}/{network_dir}/{network_file}')

print(networks)



def create_from_edge_list(the_network_file):
    with gzip.open(the_network_file, 'rt', encoding='utf-8') as infile:
        edges = [tuple(line.split()[:2])
                 for line in infile.readlines()
                 if not (line.startswith('#') or line.startswith('%'))]
        G = nx.Graph()
        G.add_edges_from(edges)
        return G

def create_from_mtx_file(the_network_file):
    G = nx.Graph(mmread(the_network_file))
    return G

def save_stats(stats_file, stats_dict):
    json_str = json.dumps(stats_dict, indent=4) + "\n"
    json_bytes = json_str.encode('utf-8')
    with gzip.open(stats_file, 'w') as rfile:
        rfile.write(json_bytes)

for network in networks:
    print(network)
    if '.mtx' in network:
        print("Creating from mtx file")
        G = create_from_mtx_file(network)
    else:
        print("Creating from edge list")
        G = create_from_edge_list(network)
    degree_sequence = sorted((d for n, d in G.degree()), reverse=True)
    new_data = {
        'network': os.path.basename(network),
        'n_nodes': G.number_of_nodes(),
        'n_edges': G.number_of_edges(),
        'degree_dist': degree_sequence,
        'max_degree': max(degree_sequence),
        'med_degree': median(degree_sequence),
        'mean_degree': mean(degree_sequence),
        'clustering': nx.clustering(G),
        'n_triangles': nx.triangles(G)
    }
    out_file = f'{STATS_DIR}/{os.path.basename(network)}'
    save_stats(out_file, new_data)

