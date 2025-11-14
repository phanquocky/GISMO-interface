#!/bin/bash
set -e  # stop on first error (optional, remove if you want to continue even on error)

# echo "Setting up identifying-codes..."
# git clone https://github.com/latower/identifying-codes.git
# cd /app

# check if cadical is already cloned
if [ -d "/app/cadical" ]; then
    echo "cadical directory already exists. Skipping clone."
else
    echo "Setting up cadical..."
    # remove any existing directories to avoid conflicts
    rm -rf /app/pblib
    # rm -rf /app/identifying-codes
    rm -rf /app/cadical
    rm -rf /app/cadiback
    rm -rf /app/project
    rm -rf /app/cryptominisat
    rm -rf /app/louvain-community
    rm -rf /app/gismo

    # setup environment
    echo "Setting up pblib..."
    git clone --recursive https://github.com/master-keying/pblib.git || true
    cd pblib || true
    cmake -H. -Bbuild || true
    cmake --build build || true
    cd build || true
    make install || true
    cd /app || true

    git clone https://github.com/arminbiere/cadical.git
    cd cadical
    ./configure --competition CXXFLAGS="-fPIC"
    make -j$(nproc)
    cd build
    g++ -shared -o libcadical.so -Wl,--whole-archive libcadical.a -Wl,--no-whole-archive -lpthread
    cd /app

    echo "Setting up cadiback..."
    git clone --branch mate --single-branch https://github.com/meelgroup/cadiback.git
    cd cadiback
    rm -f makefile config.hpp libcadiback.so
    CXX=c++ ./configure
    make -j$(nproc)
    export LD_LIBRARY_PATH=/app/cadiback:$LD_LIBRARY_PATH
    cd /app

    echo "Setting up CryptoMiniSat..."
    git clone --branch 5.11.21 https://github.com/msoos/cryptominisat.git project
    cd project
    mkdir build
    cd build
    cmake -DCMAKE_BUILD_TYPE=Release ..
    make -j$(nproc)
    make install
    ldconfig
    cd /app

    echo "Setting up louvain-community..."
    git clone https://github.com/meelgroup/louvain-community
    cd louvain-community
    mkdir build
    cd build
    cmake ..
    make -j4
    make install
    cd /app

    echo "Setting up gismo..."
    git clone https://github.com/meelgroup/gismo.git
    cd gismo
    mkdir build && cd build
    cmake ..
    make -j$(nproc)
    make install
    ldconfig
    cd /app
fi

echo "All setups done."
exec "$@"
