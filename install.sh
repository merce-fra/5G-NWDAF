#!/bin/bash -e

# Ensure the script is executed from the root directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment 'venv' not found. Please create it first."
    exit 1
fi

# Activate virtualenv
source venv/bin/activate

# Create .packages folder and clean it
mkdir -p ".packages"
rm -f .packages/*

# Install build/package pre-requisites
pip install --upgrade pip
pip install --upgrade build

# Build 3GPP APIs package
cd 3gpp-apis/
if [ ! -f "run.sh" ]; then
    echo "'run.sh' not found in 3gpp-apis directory. Please ensure it exists."
    exit 1
fi
bash run.sh
cd output/
python -m build
cd ../..

# Build libcommon package
cd libcommon
python -m build
cd ..

# Copy the packages
cp -rf 3gpp-apis/output/dist/*.whl .packages/
cp -rf libcommon/dist/*.whl .packages/
chmod -R 777 .packages/


# Run the local PyPi server
if docker ps | grep -q local_pypi; then
    echo "Stopping existing local_pypi container..."
    docker stop local_pypi
    docker rm local_pypi
fi

docker run -d --name local_pypi -p 80:8080 -v "$(pwd)/.packages:/data/packages" pypiserver/pypiserver:latest run