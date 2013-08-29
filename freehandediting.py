# -*- coding: utf-8 -*-
#-----------------------------------------------------------
#
# Freehand Editing
# Copyright (C) 2010 - 2012 Pavol Kapusta
# pavol.kapusta@gmail.com
#
# Code adopted/adapted from:
#
# 'SelectPlus Menu Plugin', Copyright (C) Barry Rowlingson
# 'Numerical Vertex Edit Plugin' and 'traceDigitize' plugin,
#  Copyright (C) Cédric Möri
#
# Spinbox idea adopted from:
# 'Improved polygon capturing' plugin, Copyright (C) Adrian Weber
#
#-----------------------------------------------------------
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
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#---------------------------------------------------------------------


# Import the PyQt and the QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

#Import own classes and tools
from freehandeditingtool import FreehandEditingTool

# initialize Qt resources from file resources.py
import resources


class FreehandEditing:

    def __init__(self, iface):
      # Save reference to the QGIS interface
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.active = False

    def initGui(self):
        settings = QSettings()
        # Create action
        self.freehand_edit = \
            QAction(QIcon(":/plugins/freehandEditing/icon.png"),
                    "Freehand editing", self.iface.mainWindow())
        self.freehand_edit.setEnabled(False)
        self.freehand_edit.setCheckable(True)
        # Add toolbar button and menu item
        self.iface.digitizeToolBar().addAction(self.freehand_edit)
        self.iface.editMenu().addAction(self.freehand_edit)

        self.spinBox = QDoubleSpinBox(self.iface.mainWindow())
        self.spinBox.setDecimals(3)
        self.spinBox.setMinimum(0.000)
        self.spinBox.setMaximum(5.000)
        self.spinBox.setSingleStep(0.100)
        toleranceval = \
            settings.value("/freehandEdit/tolerance", 0.000, type=float)
        if not toleranceval:
            settings.setValue("/freehandEdit/tolerance", 0.000)
        self.spinBox.setValue(toleranceval)
        self.spinBoxAction = \
            self.iface.digitizeToolBar().addWidget(self.spinBox)
        self.spinBox.setToolTip("Tolerance. Level of simplification.")
        self.spinBoxAction.setEnabled(False)

        # Connect to signals for button behaviour
        self.freehand_edit.activated.connect(self.freehandediting)
        self.iface.currentLayerChanged['QgsMapLayer*'].connect(self.toggle)
        self.canvas.mapToolSet['QgsMapTool*'].connect(self.deactivate)
        self.spinBox.valueChanged[float].connect(self.tolerancesettings)

        # Get the tool
        self.tool = FreehandEditingTool(self.canvas)

    def tolerancesettings(self):
        settings = QSettings()
        settings.setValue("/freehandEdit/tolerance", self.spinBox.value())

    def freehandediting(self):
        self.canvas.setMapTool(self.tool)
        self.freehand_edit.setChecked(True)
        self.tool.rbFinished['QgsGeometry*'].connect(self.createFeature)
        self.active = True

    def toggle(self):
        mc = self.canvas
        layer = mc.currentLayer()
        if layer is None:
            return

        #Decide whether the plugin button/menu is enabled or disabled
        if (layer.isEditable() and (layer.geometryType() == QGis.Line or
                                    layer.geometryType() == QGis.Polygon)):
            self.freehand_edit.setEnabled(True)
            self.spinBoxAction.setEnabled(
                layer.crs().projectionAcronym() != "longlat")
            try:  # remove any existing connection first
                layer.editingStopped.disconnect(self.toggle)
            except TypeError:  # missing connection
                pass
            layer.editingStopped.connect(self.toggle)
            try:
                layer.editingStarted.disconnect(self.toggle)
            except TypeError:  # missing connection
                pass
        else:
            self.freehand_edit.setEnabled(False)
            self.spinBoxAction.setEnabled(False)
            if (layer.type() == QgsMapLayer.VectorLayer and
                    (layer.geometryType() == QGis.Line or
                     layer.geometryType() == QGis.Polygon)):
                try:  # remove any existing connection first
                    layer.editingStarted.disconnect(self.toggle)
                except TypeError:  # missing connection
                    pass
                layer.editingStarted.connect(self.toggle)
                try:
                    layer.editingStopped.disconnect(self.toggle)
                except TypeError:  # missing connection
                    pass

    def createFeature(self, geom):
        settings = QSettings()
        mc = self.canvas
        layer = mc.currentLayer()
        if layer is None:
            return
        renderer = mc.mapRenderer()
        layerCRSSrsid = layer.crs().srsid()
        projectCRSSrsid = renderer.destinationCrs().srsid()
        provider = layer.dataProvider()
        f = QgsFeature()

        if layer.crs().projectionAcronym() == "longlat":
            tolerance = 0.000
        else:
            tolerance = settings.value("/freehandEdit/tolerance",
                                       0.000, type=float)

        #On the Fly reprojection.
        if layerCRSSrsid != projectCRSSrsid:
            geom.transform(QgsCoordinateTransform(projectCRSSrsid,
                                                  layerCRSSrsid))
        s = geom.simplify(tolerance)

        #validate geometry
        if not (s.validateGeometry()):
            f.setGeometry(s)
        else:
            reply = QMessageBox.question(
                self.iface.mainWindow(),
                'Feature not valid',
                "The geometry of the feature you just added isn't valid."
                "Do you want to use it anyway?",
                QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                f.setGeometry(s)
            else:
                return

        # add attribute fields to feature
        fields = layer.pendingFields()
        if QGis.QGIS_VERSION_INT >= 10900:  # vector api change update
            f.initAttributes(fields.count())
            for i in range(fields.count()):
                if provider.defaultValue(i):
                    f.setAttribute(i, provider.defaultValue(i))
        else:
            for i in fields:
                f.addAttribute(i, provider.defaultValue(i))

        layer.beginEditCommand("Feature added")
        if (settings.value(
                "/qgis/digitizing/disable_enter_attribute_values_dialog",
                False, type=bool)):
            layer.addFeature(f)
            layer.endEditCommand()
        else:
            dlg = self.iface.getFeatureForm(layer, f)
            self.tool.setIgnoreClick(True)
            if dlg.exec_():
                layer.addFeature(f)
                layer.endEditCommand()
            else:
                layer.destroyEditCommand()
            self.tool.setIgnoreClick(False)

    def deactivate(self):
        self.freehand_edit.setChecked(False)
        if self.active:
            self.tool.rbFinished['QgsGeometry*'].disconnect(self.createFeature)
        self.active = False

    def unload(self):
        self.iface.digitizeToolBar().removeAction(self.freehand_edit)
        self.iface.digitizeToolBar().removeAction(self.spinBoxAction)
