#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call

def myNetwork():

    net = Mininet( topo=None,
                   build=False,
                   ipBase='10.0.0.0/8')

    info( '*** Adding controller\n' )
    c0=net.addController(name='c0',
                      controller=RemoteController,
                      ip='127.0.0.1',
                      protocol='tcp',
                      port=6633)

    info( '*** Add switches\n')
    L1 = net.addSwitch('L1', cls=OVSKernelSwitch)
    L2 = net.addSwitch('L2', cls=OVSKernelSwitch)
    L3 = net.addSwitch('L3', cls=OVSKernelSwitch)
    L4 = net.addSwitch('L4', cls=OVSKernelSwitch)
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch)

    info( '*** Add hosts\n')
    h1 = net.addHost('h1', cls=Host, ip='10.1.0.11/24', defaultRoute=None)
    h2 = net.addHost('h2', cls=Host, ip='10.1.0.12/24', defaultRoute=None)
    h3 = net.addHost('h3', cls=Host, ip='10.2.0.13/24', defaultRoute=None)
    h4 = net.addHost('h4', cls=Host, ip='10.2.0.14/24', defaultRoute=None)
    h5 = net.addHost('h5', cls=Host, ip='10.3.0.15/24', defaultRoute=None)
    h6 = net.addHost('h6', cls=Host, ip='10.3.0.16/24', defaultRoute=None)
    h7 = net.addHost('h7', cls=Host, ip='10.4.0.17/24', defaultRoute=None)
    h8 = net.addHost('h8', cls=Host, ip='10.4.0.18/24', defaultRoute=None)

    info( '*** Add links\n')
    net.addLink(h1, L1)
    net.addLink(h2, L1)
    net.addLink(h3, L2)
    net.addLink(h4, L2)
    net.addLink(h5, L3)
    net.addLink(h6, L3)
    net.addLink(h7, L4)
    net.addLink(h8, L4)
    net.addLink(L1, s1)
    net.addLink(L1, s2)
    net.addLink(L2, s1)
    net.addLink(L2, s2)
    net.addLink(L3, s1)
    net.addLink(L3, s2)
    net.addLink(L4, s1)
    net.addLink(L4, s2)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('L1').start([])
    net.get('L2').start([])
    net.get('L3').start([])
    net.get('L4').start([])
    net.get('s1').start([c0])
    net.get('s2').start([c0])

    info( '*** Post configure switches and hosts\n')

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

