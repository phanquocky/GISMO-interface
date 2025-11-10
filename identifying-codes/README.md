# Identifying Codes

In this repository, we collect scripts and (extra) experiments and results, corresponding to our paper:

> *Solving the Identifying Code Set Problem with Grouped Independent Support*, Anna L.D. Latour, Arunabha Sen, Kuldeep S. Meel, IJCAI 2023 (paper #4051). [[paper pdf](https://www.ijcai.org/proceedings/2023/0219.pdf), [extended version](https://raw.githubusercontent.com/latower/latower.github.io/master/files/misc/LatEtAl23-extended_2023-08-23.pdf)]

Note: as we were doing the experiment, we had not yet settled on a name for `gismo`, so in this repository we refer to it as `arjun-grp`.

## Related sources

- The `gismo` code: [github.com/meelgroup/gismo](https://github.com/meelgroup/gismo).
- PBLib (needed for encoding cardinality constraints): [github.com/master-keying/pblib](https://github.com/master-keying/pblib)

## License information and attribution

The code in this repository is distributed under an MIT license: [LICENSES/MIT_LICENSE](./identifying-codes-public/LICENCES/MIT_LICENSE).
The networks in the `instances/networks` are obtained from:
- [networkrepository.com](https://networkrepository.com)
- [github.com/kaustav-basu/IdentifyingCodes](https://github.com/kaustav-basu/IdentifyingCodes)
and are replicated with their corresponding license files in their directories.

All other data published in this repository is distributed under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
license: [LICENSES/by-nc-sa.markdown](./identifying-codes-public/LICENCES/by-nc-sa.markdown).


## Organisation
* [binaries/](./identifying-codes-public/binaries) Contains the `gismo` binary used for our experiments.
* [exp-data/](./identifying-codes-public/exp-data) Contains the `json` files with information on the experiments, obtained from parsing the raw output files in the [results/](./identifying-codes-public/results) subdirectories.
* [instances/](./identifying-codes-public/instances)
  * [gis/](./identifying-codes-public/instances/gis) Grouped CNF (GCNF) encodings of input problems.
  * [ilp/](./identifying-codes-public/instances/ilp) ILP encodings of input problems.
  * [networks/](./identifying-codes-public/instances/networks) The input networks (edge lists and matrix market format).
* [results/](./identifying-codes-public/results) Contains the raw output files from our experiments.
* [scripts/](./identifying-codes-public/scripts)
  * [data-analysis/](./identifying-codes-public/scripts/data-analysis) Scripts for parsing the output files and organising the data into `json` files. Scripts for reading out `json` files and aggregating the data into `pandas` data frames. 
  * [data-visualisation/](./identifying-codes-public/scripts/data-visualisation) iPython Notebook for visualising the results. Output files for figures and tables in paper and extended version of paper.
  * [encoding/](./identifying-codes-public/scripts/encoding) Scripts for building an Identifying Code Set problem out of an input network. Scripts for converting that problem into ILP of GCNF.
  * [helpers/](./identifying-codes-public/scripts/helpers) Helper scripts.
  * [pbs/](./identifying-codes-public/scripts/pbs) Scripts for running the experiments on a cluster.
* [LICENSES](./identifying-codes-public/LICENSE) License information for the code in this repository and all the data in this repository (*except* the netoworks in the [networks/](./identifying-codes-public/instances/networks) directory and its subdirectories).
* [README.md](./identifying-codes-public/README.md) This file.
