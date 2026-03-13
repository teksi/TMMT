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



import os

from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtGui import QFont, QPixmap
from qgis.PyQt.QtWidgets import QDialog, QLabel

from teksi_module_management_tool.utils.tmmt_plugin_utils import TMMTPluginUtils

DIALOG_UI = TMMTPluginUtils.get_ui_class("about_dialog.ui")


class AboutDialog(QDialog, DIALOG_UI):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        metadata_file_path = TMMTPluginUtils.get_metadata_file_path()

        ini_text = QSettings(metadata_file_path, QSettings.Format.IniFormat)
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

        self.iconLabel.setPixmap(QPixmap(TMMTPluginUtils.get_plugin_icon_path("tmmt-logo.png")))

        # --- Library versions ---
        from ..libs.oqtopus.gui.about_dialog import (
            _dist_info_version,
            get_library_version,
        )

        # oqtopus version: dist-info is in teksi_module_management_tool/libs/
        tmmt_libs = os.path.join(TMMTPluginUtils.plugin_root_path(), "libs")
        oqtopus_version = _dist_info_version(tmmt_libs, "oqtopus") or "?"
        lib_versions = [
            {"name": "oqtopus", "version": oqtopus_version, "path": os.path.join(tmmt_libs, "oqtopus")},
            get_library_version("pum"),
            get_library_version("pgserviceparser"),
        ]

        bold_font = QFont()
        bold_font.setBold(True)

        grid = self.gridLayout_2
        next_row = grid.rowCount()

        for i, lib in enumerate(lib_versions):
            label = QLabel(f"{lib['name']} version:")
            label.setFont(bold_font)
            value = QLabel(lib["version"])
            value.setToolTip(lib["path"])
            grid.addWidget(label, next_row + i, 0)
            grid.addWidget(value, next_row + i, 1)
