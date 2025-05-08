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

import os
import shutil
import zipfile
import psycopg

from qgis.PyQt.QtCore import QFileInfo, Qt, QUrl
from qgis.PyQt.QtGui import QColor, QDesktopServices
from qgis.PyQt.QtWidgets import QDialog, QFileDialog, QMessageBox
from teksi_module_management_tool.gui.database_create_dialog import DatabaseCreateDialog
from teksi_module_management_tool.gui.database_duplicate_dialog import (
    DatabaseDuplicateDialog,
)
from teksi_module_management_tool.libs import pgserviceparser
from teksi_module_management_tool.libs.pum.config import PumConfig
from teksi_module_management_tool.libs.pum.schema_migrations import SchemaMigrations
from teksi_module_management_tool.libs.pum.upgrader import Upgrader
from teksi_module_management_tool.utils.plugin_utils import PluginUtils
from teksi_module_management_tool.utils.qt_utils import OverrideCursor

DIALOG_UI = PluginUtils.get_ui_class("main_dialog.ui")


class MainDialog(QDialog, DIALOG_UI):

    MODULE_VERSION_SPECIAL_LOAD_BRANCHES = "Load branches"

    def __init__(self, modules_registry, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.close_pushButton.clicked.connect(self.accept)

        self.__modules_registry = modules_registry
        self.__current_module = None

        self.__database_connection = None

        self.__pum_config = None
        self.__data_model_dir = None

        # Init GUI Modules
        self.module_module_comboBox.clear()
        self.module_module_comboBox.addItem(self.tr("Plese select a module"), None)
        for module in self.__modules_registry.modules():
            self.module_module_comboBox.addItem(module.name, module)

        self.module_module_comboBox.currentIndexChanged.connect(self._moduleChanged)

        self.module_latestVersion_label.setText("")
        module_latestVersion_label_palette = self.module_latestVersion_label.palette()
        module_latestVersion_label_palette.setColor(
            self.module_latestVersion_label.foregroundRole(), QColor(12, 167, 137)
        )
        self.module_latestVersion_label.setPalette(module_latestVersion_label_palette)

        self.module_version_comboBox.clear()
        self.module_version_comboBox.currentIndexChanged.connect(self._moduleVersionChanged)

        self.module_seeChangeLog_pushButton.clicked.connect(self._seeChangeLogClicked)

        self.module_browseZip_toolButton.clicked.connect(self._moduleBrowseZipClicked)

        # Init GUI Database
        self._loadDatabaseInformations()
        self.db_services_comboBox.currentIndexChanged.connect(self._serviceChanged)
        self._serviceChanged()

        self.db_create_button.clicked.connect(self._createDatabaseClicked)
        self.db_duplicate_button.clicked.connect(self._duplicateDatabaseClicked)

        self.db_install_pushButton.setDisabled(True)
        self.db_install_pushButton.clicked.connect(self._installModuleClicked)

        self.db_createAndGrantRoles_pushButton.clicked.connect(self._createAndGrantRolesClicked)

    def _loadDatabaseInformations(self):
        self.db_servicesConfigFilePath_label.setText(pgserviceparser.conf_path().as_posix())

        self.db_services_comboBox.clear()

        try:
            for service_name in pgserviceparser.service_names():
                self.db_services_comboBox.addItem(service_name)
        except Exception as exception:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr(f"Can't load database services:\n{exception}"),
            )
            return

    def _moduleChanged(self, index):
        if self.module_module_comboBox.currentData() == self.__current_module:
            return

        self.__current_module = self.module_module_comboBox.currentData()

        self.module_latestVersion_label.setText("")
        self.module_version_comboBox.clear()

        if self.__current_module is None:
            return

        with OverrideCursor(Qt.WaitCursor):
            if self.__current_module.versions == list():
                self.__current_module.load_versions()

            for module_version in self.__current_module.versions:
                self.module_version_comboBox.addItem(module_version.display_name(), module_version)

            if self.__current_module.latest_version is not None:
                self.module_latestVersion_label.setText(
                    f"Latest: {self.__current_module.latest_version.name}"
                )

        self.module_version_comboBox.insertSeparator(self.module_version_comboBox.count())
        self.module_version_comboBox.addItem(self.tr("Load additional branches"), self.MODULE_VERSION_SPECIAL_LOAD_BRANCHES)

    def _moduleVersionChanged(self, index):
        if self.module_version_comboBox.currentData() == self.MODULE_VERSION_SPECIAL_LOAD_BRANCHES:
            self._loadAdditionalVersionsFromBranches()
            return

        current_module_version = self.module_version_comboBox.currentData()

        if current_module_version is None:
            return

        if current_module_version == self.__current_module.latest_version:
            self.module_seeChangeLog_pushButton.setEnabled(True)
        else:
            self.module_seeChangeLog_pushButton.setEnabled(False)

        # Load module from zip
        if current_module_version.zip_url is not None:
            self.module_fromZip_lineEdit.setText(current_module_version.zip_url)
            self.module_fromZip_lineEdit.setEnabled(True)
            self.module_browseZip_toolButton.setEnabled(True)
        else:
            self.module_fromZip_lineEdit.setText("")
            self.module_fromZip_lineEdit.setEnabled(False)
            self.module_browseZip_toolButton.setEnabled(False)

    def _loadAdditionalVersionsFromBranches(self):
        if self.__current_module is None:
            return

        with OverrideCursor(Qt.WaitCursor):
            self.__current_module.load_branch_versions()

        if self.__current_module.branch_versions == list():
            QMessageBox.warning(
                self,
                self.tr("No branches found"),
                self.tr("No branches found for this module."),
            )
            return
        
        self.module_version_comboBox.removeItem(self.module_version_comboBox.count() - 1)

        for module_version in self.__current_module.branch_versions:
            self.module_version_comboBox.addItem(module_version.display_name(), module_version)

    def _moduleBrowseZipClicked(self):
        filename, format = QFileDialog.getOpenFileName(
            self, self.tr("Open from zip"), None, self.tr("Zip package (*.zip)")
        )

        if filename == "":
            return

        self.module_fromZip_lineEdit.setText(filename)

        try:
            with OverrideCursor(Qt.WaitCursor):
                self._loadModuleFromZip(filename)
        except Exception as exception:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr(f"Can't load module from zip file:\n{exception}"),
            )
            return

    def _loadModuleFromZip(self, filename):

        self.__pum_config = None
        self.__data_model_dir = None
        self.db_install_pushButton.setDisabled(True)

        temp_dir = PluginUtils.plugin_temp_path()

        package_dir = os.path.join(temp_dir, QFileInfo(filename).baseName())
        if os.path.exists(package_dir):
            shutil.rmtree(package_dir)

        # Unzip the file to plugin temp dir
        try:
            with zipfile.ZipFile(filename, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
        except zipfile.BadZipFile:
            raise Exception(self.tr(f"The selected file '{filename}' is not a valid zip archive."))

        self.__data_model_dir = os.path.join(package_dir, "datamodel")
        pumConfigFilename = os.path.join(self.__data_model_dir, ".pum-config.yaml")
        if not os.path.exists(pumConfigFilename):
            raise Exception(
                self.tr(
                    f"The selected file '{filename}' does not contain a valid .pum-config.yaml file."
                )
            )

        self.__pum_config = PumConfig.from_yaml(pumConfigFilename)

        for parameter in self.__pum_config.parameters():
            parameter_name = parameter.get("name", None)
            if parameter_name is None:
                continue

            if parameter_name == "SRID":
                default_srid = parameter.get("default", None)
                if default_srid is not None:
                    self.db_parameters_CRS_lineEdit.setText("")
                    self.db_parameters_CRS_lineEdit.setPlaceholderText(str(default_srid))

        sm = SchemaMigrations(self.__pum_config)
        migrationVersion = "0.0.0"
        if sm.exists(self.__database_connection):
            baseline_version = sm.baseline(self.__database_connection)
            self.db_moduleInfo_label.setText(self.tr(f"Version {baseline_version} found"))
            self.db_install_pushButton.setText(self.tr(f"Upgrade to {migrationVersion}"))
        else:
            self.db_moduleInfo_label.setText(self.tr("No module found"))
            self.db_install_pushButton.setText(self.tr(f"Install {migrationVersion}"))

        self.db_install_pushButton.setEnabled(True)
        

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

            self.db_duplicate_button.setDisabled(True)
            return

        service_name = self.db_services_comboBox.currentText()
        service_config = pgserviceparser.service_config(service_name)

        service_database = service_config.get("dbname", None)

        if service_database is None:
            self.db_database_label.setText(self.tr("No database provided by the service"))
            font = self.db_database_label.font()
            font.setItalic(True)
            self.db_database_label.setFont(font)

            self.db_duplicate_button.setDisabled(True)
            return

        self.db_database_label.setText(service_database)
        font = self.db_database_label.font()
        font.setItalic(False)
        self.db_database_label.setFont(font)

        self.db_duplicate_button.setEnabled(True)

        # Try getting existing module
        try:
            self.__database_connection = psycopg.connect(service=service_name)

        except Exception as exception:
            self.__database_connection = None

            QMessageBox.warning(
                self,
                self.tr("Can't connect to service"),
                self.tr(f"Can't connect to service '{service_name}':\n{exception}."),
            )

            return

        self.__database_connection.cursor().execute("SELECT current_database()")

    def _createDatabaseClicked(self):
        databaseCreateDialog = DatabaseCreateDialog(
            selected_service=self.db_services_comboBox.currentText(), parent=self
        )

        if databaseCreateDialog.exec_() == QDialog.Rejected:
            return

        self._loadDatabaseInformations()

        # Select the created service
        created_service_name = databaseCreateDialog.created_service_name()
        self.db_services_comboBox.setCurrentText(created_service_name)

    def _duplicateDatabaseClicked(self):
        databaseDuplicateDialog = DatabaseDuplicateDialog(
            selected_service=self.db_services_comboBox.currentText(), parent=self
        )
        if databaseDuplicateDialog.exec_() == QDialog.Rejected:
            return

    def _installModuleClicked(self):

        if self.__database_connection is None:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("Please select a database service first."),
            )
            return

        if self.__pum_config is None:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("No valid module available."),
            )
            return

        srid_string = self.db_parameters_CRS_lineEdit.text()
        if srid_string == "":
            srid_string = self.db_parameters_CRS_lineEdit.placeholderText()

        if srid_string == "":
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("Please provide a valid SRID."),
            )
            return
        
        srid = int(srid_string)

        try:
            service_name = self.db_services_comboBox.currentText()
            upgrader = Upgrader(pg_service=service_name,
                                config=self.__pum_config,
                                dir=self.__data_model_dir,
                                parameters={"SRID": srid}
                       )
            with OverrideCursor(Qt.WaitCursor):
                upgrader.install()
        except Exception as exception:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr(f"Can't install/upgrade module:\n{exception}"),
            )
            return
            
    def _createAndGrantRolesClicked(self):

        if self.__pum_config is None:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("No valid module available."),
            )
            return

        with OverrideCursor(Qt.WaitCursor):
            try:
                service_name = self.db_services_comboBox.currentText()
                upgrader = Upgrader(pg_service=service_name,
                                    config=self.__pum_config,
                                    dir=self.__data_model_dir,
                                    parameters={"SRID": 2056}
                           )
                upgrader.create_and_grant_roles()
            except Exception as exception:
                QMessageBox.critical(
                    self,
                    self.tr("Error"),
                    self.tr(f"Can't create and grant roles:\n{exception}"),
                )
                return