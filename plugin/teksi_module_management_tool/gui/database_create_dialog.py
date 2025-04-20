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


class DatabaseCreateDialog(QDialog, DIALOG_UI):
    def __init__(self, selected_service=None, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.existingService_comboBox.clear()
        for service_name in pgserviceparser.service_names():
            self.existingService_comboBox.addItem(service_name)
        
        if selected_service:
            self.existingService_comboBox.setCurrentText(selected_service)
        
        self.existingService_comboBox.currentIndexChanged.connect(self._serviceChanged)

        self.enterManually_radioButton.toggled.connect(self._enterManuallyToggled)

        self.parameters_ssl_comboBox.clear()
        self.parameters_ssl_comboBox.addItem("Not set", None)
        notSetFont = self.parameters_ssl_comboBox.font()
        notSetFont.setItalic(True)
        self.parameters_ssl_comboBox.setItemData(0, notSetFont, Qt.FontRole)
        self.parameters_ssl_comboBox.addItem("disable", "disable")
        self.parameters_ssl_comboBox.addItem("allow", "allow")
        self.parameters_ssl_comboBox.addItem("prefer", "prefer")
        self.parameters_ssl_comboBox.addItem("require", "require")
        self.parameters_ssl_comboBox.addItem("verify-ca", "verify-ca")
        self.parameters_ssl_comboBox.addItem("verify-full", "verify-full")

        self.database_lineEdit.textChanged.connect(self._databaseTextChanged)

        self.buttonBox.accepted.connect(self._accept)

        self._serviceChanged()

    def created_service_name(self):
        return self.service_lineEdit.text()

    def _serviceChanged(self):
        service_name = self.existingService_comboBox.currentText()
        service_config = pgserviceparser.service_config(service_name)

        service_host = service_config.get("host", None)
        service_port = service_config.get("port", None)
        service_ssl = service_config.get("sslmode", None)
        service_dbname = service_config.get("dbname", None)
        service_user = service_config.get("user", None)
        service_password = service_config.get("password", None)

        self.parameters_host_lineEdit.setText(service_host)
        self.parameters_port_lineEdit.setText(service_port)

        parameter_ssl_index = self.parameters_ssl_comboBox.findData(service_ssl)
        self.parameters_ssl_comboBox.setCurrentIndex(parameter_ssl_index)
        self.parameters_user_lineEdit.setText(service_user)
        self.parameters_password_lineEdit.setText(service_password)

        self.database_lineEdit.setText(service_dbname)

    def _enterManuallyToggled(self, checked):
        self.parameters_frame.setEnabled(checked)

    def _databaseTextChanged(self, text):
        self.database_label.setText(text)

    def _accept(self):
        service_name = self.created_service_name()

        if service_name == "":
            QMessageBox.critical(self, "Error", "Please enter a service name.")
            return

        # Check if the service name is already in use
        if service_name in pgserviceparser.service_names():
            QMessageBox.critical(self, "Error", self.tr(f"Service name '{service_name}' already exists."))
            return
        
        if self.database_lineEdit.text() == "":
            QMessageBox.critical(self, "Error", "Please enter a database name.")
            return

        service_settings = self._get_service_settings()
        
        pgserviceparser.write_service(service_name=service_name, settings=
            {
                "host": self.parameters_host_lineEdit.text(),
                "port": self.parameters_port_lineEdit.text(),
                "sslmode": self.parameters_ssl_comboBox.currentText(),
                "dbname": self.database_lineEdit.text(),
                "user": self.parameters_user_lineEdit.text(),
                "password": self.parameters_password_lineEdit.text(),
            },
            create_if_not_found=True,
        )

        super().accept()

    def _get_service_settings(self):

        settings = dict()

        if self.enterManually_radioButton.isChecked():
            if self.parameters_host_lineEdit.text():
                settings["host"] = self.parameters_host_lineEdit.text()

            if self.parameters_port_lineEdit.text():
                settings["port"] = self.parameters_port_lineEdit.text()
            
            if self.parameters_ssl_comboBox.currentData():
                settings["sslmode"] = self.parameters_ssl_comboBox.currentData()

            if self.parameters_user_lineEdit.text():
                settings["user"] = self.parameters_user_lineEdit.text()

            if self.parameters_password_lineEdit.text():
                settings["password"] = self.parameters_password_lineEdit.text()

        return settings
