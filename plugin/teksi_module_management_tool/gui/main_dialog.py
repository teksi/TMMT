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
from teksi_module_management_tool.utils.database_utils import DatabaseUtils
from teksi_module_management_tool.libs import pgserviceparser
from teksi_module_management_tool.gui.database_create_dialog import DataBaseCreateDialog

DIALOG_UI = PluginUtils.get_ui_class("main_dialog.ui")


class MainDialog(QDialog, DIALOG_UI):
    def __init__(self, modules_registry, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.close_pushButton.clicked.connect(self.accept)

        self._modules_registry = modules_registry
        self._current_module = None

        self._database_connection = None

        # Init GUI Modules
        self.module_module_comboBox.clear()
        self.module_module_comboBox.addItem(self.tr("Plese select a module"), None)
        for module in self._modules_registry.modules():
            self.module_module_comboBox.addItem(module.name, module)

        self.module_module_comboBox.currentIndexChanged.connect(self._moduleChanged)

        self.module_latestVersion_label.setText("")
        module_latestVersion_label_palette = self.module_latestVersion_label.palette()
        module_latestVersion_label_palette.setColor(
            self.module_latestVersion_label.foregroundRole(), QColor(12, 167, 137)
        )
        self.module_latestVersion_label.setPalette(module_latestVersion_label_palette)

        self.module_version_comboBox.clear()

        self.module_seeChangeLog_pushButton.clicked.connect(self._seeChangeLogClicked)

        # Init GUI Database
        self._loadDatabaseInformations()
        self.db_services_comboBox.currentIndexChanged.connect(self._serviceChanged)
        self._serviceChanged()

        self.db_create_button.clicked.connect(self._createDatabaseClicked)

    def _loadDatabaseInformations(self):
        self.db_servicesConfigFilePath_label.setText(pgserviceparser.conf_path().as_posix())

        self.db_services_comboBox.clear()
        for service_name in pgserviceparser.service_names():
            self.db_services_comboBox.addItem(service_name)

    def _moduleChanged(self, index):
        if self.module_module_comboBox.currentData() == self._current_module:
            return

        self._current_module = self.module_module_comboBox.currentData()

        self.module_latestVersion_label.setText("")
        self.module_version_comboBox.clear()

        if self._current_module is None:
            return

        with OverrideCursor(Qt.WaitCursor):
            if self._current_module.versions == list():
                self._current_module.load_versions()

            for module_version in self._current_module.versions:
                self.module_version_comboBox.addItem(module_version.display_name(), module_version)

            if self._current_module.latest_version is not None:
                self.module_latestVersion_label.setText(
                    f"Latest: {self._current_module.latest_version.name}"
                )

    def _seeChangeLogClicked(self):
        current_module_version = self.module_version_comboBox.currentData()

        if current_module_version is None:
            QMessageBox.warning(
                self,
                self.tr("Can't open changelog"),
                self.tr("Please select a module and version first."),
            )
            return

        QDesktopServices.openUrl(QUrl(current_module_version.html_url))

    def _serviceChanged(self, index=None):
        if self.db_services_comboBox.currentText() == "":
            self.db_database_label.setText(self.tr("No database"))
            font = self.db_database_label.font()
            font.setItalic(True)
            self.db_database_label.setFont(font)
            return
        
        service_name = self.db_services_comboBox.currentText()
        service_config = pgserviceparser.service_config(service_name)

        service_database = service_config.get("dbname", None)
        
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

        self._database_connection = DatabaseUtils.PsycopgConnection(service=service_name)

    def _createDatabaseClicked(self):
        databaseCreateDialog = DataBaseCreateDialog(selected_service=self.db_services_comboBox.currentText(), parent=self)
        
        if databaseCreateDialog.exec_() == QDialog.Rejected:
            return
        
        self._loadDatabaseInformations()

        # Select the created service
        created_service_name = databaseCreateDialog.created_service_name()
        self.db_services_comboBox.setCurrentText(created_service_name)

