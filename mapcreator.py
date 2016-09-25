#!/usr/bin/env python
# -*- coding: utf-8 -*-import sys
import logging
import functools
import graphviz as gv

import main 
class MapCreator(object):
	
    def __init__(self):
        super(MapCreator, self).__init__()
        
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
                    ips_info.setdefault(dst_ip, {})   
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
        from main import merge
        # select ips
        unique_dst_ips = self.get_unique_dst_ips(connects_info)     # TODO: unused?
        logging.info(' SELECTED_DST_IPS: %s' % (selected_dst_ips))


        if not merge:
            selected_ips_info = self.extract_ips_info(connects_info, selected_dst_ips)
            logging.info('SELECTED_IPS: (IP_SRC PORTDST ) %s:' % (selected_ips_info))

           # paint digraph
            digraph = functools.partial(gv.Digraph, format='%s' % (formatsave), engine='%s' % (formatcreate))
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