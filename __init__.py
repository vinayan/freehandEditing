# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Freehand Editing
                                 A QGIS plugin
                             -------------------
        begin                : 2013-01-23
        copyright            : (C) 2013 by Pavol Kapusta
        email                : pavol.kapusta@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


def name():
    return "Freehand editing"


def description():
    return "Freehand line/polygon editing"


def version():
    return "Version 0.2.6"


def icon():
    return "icon.png"


def qgisMinimumVersion():
    return "1.7"

def author():
    return "Pavol Kapusta"

def email():
    return "pavol.kapusta@gmail.com"

def classFactory(iface):
  from freehandediting import FreehandEditing
  return FreehandEditing(iface)

