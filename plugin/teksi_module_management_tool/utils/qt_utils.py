"""
/***************************************************************************
                              -------------------
        begin                : 2016
        copyright            : (C) 2016 by OPENGIS.ch
        email                : info@opengis.ch
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

from PyQt5.QtWidgets import QApplication


class OverrideCursor:
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        QApplication.setOverrideCursor(self.cursor)

    def __exit__(self, exc_type, exc_val, exc_tb):
        QApplication.restoreOverrideCursor()

class QtUtils:

    @staticmethod
    def setForegroundColor(widget, color):
        """
        Set the foreground color of a widget.
        :param widget: The widget to set the foreground color for.
        :param color: The color to set.
        """
        palette = widget.palette()
        palette.setColor(widget.foregroundRole(), color)
        widget.setPalette(palette)
    
    @staticmethod
    def resetForegroundColor(widget):
        """
        Reset the foreground color of a widget to the default.
        :param widget: The widget to reset the foreground color for.
        """
        palette = widget.palette()
        palette.setColor(widget.foregroundRole(), QApplication.style().standardPalette().color(palette.WindowText))
        widget.setPalette(palette)

    @staticmethod
    def setFontItalic(widget, italic):
        """
        Set the font of a widget to italic.
        :param widget: The widget to set the font for.
        """
        font = widget.font()
        font.setItalic(italic)
        widget.setFont(font)

