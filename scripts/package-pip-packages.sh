#!/usr/bin/env bash

set -e  # Exit on any error
set -o pipefail  # Catch errors in pipes

echo "Downloading PyPI packages..."
mkdir -p temp

# Only download oqtopus - it bundles pum and pgserviceparser inside
LIB="oqtopus"
echo "Processing $LIB..."
DNL=$(grep "^$LIB" requirements.txt | head -n1)
if [ -z "$DNL" ]; then
  echo "ERROR: Could not find $LIB in requirements.txt"
  exit 1
fi
echo "  Downloading: $DNL"
pip download $DNL --no-deps --only-binary :all: -d temp/

# Check that wheels were actually downloaded
if ! ls temp/*.whl 1> /dev/null 2>&1; then
  echo "ERROR: No .whl files found in temp/ directory"
  exit 1
fi

echo "Extracting to teksi_module_management_tool/libs..."
unzip -o "temp/*.whl" -d teksi_module_management_tool/libs

echo "Cleaning up..."
rm -r temp

# set write rights to group (because qgis-plugin-ci needs it)
chmod -R g+w teksi_module_management_tool/libs

echo "Done! PyPI packages successfully bundled."
