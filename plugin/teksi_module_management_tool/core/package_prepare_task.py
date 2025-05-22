import os
import shutil
import zipfile
import logging

import requests
from qgis.PyQt.QtCore import QFileInfo, QThread, pyqtSignal
from teksi_module_management_tool.utils.plugin_utils import PluginUtils


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
                self.__download_module_version(self.module_version)

            self.__extract_zip_file(self.zip_file)

        except Exception as e:
            # Handle any exceptions that occur during processing
            print(f"Erorr: {e}")
            self.lastError = e

    def __download_module_version(self, module_version):

        url = module_version.download_url
        filename = module_version.name + ".zip"

        temp_dir = PluginUtils.plugin_temp_path()
        destination_directory = os.path.join(temp_dir, "Downloads")
        os.makedirs(destination_directory, exist_ok=True)

        self.zip_file = os.path.join(destination_directory, filename)

        # Streaming, so we can iterate over the response.
        response = requests.get(url, allow_redirects=True, stream=True)

        # Raise an exception in case of http errors
        response.raise_for_status()

        self.__checkForCanceled()

        
        logging.info(f"Downloading from '{url}' to '{self.zip_file}'")
        data_size = 0
        with open(self.zip_file, "wb") as file:
            for data in response.iter_content(chunk_size=None):

                self.__checkForCanceled()

                data_size += len(data)
                # print(f"Recived '{data_size}' bytes")
                # self.signalPackagingProgress.emit(data_size)

                file.write(data)

    def __extract_zip_file(self, zip_file):
        temp_dir = PluginUtils.plugin_temp_path()
        self.package_dir = os.path.join(temp_dir, QFileInfo(zip_file).baseName())
        if os.path.exists(self.package_dir):
            shutil.rmtree(self.package_dir)

        logging.info(f"Extracting package '{zip_file}' to '{self.package_dir}'")

        # Unzip the file to plugin temp dir
        try:
            with zipfile.ZipFile(zip_file, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
        except zipfile.BadZipFile:
            raise Exception(self.tr(f"The selected file '{zip_file}' is not a valid zip archive."))

    def __checkForCanceled(self):
        """
        Check if the task has been canceled.
        """
        if self.__canceled:
            raise Exception(self.tr("The task has been canceled."))
