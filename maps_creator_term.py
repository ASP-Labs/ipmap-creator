#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Set log level to benefit from Scapy warnings
import logging
import graphviz as gv
import functools
import logging
import curses
import curses.wrapper
import argparse
import itertools
import copy


logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.DEBUG,
                    filename=u'ex33v3.log'
                    )

logging.info('started')
ipsrc = []
info = 'None'
l = 'None'
nabor = []
ip_dst = []

portdst = []
prov = []


class Picker:
    """Allows you to select from a list with curses"""
    stdscr = None
    win = None
    title = ""
    arrow = ""
    footer = ""
    more = ""
    c_selected = ""
    c_empty = ""

    cursor = 0
    offset = 0
    selected = 0
    selcount = 0
    aborted = False

    window_height = 15
    window_width = 60
    all_options = []
    length = 0

    def curses_start(self):
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.win = curses.newwin(
            5 + self.window_height,
            self.window_width,
            2,
            4
        )

    def curses_stop(self):
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()

    def getSelected(self):
        if self.aborted:
            return False

        ret_s = filter(lambda x: x["selected"], self.all_options)
        ret = map(lambda x: x["label"], ret_s)
        return ret

    def redraw(self):
        self.win.clear()
        self.win.border(
            self.border[0], self.border[1],
            self.border[2], self.border[3],
            self.border[4], self.border[5],
            self.border[6], self.border[7]
        )
        self.win.addstr(
            self.window_height + 4, 5, " " + self.footer + " "
        )

        position = 0
        range = self.all_options[self.offset:self.offset+self.window_height+1]
        for option in range:
            if option["selected"]:
                line_label = self.c_selected + " "
            else:
                line_label = self.c_empty + " "

            self.win.addstr(position + 2, 5, line_label + option["label"])
            position = position + 1

        # hint for more content above
        if self.offset > 0:
            self.win.addstr(1, 5, self.more)

        # hint for more content below
        if self.offset + self.window_height <= self.length - 2:
            self.win.addstr(self.window_height + 3, 5, self.more)

        self.win.addstr(0, 5, " " + self.title + " ")
        self.win.addstr(
            0, self.window_width - 8,
            " " + str(self.selcount) + "/" + str(self.length) + " "
        )
        self.win.addstr(self.cursor + 2, 1, self.arrow)
        self.win.refresh()

    def check_cursor_up(self):
        if self.cursor < 0:
            self.cursor = 0
            if self.offset > 0:
                self.offset = self.offset - 1

    def check_cursor_down(self):
        if self.cursor >= self.length:
            self.cursor = self.cursor - 1

        if self.cursor > self.window_height:
            self.cursor = self.window_height
            self.offset = self.offset + 1

            if self.offset + self.cursor >= self.length:
                self.offset = self.offset - 1

    def curses_loop(self, stdscr):
        while 1:
            self.redraw()
            c = stdscr.getch()

            if c == ord('q') or c == ord('Q'):
                self.aborted = True
                break
            elif c == curses.KEY_UP:
                self.cursor = self.cursor - 1
            elif c == curses.KEY_DOWN:
                self.cursor = self.cursor + 1
            # elif c == curses.KEY_PPAGE:
            # elif c == curses.KEY_NPAGE:
            elif c == ord(' '):
                self.all_options[self.selected]["selected"] = \
                    not self.all_options[self.selected]["selected"]
            elif c == 10:
                break

            # deal with interaction limits
            self.check_cursor_up()
            self.check_cursor_down()

            # compute selected position only after dealing with limits
            self.selected = self.cursor + self.offset

            temp = self.getSelected()
            self.selcount = len(temp)

    def __init__(
        self,
        options,
        title='Select',
        arrow="-->",
        footer="Space = toggle, Enter = accept, q = cancel",
        more="...",
        border="||--++++",
        c_selected="[v]",
        c_empty="[ ]"
    ):
        self.title = title
        self.arrow = arrow
        self.footer = footer
        self.more = more
        self.border = border
        self.c_selected = c_selected
        self.c_empty = c_empty
        self.all_options = []

        for option in options:
            self.all_options.append({
                "label": option,
                "selected": False
            })
            self.length = len(self.all_options)

        self.curses_start()
        curses.wrapper(self.curses_loop)
        self.curses_stop()


def add_nodes(graph, nodes):
    for n in nodes:
        if isinstance(n, tuple):
            graph.node(n[0], **n[1])
        else:
            graph.node(n)
    return graph


def add_edges(graph, edges):
    for e in edges:
        if isinstance(e[0], tuple):
            graph.edge(*e[0], **e[1])
        else:
            graph.edge(*e)
    return graph


def parse_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('file',
                        type=argparse.FileType('r'),
                        help='name of the file with input data'
                        )
    parser.add_argument('-fs', '--formatsave',
                        help='format of result image',
                        default='svg'
                        )
    parser.add_argument('-fc', '--formatcreate',
                        help='image creation method',
                        default='dot'
                        )
    parser.add_argument('-m', '--merge',
                        help='merge nodes if eq connections',
                        dest='merge',
                        action='store_true'
                        )    
    return parser.parse_args()


def get_unique_dst_ips(connects_info):
    dst_ips = []
    for connect_info in connects_info:
        if connect_info['dst_ip'] not in dst_ips:
            dst_ips.append(connect_info['dst_ip'])
    return dst_ips

def get_unique_src_ips(connects_info):
    src_ips = []
    for connect_info in connects_info:
        if connect_info['src_ip'] not in src_ips:
            src_ips.append(connect_info['src_ip'])
    return src_ips

def extract_ips_info(connects_info, dst_ips):
    ips_info = {}
    for ip in dst_ips:
        ips_info[ip] = []
        for connect_info in connects_info:
            if ip == connect_info['dst_ip']:
                item = [connect_info['src_ip'], connect_info['dst_port']]
                if item not in ips_info[ip]:
                    ips_info[ip].append(item)
    return ips_info

def extract_merged_ips_info(connects_info, dst_ips):
    ips_info = {}
    for dst_ip in dst_ips:
        for connect_info in connects_info:

            if dst_ip == connect_info['dst_ip']:
                src_ip = connect_info['src_ip']
                port = connect_info['dst_port']
                ips_info.setdefault(src_ip, {})      # {ip_src1:{ip_dst1:[1,2,3], ip_dst2:[1,23]}} 
                
                if dst_ip not in ips_info[src_ip]:
                    ips_info[src_ip][dst_ip] = []
                if port not in ips_info[src_ip][dst_ip]:
                    ips_info[src_ip][dst_ip].append(port)
    return ips_info


def parse_file(file):
    connects_info = []
    for line in file:
        line_items = line.replace(',', ' ').split()
        connect_info = {}
        connect_info['src_ip'] = line_items[0]
        connect_info['dst_ip'] = line_items[1]
        connect_info['src_port'] = line_items[2]
        connect_info['dst_port'] = line_items[3]
        connect_info['n_connects'] = line_items[4]
        connects_info.append(connect_info)
    return connects_info

def merge_dic_by_eq_keys(dic):
    #TODO: change format of str_keys
    new_dic = {}
    keys = dic.keys()
    first_el = keys[0]
    deleted = []
    while True:
        str_keys = ""
        str_keys += (str(first_el))
        buf = dic[first_el]
        for el in keys:
            if cmp(buf, dic[el]) == 0:
                str_keys += "\n" + str(el)
                del dic[el]
                deleted.append(el)
        keys = [x for x in keys if x not in deleted]
        new_dic [str_keys] = {}
        new_dic [str_keys] = buf
        if keys:
        	first_el = keys[0]
        else:
        	break
    new_dic = copy.deepcopy(new_dic)
    return new_dic

def create_merge_nodes_json(selected_ips, new_ips_info):
    nodes = []

    for ip in new_ips_info:
        nodes.append((ip, {'label': ip}))
        for item in new_ips_info[ip]:
            nodes.append((item, {'label': item}))
    return nodes


def create_merge_edges_json(selected_ips, ips_info):
    edges = []
    for src in ips_info:
    	for dst in ips_info[src]:
    		for link in ips_info[src][dst]:
    			edges.append(((src, dst), {'label': link}))
    return edges

def create_nodes_json(selected_ips, ips_info):
    nodes = []
    for ip in selected_ips:
        nodes.append((ip, {'label': ip}))
        for item in ips_info[ip]:
            nodes.append((item[0], {'label': item[0]}))
    return nodes


def create_edges_json(selected_ips, ips_info):
    edges = []
    for ip in selected_ips:
        for item in ips_info[ip]:
            edges.append(((item[0], ip), {'label': item[1]}))
    return edges


def main():
    # parse input arguments
    args = parse_args()
    # read and parse given file data
    print("[ ] Parsing file %r..." % args.file.name)
    connects_info = parse_file(args.file)
    # select ips
    print("[ ] Selecting IPs...")
    unique_dst_ips = get_unique_dst_ips(connects_info)
    selected_dst_ips = Picker(title='Select destination IPs', options=unique_dst_ips).getSelected()
    logging.info(' SELECTED_DST_IPS: %s' % (selected_dst_ips))


    if not args.merge:
        print("[ ] Get info of selected IPs...")
        selected_ips_info = extract_ips_info(connects_info, selected_dst_ips)
        logging.info('SELECTED_IPS: (IP_SRC PORTDST ) %s:' % (selected_ips_info))
        
        # paint digraph 
        print("[ ] Paint digraph with %s engine to .%s file..." % (args.formatcreate, args.formatsave))
        digraph = functools.partial(gv.Digraph, format='%s' % (args.formatsave),
                                    engine='%s' % (args.formatcreate)
                                    )

        # select nodes and edges
        nodes = create_nodes_json(selected_dst_ips, selected_ips_info)
        logging.info('count graph: %s' % (nodes))
        edges = create_edges_json(selected_dst_ips, selected_ips_info)
        logging.info('communication between graph: %s' % (edges))
    else:
        print("[ ] Get info of selected IPs...")
        selected_ips_info = extract_merged_ips_info(connects_info, selected_dst_ips)
        logging.info('SELECTED_IPS: {IP_DST PORTDST} %s:' % (selected_ips_info))
        
        # paint digraph
        print("[ ] Paint digraph with %s engine to .%s file..." % (args.formatcreate, args.formatsave))
        digraph = functools.partial(gv.Digraph, format='%s' % (args.formatsave),
                                    engine='%s' % (args.formatcreate)
                                    )
        new_ips_info = merge_dic_by_eq_keys(selected_ips_info)
        nodes = create_merge_nodes_json(selected_dst_ips, new_ips_info)
        logging.info('count graph: %s' % (nodes))
        edges = create_merge_edges_json(selected_dst_ips, new_ips_info)
        logging.info('communication between graph: %s' % (edges))
    
    #g = add_edges(add_nodes(digraph(), nodes), edges).render('img/' 'res-%s' % ('_'.join(selected_dst_ips)))
    g = add_edges(add_nodes(digraph(), nodes), edges).render('img/' 'res-%s' % ('_'.join(selected_dst_ips)))
    logging.info(g)
    logging.info('The result is in the folder /img')
    print("[+] Done!")
    print('See result in file %r' % g)

if __name__ == '__main__':
    main()
