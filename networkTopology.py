#!/usr/bin/python

from mininet.log import setLogLevel, info
from mn_wifi.net import Mininet_wifi , Mininet
from mn_wifi.node import Station, OVSKernelAP
from mn_wifi.cli import CLI
from mn_wifi.link import wmediumd, adhoc
from mn_wifi.wmediumdConnector import interference
from subprocess import call
import sys

from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel

def myNetwork():

    net = Mininet_wifi(link=wmediumd,wmediumd_mode=interference,ipBase='10.0.0.0/8')

    info( '*** Adding controller\n' )
    info( '*** Add switches/APs\n')

    info( '*** Add hosts/stations\n')
    sta1 = net.addStation('sta1', ip='10.0.0.1',position='50,10,0')
    sta2 = net.addStation('sta2', ip='10.0.0.2',position='100,10,0',color='blue')
    sta3 = net.addStation('sta3', ip='10.0.0.3',position='170,10,0',color='brown')
    sta4 = net.addStation('sta4', ip='10.0.0.4',position='50,80,0',color='purple')
    sta5 = net.addStation('sta5', ip='10.0.0.5',position='110,80,0',color='y')
    sta6 = net.addStation('sta6', ip='10.0.0.6',position='230,40,0',color='r')

    info("*** Configuring Propagation Model\n")
    net.setPropagationModel(model="logDistance", exp=4)

    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()

    info( '*** Add links\n')
    net.addLink(sta2, cls=adhoc, ssid='adhocNet', proto='olsr', mode='g', channel=5, intf='sta2-wlan0')
    net.addLink(sta3, cls=adhoc, ssid='adhocNet', proto='olsr', mode='g', channel=5, intf='sta3-wlan0')
    net.addLink(sta1, cls=adhoc, ssid='adhocNet', proto='olsr', mode='g', channel=5, intf='sta1-wlan0')
    net.addLink(sta4, cls=adhoc, ssid='adhocNet', proto='olsr', mode='g', channel=5, intf='sta4-wlan0')
    net.addLink(sta5, cls=adhoc, ssid='adhocNet', proto='olsr', mode='g', channel=5, intf='sta5-wlan0')
    net.addLink(sta6, cls=adhoc, ssid='adhocNet', proto='olsr', mode='g', channel=5, intf='sta6-wlan0')   

    net.plotGraph(max_x=500, max_y=500)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches/APs\n')

    info( '*** Post configure nodes\n')

    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

