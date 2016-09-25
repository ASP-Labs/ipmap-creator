# ipmap creator

## Description
ipmap creator is an open source tool for creating network flow map from wireshark .pcap file.

## Main features
* two modes for display data:
  * standard 
![Standart example](/screen2.png)
  * merged
![Merged example](/screen1.png)
* save result file to .svg format
* selectable source/destination IPs and ports
* use maps_creator_term.py for terminal version of programm

## Installation
* These are the packages that are required to build different python libraries. Install them with apt:
  * sudo apt-get install python-pip python-dev pyqt4-dev-tools
* Update your pip:
  * sudo -H pip install --upgrade pip
* Install a graphviz:
  * pip install graphviz
* Also you need to install tshark:
  * sudo apt-get install tshark
