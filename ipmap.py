#!/usr/bin/env python
# -*- coding: utf-8 -*-import sys
# This is only needed for Python v2 but is harmless for Python v3.
import sip
sip.setapi('QString', 2)

from PyQt4 import QtCore, QtGui, QtSvg
import logging
import graphviz as gv
import functools
import logging
import curses
import curses.wrapper
import argparse
import itertools
import copy
import hashlib


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
        self.view = SvgView()
        self.lchbox_src = listchbox()
        self.lchbox_dst = listchbox()
        self.lchbox_ports=listchbox()
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
        svg_file = QtCore.QFile(g)
    	self.view.runFile(svg_file)

    def openFile(self, path=None):
    	global path1;
        if not path:
            path = QtGui.QFileDialog.getOpenFileName(self, "Open File",
                    self.currentPath, "data file (*.*)")
        if path:
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

class MapCreator(object):
    """Class creating map from file"""
    def __init__(self):
        super(MapCreator, self).__init__()
        #self.arg = arg
        
    def add_nodes(self, graph, nodes):
        for n in nodes:
            if isinstance(n, tuple):
                graph.node(n[0], **n[1])
            else:
                graph.node(n)
        return graph

    def add_edges(self, graph, edges):
        for e in edges:
            if isinstance(e[0], tuple):
                graph.edge(*e[0], **e[1])
            else:
                graph.edge(*e)
        return graph

    def get_unique_dst_ips(self, connects_info):
        dst_ips = []
        for connect_info in connects_info:
            if connect_info['dst_ip'] not in dst_ips:
                dst_ips.append(connect_info['dst_ip'])
        return dst_ips

    def get_unique_src_ips(self, connects_info):
        src_ips = []
        for connect_info in connects_info:
            if connect_info['src_ip'] not in src_ips:
                src_ips.append(connect_info['src_ip'])
        return src_ips

    # src and dst hosts
    def get_unique_hosts(self, connects_info):
        hosts = []
        for connection in connects_info:
            if connection['src_ip'] not in hosts:
                hosts.append(connection['src_ip'])
            if connection['dst_ip'] not in hosts:
                hosts.append(connection['dst_ip'])
        return hosts

    def get_unique_ports(self, connects_info):
        ports = []
        for connection in connects_info:
            if connection['dst_port'] not in ports:
                ports.append(connection['dst_port'])
        return ports

    def extract_ips_info(self, connects_info, dst_ips):
        ips_info = {}
        for ip in dst_ips:
            ips_info[ip] = []
            for connect_info in connects_info:
                if ip == connect_info['dst_ip']:
                    item = [connect_info['src_ip'], connect_info['dst_port']]
                    if item not in ips_info[ip]:
                        ips_info[ip].append(item)
        return ips_info

    def extract_merged_ips_info(self, connects_info, dst_ips,src_ips):
        ips_info = {}
        for dst_ip in dst_ips:
            for connect_info in connects_info:
                if dst_ip == connect_info['dst_ip']:
                    src_ip = connect_info['src_ip']
                    port = connect_info['dst_port']
                    ips_info.setdefault(dst_ip, {})      # {ip_src1:{ip_dst1:[1,2,3], ip_dst2:[1,23]}}
                    if port not in ips_info[dst_ip]:
                    	ips_info[dst_ip][port] = ''
                    if src_ip in src_ips:
                    	if src_ip not in ips_info[dst_ip][port]:
                    		ips_info[dst_ip][port]=ips_info[dst_ip][port]+'\n'+src_ip
        return ips_info

    def create_nodes_json(self, selected_ips, ips_info, selected_src_ips):
        nodes = []
        for ip in selected_ips:
            nodes.append((ip, {'label': ip,'color':'blue'}))
            for item in ips_info[ip]:
                if item[0] in selected_src_ips:
                    nodes.append((item[0], {'label': item[0],'color':'green'}))
        return nodes

    def create_merge_nodes_json(self, selected_ips, new_ips_info,selected_src_ips):
        nodes = []
        for ip in new_ips_info:
            nodes.append((ip, {'label': ip,'color':'blue'}))
            for item in new_ips_info[ip]:
            	if new_ips_info[ip][item]!='':
            		nodes.append((new_ips_info[ip][item], {'label': new_ips_info[ip][item],'color':'green'}))
        return nodes

    def create_edges_json(self, selected_ips, ips_info, selected_src_ips,selected_ports_ips):
        edges = []
        for ip in selected_ips:
            for item in ips_info[ip]:
                if item[0] in selected_src_ips:
                    if item[1] in selected_ports_ips:
                        edges.append(((item[0], ip), {'label': item[1],'fontsize':'10'}))
        return edges

    def create_merge_edges_json(self, selected_ips, ips_info,selected_ports_ips,selected_src_ips):
        edges = []
        for dst in ips_info:
        	for port in ips_info[dst]:
        		if port in selected_ports_ips:
        			if ips_info[dst][port]!='':
        				edges.append(((ips_info[dst][port], dst), {'label': port,'fontsize':'10'}))
        return edges

    def create_map(self, selected_dst_ips, formatsave, formatcreate, connects_info, selected_src_ips,selected_ports_ips):
        global g
        global merge
        # select ips
        unique_dst_ips = self.get_unique_dst_ips(connects_info)     # TODO: unused?
        logging.info(' SELECTED_DST_IPS: %s' % (selected_dst_ips))


        if not merge:
            selected_ips_info = self.extract_ips_info(connects_info, selected_dst_ips)
            logging.info('SELECTED_IPS: (IP_SRC PORTDST ) %s:' % (selected_ips_info))

           # paint digraph
            digraph = functools.partial(gv.Digraph, format='%s' % (formatsave),
                                        engine='%s' % (formatcreate)
                                        )
            # select nodes and edges
            nodes = self.create_nodes_json(selected_dst_ips, selected_ips_info, selected_src_ips)
            logging.info('count graph: %s' % (nodes))
            edges = self.create_edges_json(selected_dst_ips, selected_ips_info, selected_src_ips,selected_ports_ips)
            logging.info('communication between graph: %s' % (edges))
        else:
            selected_ips_info = self.extract_merged_ips_info(connects_info, selected_dst_ips,selected_src_ips)
            logging.info('SELECTED_IPS: {IP_DST PORTDST} %s:' % (selected_ips_info))
            # paint digraph
            digraph = functools.partial(gv.Digraph, format='%s' % (formatsave),
                                        engine='%s' % (formatcreate)
                                        )
            nodes = self.create_merge_nodes_json(selected_dst_ips, selected_ips_info,selected_src_ips)
            logging.info('count graph: %s' % (nodes))
            edges = self.create_merge_edges_json(selected_dst_ips, selected_ips_info,selected_ports_ips,selected_src_ips)
            logging.info('communication between graph: %s' % (edges))        	
        filename = '_'.join(selected_dst_ips)
        if len(filename) > 180:
        	filename = "file" 

        g = self.add_edges(self.add_nodes(digraph(), nodes), edges).render('img/' 'res-%s' % (filename))
        logging.info(g)
        logging.info('The result is in the folder /img')

    def parse_file(self,file):
        connects_info = []
        for line in file:
            line_items = line.replace(',', ' ').split()
            port = int(line_items[3])
            connect_info = {}
            connect_info['src_ip'] = line_items[0]
            connect_info['dst_ip'] = line_items[1]
            connect_info['src_port'] = line_items[2]
            connect_info['dst_port'] = line_items[3]
            connect_info['load'] = line_items[4]
            connects_info.append(connect_info)
        return connects_info

class listchbox(QtGui.QListWidget):

    def openFile(self, dst):
        dst.sort()
        for x in dst:
            item = QtGui.QListWidgetItem(str(x), self)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsSelectable)
        self.setSelectionMode(QtGui.QListWidget.MultiSelection)

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

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())