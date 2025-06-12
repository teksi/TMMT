#!/usr/bin/env bash

# Remove when oqtopus is available on PyPI
pip install --target plugin/teksi_module_management_tool/libs git+https://github.com/opengisch/oqtopus.git
exit 0

pip download -r requirements.txt --only-binary :all: -d temp/
            unzip -o "temp/*.whl" -d plugin/teksi_module_management_tool/libs
            rm -r temp
            # set write rights to group (because qgis-plugin-ci needs it)
            chmod -R g+w plugin/teksi_module_management_tool/libs
