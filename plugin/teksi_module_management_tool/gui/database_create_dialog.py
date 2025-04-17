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

from qgis.PyQt.QtCore import QUrl, Qt
from qgis.PyQt.QtGui import QColor, QDesktopServices
from qgis.PyQt.QtWidgets import QDialog, QMessageBox
from teksi_module_management_tool.utils.plugin_utils import PluginUtils
from teksi_module_management_tool.utils.qt_utils import OverrideCursor
from teksi_module_management_tool.libs import pgserviceparser

DIALOG_UI = PluginUtils.get_ui_class("database_create_dialog.ui")


class DataBaseCreateDialog(QDialog, DIALOG_UI):
    def __init__(self, selected_service=None, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.db_services_comboBox.clear()
        for service_name in pgserviceparser.service_names():
            self.db_services_comboBox.addItem(service_name)
        self.db_services_comboBox.currentIndexChanged.connect(self._serviceChanged)
        
        if selected_service:
            self.db_services_comboBox.setCurrentText(selected_service)
        else:
            self._serviceChanged()

    def _serviceChanged(self):
        service_name = self.db_services_comboBox.currentText()
        service_config = pgserviceparser.service_config(service_name)

        service_host = service_config.get("host", None)
        service_port = service_config.get("port", None)
        service_dbname = service_config.get("dbname", None)
        service_user = service_config.get("user", None)
        service_password = service_config.get("password", None)
        
        if service_database is None:
            self.db_database_label.setText(self.tr("No database provided by the service"))
            font = self.db_database_label.font()
            font.setItalic(True)
            self.db_database_label.setFont(font)
            return

        self.db_database_label.setText(service_database)
        font = self.db_database_label.font()
        font.setItalic(False)
        self.db_database_label.setFont(font)

        


