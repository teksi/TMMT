"""
/***************************************************************************
 Plugin Utils
                              -------------------
        begin                : 28.4.2018
        copyright            : (C) 2018 by OPENGIS.ch
        email                : matthias@opengis.ch
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.uic import loadUiType


class PluginUtils:

    PLUGIN_NAME = "TEKSI Module Management Tool (TMMT)"

    @staticmethod
    def plugin_root_path():
        """
        Returns the root path of the plugin
        """
        return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

    @staticmethod
    def get_plugin_icon_path(icon_filename):
        return os.path.join(PluginUtils.plugin_root_path(), "icons", icon_filename)

    @staticmethod
    def get_plugin_icon(icon_filename):
        return QIcon(PluginUtils.get_plugin_icon_path(icon_filename=icon_filename))

    @staticmethod
    def get_ui_class(ui_file):
        """Get UI Python class from .ui file.
           Can be filename.ui or subdirectory/filename.ui
        :param ui_file: The file of the ui in svir.ui
        :type ui_file: str
        """
        os.path.sep.join(ui_file.split("/"))
        ui_file_path = os.path.abspath(os.path.join(PluginUtils.plugin_root_path(), "ui", ui_file))
        return loadUiType(ui_file_path)[0]
    
    @staticmethod
    def get_metadata_file_path():
        return os.path.join(PluginUtils.plugin_root_path(), "metadata.txt")

    @staticmethod
    def get_plugin_version():
        ini_text = QSettings(PluginUtils.get_metadata_file_path(), QSettings.IniFormat)
        version = ini_text.value("version")
