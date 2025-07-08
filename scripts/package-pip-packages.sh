#!/usr/bin/env bash

pip download -r requirements.txt --no-deps --only-binary :all: -d temp/
unzip -o "temp/*.whl" -d plugin/teksi_module_management_tool/libs
rm -r temp
# set write rights to group (because qgis-plugin-ci needs it)
chmod -R g+w plugin/teksi_module_management_tool/libs
