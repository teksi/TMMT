
import os
import shutil
import zipfile
import requests

from qgis.PyQt.QtCore import QFileInfo, Qt, QUrl, QThread, pyqtSignal
from qgis.PyQt.QtGui import QColor, QDesktopServices
from qgis.PyQt.QtWidgets import QAction, QDialog, QFileDialog, QMenu, QMessageBox
from teksi_module_management_tool.gui.database_create_dialog import DatabaseCreateDialog
from teksi_module_management_tool.gui.database_duplicate_dialog import (
    DatabaseDuplicateDialog,
)
from teksi_module_management_tool.libs import pgserviceparser
from teksi_module_management_tool.libs.pum.config import PumConfig
from teksi_module_management_tool.libs.pum.schema_migrations import SchemaMigrations
from teksi_module_management_tool.libs.pum.upgrader import Upgrader
from teksi_module_management_tool.utils.plugin_utils import PluginUtils
from teksi_module_management_tool.utils.qt_utils import OverrideCursor, QtUtils


class PackagePrepareTask(QThread):
    """
    This class is responsible for preparing the package for the Teksi module management tool.
    It inherits from QThread to run the preparation process in a separate thread.
    """

    signalPackagingProgress = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.zip_file = None
        self.module_version = None

        self.package_dir = None

        self.__canceled = False
        self.lastError = None

    def startFromZip(self, zip_file: str):

        self.zip_file = zip_file
        self.module_version = None

        self.package_dir = None

        self.__canceled = False
        self.lastError = None
        self.start()

    def startFromModuleVersion(self, module_version):
        self.zip_file = None
        self.module_version = module_version
        
        self.package_dir = None

        self.__canceled = False
        self.lastError = None
        self.start()

    def cancel(self):
        self.__canceled = True

    def run(self):
        """
        The main method that runs when the thread starts.
        """

        try:    
            if self.module_version is not None:
                self.zip_file = self.__download_module_version(self.module_version)

            self.__extract_zip_file(self.zip_file)

        except Exception as e:
            # Handle any exceptions that occur during processing
            print(f"Erorr: {e}")
            self.lastError = e

    def __download_module_version(self, module_version):
             
        url = module_version.download_url
        filename = module_version.name + ".zip"
        
        temp_dir = PluginUtils.plugin_temp_path()

        self.zip_file = os.path.join(temp_dir, "Downloads", filename)
        if os.path.exists(self.zip_file):
            shutil.rmtree(self.zip_file)

        # Streaming, so we can iterate over the response.
        response = requests.get(url, stream=True)

        self.__checkForCanceled()
        
        # Sizes in bytes.
        total_size = int(response.headers.get("content-length", 0))
        block_size = 1024
        data_size = 0
        
        with open(self.zip_file, "wb") as file:
            for data in response.iter_content(block_size):
                self.__checkForCanceled()

                data_size += len(data)
                self.signalPackagingProgress.emit(data_size / total_size)
                
                file.write(data)
        
        if total_size != data_size:
            raise RuntimeError(f"Could not download package from '{url}'")

    def __extract_zip_file(self, zip_file):
        temp_dir = PluginUtils.plugin_temp_path()

        self.package_dir = os.path.join(temp_dir, QFileInfo(filename).baseName())
        if os.path.exists(self.package_dir):
            shutil.rmtree(self.package_dir)

        # Unzip the file to plugin temp dir
        try:
            with zipfile.ZipFile(filename, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
        except zipfile.BadZipFile:
            raise Exception(self.tr(f"The selected file '{filename}' is not a valid zip archive."))


    def __checkForCanceled(self):
        """
        Check if the task has been canceled.
        """
        if self.__canceled:
            raise Exception(self.tr("The task has been canceled."))
