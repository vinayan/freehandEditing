# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

# Tool class
class FreehandEditingTool(QgsMapTool):
    def __init__(self, canvas):
        QgsMapTool.__init__(self,canvas)
        self.canvas=canvas
        self.rb = None
        self.mCtrl = None
        #our own fancy cursor
        self.cursor = QCursor(QPixmap(["16 16 3 1",
                                       "      c None",
                                       ".     c #FF0000",
                                       "+     c #faed55",
                                       "                ",
                                       "       +.+      ",
                                       "      ++.++     ",
                                       "     +.....+    ",
                                       "    +.  .  .+   ",
                                       "   +.   .   .+  ",
                                       "  +.    .    .+ ",
                                       " ++.    .    .++",
                                       " ... ...+... ...",
                                       " ++.    .    .++",
                                       "  +.    .    .+ ",
                                       "   +.   .   .+  ",
                                       "   ++.  .  .+   ",
                                       "    ++.....+    ",
                                       "      ++.++     ",
                                       "       +.+      "]))
                                  
 

    

    def keyPressEvent(self,  event):
        if event.key() == Qt.Key_Control:
            self.mCtrl = True


    def keyReleaseEvent(self,  event):
        if event.key() == Qt.Key_Control:
            self.mCtrl = False
    
    
    def canvasPressEvent(self,event):
        layer = self.canvas.currentLayer()
        gtype = layer.geometryType()
        color = QColor(255,0,0)
        if self.isPolygon:
            self.rb = QgsRubberBand(self.canvas, True)
        else:
            self.rb = QgsRubberBand(self.canvas, False)
            self.rb.setColor(color)
            self.rb.setWidth(1)
        x = event.pos().x()
        y = event.pos().y()
        if gtype == 1:
            if self.mCtrl:
                startingPoint = QPoint(x,y)
                snapper = QgsMapCanvasSnapper(self.canvas)
                (retval,result) = snapper.snapToCurrentLayer (startingPoint, QgsSnapper.SnapToVertex)
                if result <> []:
                    point = result[0].snappedVertex
                else:
                    (retval,result) = snapper.snapToBackgroundLayers(startingPoint)
                    if result <> []:
                        point = result[0].snappedVertex
                    else:
                        point = self.toLayerCoordinates(layer,event.pos())
            else:
                point = self.toLayerCoordinates(layer,event.pos()) 
            pointMap = self.toMapCoordinates(layer, point)
            self.rb.addPoint(pointMap)
        else:
            point = self.toLayerCoordinates(layer,event.pos())
            pointMap = self.toMapCoordinates(layer, point)
            self.rb.addPoint(pointMap)
    
    
    def canvasMoveEvent(self,event):
        if not self.rb:return
        self.rb.addPoint(self.toMapCoordinates(event.pos()))
  

    def canvasReleaseEvent(self,event):
        if not self.rb:return
        if self.rb.numberOfVertices() > 2:
            geom = self.rb.asGeometry()
            self.emit(SIGNAL("rbFinished(PyQt_PyObject)"), geom)
   
        self.rb.reset()
        self.rb=None
       
        # reset rubberband and refresh the canvas
        if self.type == 1:
            self.isPolygon = False
        else:
            self.isPolygon = True
        
        self.canvas.refresh()


    def showSettingsWarning(self):
        pass
    
    def activate(self):
        self.canvas.setCursor(self.cursor)
        # Check whether Geometry is a Line or a Polygon
        mc = self.canvas
        layer = mc.currentLayer()
        self.type = layer.geometryType()
        self.isPolygon = True
        if self.type == 1:
            self.isPolygon = False
        else:
            self.isPolygon = True
        
    def deactivate(self):
        pass

    def isZoomTool(self):
        return False
  
    def isTransient(self):
        return False
    
    def isEditTool(self):
        return True

