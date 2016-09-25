#!/usr/bin/env python
# -*- coding: utf-8 -*-import sys
from PyQt4 import QtCore, QtGui, QtSvg

class SvgView(QtGui.QGraphicsView):
    def __init__(self, parent=None):
        super(SvgView, self).__init__(parent)

        self.svgItem = None
        self.image = QtGui.QImage()
        self.setScene(QtGui.QGraphicsScene(self))
        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)

    def runFile(self, svg_file):
        if not svg_file.exists():
            return
        self.setScene(QtGui.QGraphicsScene(self))
        s = self.scene()
        s.clear()

        self.svgItem = QtSvg.QGraphicsSvgItem(svg_file.fileName())
        self.svgItem.setFlags(QtGui.QGraphicsItem.ItemClipsToShape)
        self.svgItem.setCacheMode(QtGui.QGraphicsItem.NoCache)
        self.svgItem.setZValue(0)
        s.addItem(self.svgItem)

    def wheelEvent(self, event):
        zoomInFactor = 1.25
        zoomOutFactor = 1 / zoomInFactor
        if event.delta() > 0:
            zoomFactor = zoomInFactor
        else:
            zoomFactor = zoomOutFactor
        self.scale(zoomFactor, zoomFactor)