# -----------------------------------------------------------
#
# Profile
# Copyright (C) 2012  Patrice Verchere
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


from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtWidgets import QDialog

from teksi_module_management_tool.utils.plugin_utils import PluginUtils

DIALOG_UI = PluginUtils.get_ui_class("about_dialog.ui")


class AboutDialog(QDialog, DIALOG_UI):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        metadata_file_path = PluginUtils.get_metadata_file_path()

        ini_text = QSettings(metadata_file_path, QSettings.IniFormat)
        version = ini_text.value("version")
        name = ini_text.value("name")
        description = "".join(ini_text.value("description"))
        about = " ".join(ini_text.value("about"))
        qgisMinimumVersion = ini_text.value("qgisMinimumVersion")

        self.setWindowTitle(f"{name} - {version}")
        self.titleLabel.setText(self.windowTitle())
        self.descriptionLabel.setText(description)
        self.aboutLabel.setText(about)
        self.qgisMinimumVersionLabel.setText(qgisMinimumVersion)

        self.iconLabel.setPixmap(QPixmap(PluginUtils.get_plugin_icon_path("tmmt-logo.png")))
