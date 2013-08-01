# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *


class FreehandEditingTool(QgsMapTool):

    rbFinished = pyqtSignal('QgsGeometry*')

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.rb = None
        self.mCtrl = None
        self.drawing = False
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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.mCtrl = True

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.mCtrl = False

    def canvasPressEvent(self, event):
        if self.drawing:
            # ignore secondary canvasPressEvents if already drag-drawing
            # NOTE: canvasReleaseEvent will still occur (ensures rb is deleted)
            # click on multi-button input device will halt drag-drawing
            return
        layer = self.canvas.currentLayer()
        if not layer:
            return
        self.drawing = True
        gtype = layer.geometryType()
        color = QColor(255, 0, 0)
        if self.isPolygon:
            #print "self is a polygon"
            self.rb = QgsRubberBand(self.canvas, QGis.Polygon)
        else:
            #print "self is not a polygon"
            self.rb = QgsRubberBand(self.canvas)
            self.rb.setColor(color)
            self.rb.setWidth(1)
        x = event.pos().x()
        y = event.pos().y()
        if gtype == 1:
            if self.mCtrl:
                startingPoint = QPoint(x, y)
                snapper = QgsMapCanvasSnapper(self.canvas)
                (retval, result) = \
                    snapper.snapToCurrentLayer(startingPoint,
                                               QgsSnapper.SnapToVertex)
                if result:
                    point = result[0].snappedVertex
                else:
                    (retval, result) = \
                        snapper.snapToBackgroundLayers(startingPoint)
                    if result:
                        point = result[0].snappedVertex
                    else:
                        point = self.toLayerCoordinates(layer, event.pos())
            else:
                point = self.toLayerCoordinates(layer, event.pos())
            pointMap = self.toMapCoordinates(layer, point)
            self.rb.addPoint(pointMap)
        else:
            point = self.toLayerCoordinates(layer, event.pos())
            pointMap = self.toMapCoordinates(layer, point)
            self.rb.addPoint(pointMap)

    def canvasMoveEvent(self, event):
        if not self.rb:
            return
        self.rb.addPoint(self.toMapCoordinates(event.pos()))
        #print self.rb.asGeometry().exportToWkt()

    def canvasReleaseEvent(self, event):
        self.drawing = False
        if not self.rb:
            return
        if self.rb.numberOfVertices() > 2:
            geom = self.rb.asGeometry()
            self.rbFinished.emit(geom)

        # reset rubberband and refresh the canvas
        self.rb.reset()
        self.rb = None
        self.isPolygon = (self.type != QGis.Line)
        self.canvas.refresh()

    def showSettingsWarning(self):
        pass

    def activate(self):
        mc = self.canvas
        mc.setCursor(self.cursor)
        # Check whether Geometry is a Line or a Polygon
        layer = mc.currentLayer()
        self.type = layer.geometryType()
        # toolbar button is only active with editable line and polygon layers
        self.isPolygon = (self.type != QGis.Line)

    def deactivate(self):
        pass

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True
