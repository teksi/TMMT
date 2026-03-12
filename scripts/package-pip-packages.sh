#!/usr/bin/env bash

set -e  # Exit on any error
set -o pipefail  # Catch errors in pipes

echo "Downloading PyPI packages..."
mkdir -p temp

for LIB in oqtopus pum pgserviceparser; do
  echo "Processing $LIB..."
  DNL=$(git grep $LIB requirements.txt | cut -d: -f2)
  if [ -z "$DNL" ]; then
    echo "ERROR: Could not find $LIB in requirements.txt"
    exit 1
  fi
  echo "  Downloading: $DNL"
  pip download $DNL --no-deps --only-binary :all: -d temp/
done

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
