#!/usr/bin/env python
# -*- coding: utf-8 -*-import sys
from PyQt4 import QtCore, QtGui, QtSvg
import mapcreator
import svgview
import logging
import os


logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.DEBUG,
                    filename=u'ex33v3.log'
                    )
logging.info('started')
info = 'None'
l = 'None'
nabor = []
portdst = []
prov = []
g='none'
MAX_FILENAME = 180
merge=0
path1='None'

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.currentPath = ''
        from svgview import SvgView
        self.view = SvgView()
        self.lchbox_src = listchbox()
        self.lchbox_dst = listchbox()
        self.lchbox_ports=listchbox()
        from mapcreator import MapCreator

        self.mc=MapCreator()

        fileMenu = QtGui.QMenu("&File", self)
        openAction = fileMenu.addAction("&Open...")
        openAction.setShortcut("Ctrl+O")
        runAction = fileMenu.addAction("R&un")
        runAction.setShortcut("Ctrl+R")

        quitAction = fileMenu.addAction("E&xit")
        quitAction.setShortcut("Ctrl+Q")
        optionsMenu = QtGui.QMenu("Options", self)
        mergedAction = optionsMenu.addAction("Merged")
        mergedAction.setShortcut("Ctrl+M")
        mergedAction.isCheckable()
        mergedAction.setCheckable(1)
        mergedAction.setChecked(0)
        ClearSrcSelectAction = optionsMenu.addAction("Clear src ips select")
        ClearSrcSelectAction.setShortcut("Ctrl+Z")
        ClearDstSelectAction = optionsMenu.addAction("Clear dst ips select")
        ClearDstSelectAction.setShortcut("Ctrl+X")
        ClearPortsSelectAction = optionsMenu.addAction("Clear ports select")
        ClearPortsSelectAction.setShortcut("Ctrl+C")
             
        self.menuBar().addMenu(fileMenu)
        self.menuBar().addMenu(optionsMenu)

        openAction.triggered.connect(self.openFile)
        runAction.triggered.connect(self.runFile)
        ClearDstSelectAction.triggered.connect(self.lchbox_dst.clearSelection)
        ClearSrcSelectAction.triggered.connect(self.lchbox_src.clearSelection)
        ClearPortsSelectAction.triggered.connect(self.lchbox_ports.clearSelection)              

        mergedAction.triggered.connect(self.merged)
        quitAction.triggered.connect(QtGui.qApp.quit)

        layout = QtGui.QHBoxLayout()
        splittersrcdst = QtGui.QSplitter(QtCore.Qt.Horizontal)
        splittersrcdst.addWidget(self.lchbox_src)
        splittersrcdst.addWidget(self.lchbox_dst)
        splitterwithports=QtGui.QSplitter(QtCore.Qt.Vertical)
        splitterwithports.addWidget(splittersrcdst)
        splitterwithports.addWidget(self.lchbox_ports)
        splitterwithports.setSizes([800, 400])
        splitter=QtGui.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(splitterwithports)
        splitter.addWidget(self.view)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([300, 1000])
        layout.addWidget(splitter)

        widget= QtGui.QWidget();
        self.setCentralWidget(widget)
        self.centralWidget().setLayout(layout);
        self.setWindowTitle("IPs graph map")

    def merged(self):
        global merge
        if merge==0:
            merge=1
        else:
            merge=0      


    def runFile(self, path=None):
        file=open(path1,'r')
        conectsinfo = self.mc.parse_file(file)
        unique_sources = self.mc.get_unique_src_ips(conectsinfo)
        unique_destinations = self.mc.get_unique_dst_ips(conectsinfo)
        unique_ports = self.mc.get_unique_ports(conectsinfo)

    	self.view.resetTransform
        selected_dst = self.lchbox_dst.selectedItems()
        selected_dst_ips = []
        for x in selected_dst:
            if str(x.text()) in unique_destinations:
                selected_dst_ips.append(str(x.text()))

        selected_src = self.lchbox_src.selectedItems()
        selected_src_ips = []
        for x in selected_src:
            if str(x.text()) in unique_sources:
                selected_src_ips.append(str(x.text()))

        selected_ports = self.lchbox_ports.selectedItems()
        selected_ports_ips = []
        for x in selected_ports:
            if str(x.text()) in unique_ports:
                selected_ports_ips.append(str(x.text()))

        self.mc.create_map(selected_dst_ips,'svg','dot',conectsinfo, selected_src_ips,selected_ports_ips)
        from mapcreator import g
        svg_file = QtCore.QFile(g)
    	self.view.runFile(svg_file)

    def openFile(self, path=None):
    	global path1;
        if not path:
            path = QtGui.QFileDialog.getOpenFileName(self, "Open File",
                    self.currentPath, "pcap file (*.pcapng)")
        if path:
            cmd="sudo tshark -r "+str(path)+" -T fields -e ip.addr -e tcp.port -e udp.port -e frame.len |sort > ./tempfile"
            cmd1="sudo chmod 777 tempfile"
            cmd2="sed -ri '/\S+\s+\S+\s+\S+/!d' tempfile"
            os.system(cmd)
            os.system(cmd1)
            os.system(cmd2)
            path="./tempfile"
            ipsvg_file = QtCore.QFile(path)
            if not ipsvg_file.exists():
                QtGui.QMessageBox.critical(self, "Open File",
                        "Could not open file '%s'." % path)
                return
            self.lchbox_dst.clear();
            self.lchbox_src.clear();
            self.lchbox_ports.clear();
            connects_info = []
            path1=path
            file=open(path,'r')
            pf=self.mc.parse_file(file)
            dst = self.mc.get_unique_dst_ips(pf)
            self.lchbox_dst.openFile(dst)
            src = self.mc.get_unique_src_ips(pf)
            self.lchbox_src.openFile(src)
            ports = self.mc.get_unique_ports(pf)
            self.lchbox_ports.openFile(ports)
            if not path.startswith(':/'):
                self.currentPath = path
                self.setWindowTitle("%s - ips-Graph" % self.currentPath)


class listchbox(QtGui.QListWidget):

    def openFile(self, dst):
        dst.sort()
        for x in dst:
            item = QtGui.QListWidgetItem(str(x), self)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsSelectable)
        self.setSelectionMode(QtGui.QListWidget.MultiSelection)

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
