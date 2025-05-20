# -----------------------------------------------------------
#
# Profile
# Copyright (C) 2025  Damiano Lombardi
# -----------------------------------------------------------
#
# licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, print to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# ---------------------------------------------------------------------

from qgis.PyQt.QtWidgets import QDialog, QMessageBox
from teksi_module_management_tool.libs import pgserviceparser
from teksi_module_management_tool.utils.plugin_utils import PluginUtils

DIALOG_UI = PluginUtils.get_ui_class("service_edit_dialog.ui")


class ServiceEditDialog(QDialog, DIALOG_UI):
    def __init__(self, selected_service=None, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.existingService_label.setText(selected_service)

        self.__existing_service_config = pgserviceparser.service_config(selected_service)
        self.existingDatabase_label.setText(self.__existing_service_config.get("dbname", ""))

        self.buttonBox.accepted.connect(self._accept)

    def _accept(self):

        if self.newDatabase_lineEdit.text() == "":
            QMessageBox.critical(self, "Error", "Please enter a database name.")
            return

        if self.newService_lineEdit.text() == "":
            QMessageBox.critical(self, "Error", "Please enter a service name.")
            return
