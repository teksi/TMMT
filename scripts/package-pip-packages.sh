#!/usr/bin/env bash

for LIB in oqtopus pum pgserviceparser; do
  DNL=$(git grep $LIB requirements.txt | cut -d: -f2)
  pip download $DNL --no-deps --only-binary :all: -d temp/
done
unzip -o "temp/*.whl" -d teksi_module_management_tool/libs
rm -r temp
# set write rights to group (because qgis-plugin-ci needs it)
chmod -R g+w teksi_module_management_tool/libs
