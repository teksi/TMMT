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
from qgis.PyQt.QtWidgets import QAction, QDialog, QFileDialog, QMenu, QMessageBox
from teksi_module_management_tool.gui.database_create_dialog import DatabaseCreateDialog
from teksi_module_management_tool.gui.database_duplicate_dialog import (
    DatabaseDuplicateDialog,
)
from teksi_module_management_tool.core.package_prepare_task import PackagePrepareTask
from teksi_module_management_tool.libs import pgserviceparser
from teksi_module_management_tool.libs.pum.config import PumConfig
from teksi_module_management_tool.libs.pum.schema_migrations import SchemaMigrations
from teksi_module_management_tool.libs.pum.upgrader import Upgrader
from teksi_module_management_tool.utils.plugin_utils import PluginUtils
from teksi_module_management_tool.utils.qt_utils import OverrideCursor, QtUtils


DIALOG_UI = PluginUtils.get_ui_class("main_dialog.ui")


class MainDialog(QDialog, DIALOG_UI):

    MODULE_VERSION_SPECIAL_LOAD_FROM_ZIP = "Load from ZIP"
    MODULE_VERSION_SPECIAL_LOAD_DEVELOPMENT = "Load development versions"

    COLOR_GREEN = QColor(12, 167, 137)
    COLOR_WARNING = QColor(255, 165, 0)

    def __init__(self, modules_registry, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.buttonBox.rejected.connect(self.accept)
        self.buttonBox.helpRequested.connect(self.__helpRequested)

        self.__modules_registry = modules_registry
        self.__current_module = None

        self.__database_connection = None

        self.__pum_config = None
        self.__data_model_dir = None

        # Init GUI Modules
        self.__initGuiModules()

        # Init GUI Database
        self.__initGuiDatabase()

        # Init GUI Module Info
        self.__initGuiModuleInfo()

        self.__packagePrepareTask = PackagePrepareTask(self)
        self.__packagePrepareTask.finished.connect(self.__packagePrepareTaskFinished)
        self.__packagePrepareTask.signalPackagingProgress.connect(self.__packagePrepareTaskProgress)

    def __helpRequested(self):
        QDesktopServices.openUrl(QUrl("https://github.com/teksi/TMMT"))

    def __initGuiModules(self):
        self.module_module_comboBox.clear()
        self.module_module_comboBox.addItem(self.tr("Please select a module"), None)
        for module in self.__modules_registry.modules():
            self.module_module_comboBox.addItem(module.name, module)

        self.module_latestVersion_label.setText("")
        QtUtils.setForegroundColor(
            self.module_latestVersion_label, self.COLOR_GREEN
        )

        self.module_version_comboBox.clear()
        self.module_version_comboBox.addItem(self.tr("Please select a version"), None)

        self.module_zipPackage_groupBox.setVisible(False)

        self.module_module_comboBox.currentIndexChanged.connect(self.__moduleChanged)
        self.module_version_comboBox.currentIndexChanged.connect(self.__moduleVersionChanged)
        self.module_seeChangeLog_pushButton.clicked.connect(self.__seeChangeLogClicked)
        self.module_browseZip_toolButton.clicked.connect(self.__moduleBrowseZipClicked)

    def __initGuiDatabase(self):
        self.db_database_label.setText(self.tr("No database"))
        QtUtils.setForegroundColor(self.db_database_label, self.COLOR_WARNING)
        QtUtils.setFontItalic(self.db_database_label, True)

        self.__loadDatabaseInformations()
        self.db_services_comboBox.currentIndexChanged.connect(self.__serviceChanged)

        db_operations_menu = QMenu(self.db_operations_toolButton)

        actionCreateDb = QAction(self.tr("Create database"), db_operations_menu)
        self.__actionDuplicateDb = QAction(self.tr("Duplicate database"), db_operations_menu)
        actionCreateAndGrantRoles = QAction(self.tr("Create and grant roles"), db_operations_menu)

        actionCreateDb.triggered.connect(self.__createDatabaseClicked)
        self.__actionDuplicateDb.triggered.connect(self.__duplicateDatabaseClicked)
        actionCreateAndGrantRoles.triggered.connect(self.__createAndGrantRolesClicked)

        db_operations_menu.addAction(actionCreateDb)
        db_operations_menu.addAction(self.__actionDuplicateDb)
        db_operations_menu.addAction(actionCreateAndGrantRoles)

        self.db_operations_toolButton.setMenu(db_operations_menu)

    def __initGuiModuleInfo(self):
        QtUtils.setForegroundColor(self.moduleInfo_NoModuleFound_label, self.COLOR_WARNING)
        QtUtils.setFontItalic(self.moduleInfo_NoModuleFound_label, True)

        self.moduleInfo_stackedWidget.setCurrentWidget(self.moduleInfo_stackedWidget_pageInstall)

        self.moduleInfo_install_pushButton.clicked.connect(self.__installModuleClicked)
        self.moduleInfo_upgrade_pushButton.clicked.connect(self.__upgradeModuleClicked)

    def __loadDatabaseInformations(self):
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

    def __moduleChanged(self, index):
        if self.module_module_comboBox.currentData() == self.__current_module:
            return

        self.__current_module = self.module_module_comboBox.currentData()

        self.module_latestVersion_label.setText("")
        self.module_version_comboBox.clear()
        self.module_version_comboBox.addItem(self.tr("Please select a version"), None)

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
        self.module_version_comboBox.addItem(
            self.tr("Load from ZIP file"), self.MODULE_VERSION_SPECIAL_LOAD_FROM_ZIP
        )

        self.module_version_comboBox.insertSeparator(self.module_version_comboBox.count())
        self.module_version_comboBox.addItem(
            self.tr("Load additional branches"), self.MODULE_VERSION_SPECIAL_LOAD_DEVELOPMENT
        )

    def __moduleVersionChanged(self, index):

        if self.module_version_comboBox.currentData() == self.MODULE_VERSION_SPECIAL_LOAD_FROM_ZIP:
            self.module_zipPackage_groupBox.setVisible(True)
            return
        else:
            self.module_zipPackage_groupBox.setVisible(False)

        if (
            self.module_version_comboBox.currentData()
            == self.MODULE_VERSION_SPECIAL_LOAD_DEVELOPMENT
        ):
            self.__loadDevelopmentVersions()
            return

        current_module_version = self.module_version_comboBox.currentData()
        if current_module_version is None:
            return
        
        self.__pum_config = None
        self.__data_model_dir = None

        if self.__packagePrepareTask.isRunning():
            self.__packagePrepareTask.cancel()
            self.__packagePrepareTask.wait()

        self.__packagePrepareTask.startFromModuleVersion(current_module_version)

    def __loadDevelopmentVersions(self):
        if self.__current_module is None:
            return

        with OverrideCursor(Qt.WaitCursor):
            self.__current_module.load_development_versions()

        if self.__current_module.development_versions == list():
            QMessageBox.warning(
                self,
                self.tr("No development versions found"),
                self.tr("No development versions found for this module."),
            )
            return

        self.module_version_comboBox.removeItem(self.module_version_comboBox.count() - 1)

        for module_version in self.__current_module.development_versions:
            self.module_version_comboBox.addItem(module_version.display_name(), module_version)

    def __moduleBrowseZipClicked(self):
        filename, format = QFileDialog.getOpenFileName(
            self, self.tr("Open from zip"), None, self.tr("Zip package (*.zip)")
        )

        if filename == "":
            return

        self.module_fromZip_lineEdit.setText(filename)

        try:
            with OverrideCursor(Qt.WaitCursor):
                self.__loadModuleFromZip(filename)
        except Exception as exception:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr(f"Can't load module from zip file:\n{exception}"),
            )
            return

    def __loadModuleFromZip(self, filename):

        self.__pum_config = None
        self.__data_model_dir = None

        if self.__packagePrepareTask.isRunning():
            self.__packagePrepareTask.cancel()
            self.__packagePrepareTask.wait()

        self.__packagePrepareTask.startFromZip(filename)

    def __packagePrepareTaskFinished(self):

        if self.__packagePrepareTask.lastError is not None:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr(f"Can't load module package:\n{self.__packagePrepareTask.lastError}"),
            )
            return

        self.__data_model_dir = os.path.join(self.__packagePrepareTask.package_dir, "datamodel")
        pumConfigFilename = os.path.join(self.__data_model_dir, ".pum.yaml")
        if not os.path.exists(pumConfigFilename):
            raise Exception(
                self.tr(
                    f"The selected file '{self.__packagePrepareTask.zip_file}' does not contain a valid .pum.yaml file."
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
            self.db_upgrade_pushButton.setText(self.tr(f"Upgrade to {migrationVersion}"))

            self.moduleInfo_stackedWidget.setCurrentWidget(self.moduleInfo_stackedWidget_pageUpgrade)
        else:
            self.db_moduleInfo_label.setText(self.tr("No module found"))
            self.db_install_pushButton.setText(self.tr(f"Install {migrationVersion}"))
            self.moduleInfo_stackedWidget.setCurrentWidget(self.moduleInfo_stackedWidget_pageInstall)

    def __packagePrepareTaskProgress(self, progress):
        print(f"Progress: {progress}")

    def __seeChangeLogClicked(self):
        current_module_version = self.module_version_comboBox.currentData()

        if current_module_version == self.MODULE_VERSION_SPECIAL_LOAD_FROM_ZIP:
            QMessageBox.warning(
                self,
                self.tr("Can't open changelog"),
                self.tr("Changelog is not available for Zip packages."),
            )
            return

        if current_module_version is None:
            QMessageBox.warning(
                self,
                self.tr("Can't open changelog"),
                self.tr("Please select a module and version first."),
            )
            return

        if current_module_version.html_url is None:
            QMessageBox.warning(
                self,
                self.tr("Can't open changelog"),
                self.tr(f"Changelog not available for version '{current_module_version.name}'."),
            )
            return

        QDesktopServices.openUrl(QUrl(current_module_version.html_url))

    def __serviceChanged(self, index=None):
        if self.db_services_comboBox.currentText() == "":
            self.db_database_label.setText(self.tr("No database"))
            QtUtils.setForegroundColor(self.db_database_label, self.COLOR_WARNING)
            QtUtils.setFontItalic(self.db_database_label, True)

            self.__actionDuplicateDb.setDisabled(True)
            return

        service_name = self.db_services_comboBox.currentText()
        service_config = pgserviceparser.service_config(service_name)

        service_database = service_config.get("dbname", None)

        if service_database is None:
            self.db_database_label.setText(self.tr("No database provided by the service"))
            QtUtils.setForegroundColor(self.db_database_label, self.COLOR_WARNING)
            QtUtils.setFontItalic(self.db_database_label, True)

            self.__actionDuplicateDb.setDisabled(True)
            return

        self.db_database_label.setText(service_database)
        QtUtils.resetForegroundColor(self.db_database_label)
        QtUtils.setFontItalic(self.db_database_label, False)

        self.__actionDuplicateDb.setEnabled(True)

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

    def __createDatabaseClicked(self):
        databaseCreateDialog = DatabaseCreateDialog(
            selected_service=self.db_services_comboBox.currentText(), parent=self
        )

        if databaseCreateDialog.exec_() == QDialog.Rejected:
            return

        self.__loadDatabaseInformations()

        # Select the created service
        created_service_name = databaseCreateDialog.created_service_name()
        self.db_services_comboBox.setCurrentText(created_service_name)

    def __duplicateDatabaseClicked(self):
        databaseDuplicateDialog = DatabaseDuplicateDialog(
            selected_service=self.db_services_comboBox.currentText(), parent=self
        )
        if databaseDuplicateDialog.exec_() == QDialog.Rejected:
            return

    def __installModuleClicked(self):

        if self.__current_module is None:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("Please select a module first."),
            )
            return
        
        current_module_version = self.module_version_comboBox.currentData()
        if current_module_version is None:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("Please select a module version first."),
            )
            return

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
            upgrader = Upgrader(
                pg_service=service_name,
                config=self.__pum_config,
                dir=self.__data_model_dir,
                parameters={"SRID": srid},
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

    def __upgradeModuleClicked(self):
        if self.__current_module is None:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("Please select a module first."),
            )
            return
        
        current_module_version = self.module_version_comboBox.currentData()
        if current_module_version is None:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("Please select a module version first."),
            )
            return

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
        
        raise NotImplementedError("Upgrade module is not implemented yet")

    def __createAndGrantRolesClicked(self):

        if self.__pum_config is None:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("No valid module available."),
            )
            return
        
        raise NotImplementedError("Create and grant roles is not implemented yet")
