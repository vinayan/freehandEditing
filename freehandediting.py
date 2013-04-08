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
# 'Numerical Vertex Edit Plugin' and 'traceDigitize' plugin, Copyright (C) Cédric Möri
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

# Our main class for the plugin
class FreehandEditing:

    def __init__(self, iface):
      # Save reference to the QGIS interface
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
    
    def initGui(self):        
        settings = QSettings()
        # Create action
        self.freehand_edit = QAction(QIcon(":/plugins/freehandEditing/icon.png"),  "Freehand editing",  self.iface.mainWindow())
        self.freehand_edit.setEnabled(False)
        self.freehand_edit.setCheckable(True)
        # Add toolbar button and menu item
        self.iface.digitizeToolBar().addAction(self.freehand_edit)
        self.iface.editMenu().addAction(self.freehand_edit)
      
        self.spinBox = QDoubleSpinBox(self.iface.mainWindow())
        self.spinBox.setDecimals(2)
        self.spinBox.setMinimum(0.00)
        self.spinBox.setMaximum(5.00)
        self.spinBox.setSingleStep(0.10)
        toleranceval = settings.value("/freehandEdit/tolerance").toDouble()
        if not toleranceval[1]:
           settings.setValue("/freehandEdit/tolerance", 0.00)
        self.spinBox.setValue(toleranceval[0])
        self.spinBoxAction = self.iface.digitizeToolBar().addWidget(self.spinBox)
        self.spinBox.setToolTip("Tolerance. Level of simplification.")
        self.spinBoxAction.setEnabled(False)
    
        # Connect to signals for button behaviour
        QObject.connect(self.freehand_edit,  SIGNAL("activated()"),  self.freehandediting)
        QObject.connect(self.iface, SIGNAL("currentLayerChanged(QgsMapLayer*)"), self.toggle)
        QObject.connect(self.canvas, SIGNAL("mapToolSet(QgsMapTool*)"), self.deactivate)
        QObject.connect(self.spinBox,  SIGNAL("valueChanged(double)"),  self.tolerancesettings)
    
        # Get the tool
        self.tool = FreehandEditingTool( self.canvas )
               
      
    def tolerancesettings(self):
		settings = QSettings()
		settings.setValue("/freehandEdit/tolerance", self.spinBox.value())

    
    def freehandediting(self):
        self.canvas.setMapTool(self.tool)
        self.freehand_edit.setChecked(True)    
      
        QObject.connect(self.tool, SIGNAL("rbFinished(PyQt_PyObject)"), self.createFeature)  

        
    def toggle(self):
        mc = self.canvas
        layer = mc.currentLayer()

        #Decide whether the plugin button/menu is enabled or disabled
        if layer <> None:
            if layer.isEditable() and (layer.geometryType() == 1 or layer.geometryType() == 2) and (layer.crs().projectionAcronym() == "longlat"):
                self.freehand_edit.setEnabled(True)
                self.spinBoxAction.setEnabled(False)
                QObject.connect(layer,SIGNAL("editingStopped()"),self.toggle)
                QObject.disconnect(layer,SIGNAL("editingStarted()"),self.toggle)
            elif layer.isEditable() and (layer.geometryType() == 1 or layer.geometryType() == 2) and (layer.crs().projectionAcronym() != "longlat"):
                self.freehand_edit.setEnabled(True)
                self.spinBoxAction.setEnabled(True)
                QObject.connect(layer,SIGNAL("editingStopped()"),self.toggle)
                QObject.disconnect(layer,SIGNAL("editingStarted()"),self.toggle)
            else:
                self.freehand_edit.setEnabled(False)
                self.spinBoxAction.setEnabled(False)
                QObject.connect(layer,SIGNAL("editingStarted()"),self.toggle)
                QObject.disconnect(layer,SIGNAL("editingStopped()"),self.toggle)


    def createFeature(self, geom):
        settings = QSettings()
        mc = self.canvas
        layer = mc.currentLayer()
        renderer = mc.mapRenderer()
        layerCRSSrsid = layer.crs().srsid()
        projectCRSSrsid = renderer.destinationCrs().srsid()
        provider = layer.dataProvider()
        f = QgsFeature()
        
        
        if layer.crs().projectionAcronym() == "longlat":
            tolerance = 0.00
        else:
            tolerance = settings.value("/freehandEdit/tolerance").toDouble()[0]
 
        #On the Fly reprojection.
        if layerCRSSrsid != projectCRSSrsid:
            geom.transform(QgsCoordinateTransform(projectCRSSrsid, layerCRSSrsid))

        s = geom.simplify(tolerance)
        
        #validate geometry
        if not (s.validateGeometry()):
            f.setGeometry(s)
        else:
            reply = QMessageBox.question(self.iface.mainWindow(), 'Feature not valid',
            "The geometry of the feature you just added isn't valid. Do you want to use it anyway?",
            QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                f.setGeometry(s)
            else:
                return False
        
        # add attribute fields to feature
        fields = layer.pendingFields()
        
        # vector api change update
        if QGis.QGIS_VERSION_INT >= 10900:
            f.initAttributes(fields.count())			
            for i in range(fields.count()):
                f.setAttribute(i,provider.defaultValue(i))
        else:
			for i in fields:
				f.addAttribute(i,  provider.defaultValue(i))
        
        if not (settings.value("/qgis/digitizing/disable_enter_attribute_values_dialog").toBool()):
            self.iface.openFeatureForm( layer, f, False)
        
        layer.beginEditCommand("Feature added")       
        layer.addFeature(f)
        layer.endEditCommand()

	                
    def deactivate(self):
        self.freehand_edit.setChecked(False)
        QObject.disconnect(self.tool, SIGNAL("rbFinished(PyQt_PyObject)"), self.createFeature)

	 
    def unload(self):
        self.iface.digitizeToolBar().removeAction(self.freehand_edit)
        self.iface.digitizeToolBar().removeAction(self.spinBoxAction)
