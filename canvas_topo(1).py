#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
canvas_spine_leaf.py  (Python 2 compatible)
Clos fabric: 2 spines (s1,s2), 3 leaves (l1..l3), 4 hosts per leaf.
VLANs per host (round-robin): 100,200,300,400.

Run with Mininet:
  sudo mn --custom canvas_topo_py2.py \
    --topo canvas,spines=2,leaves=3,hosts_per_leaf=4 \
    --controller=remote,ip=<ONOS_IP>,port=6653 \
    --switch ovsk,protocols=OpenFlow13
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, Host
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info

class CanvasSpineLeaf(Topo):
    def build(self, spines=2, leaves=3, hosts_per_leaf=4,
              core_bw=10, core_delay='1ms', leaf_bw=5, leaf_delay='2ms',
              host_bw=1, host_delay='5ms'):
        spines = int(spines); leaves = int(leaves); hosts_per_leaf = int(hosts_per_leaf)

        # Create spines
        sp = [ self.addSwitch('s{0}'.format(i), cls=OVSKernelSwitch, protocols='OpenFlow13')
               for i in range(1, spines+1) ]
        # Create leaves
        lf = [ self.addSwitch('l{0}'.format(j), cls=OVSKernelSwitch, protocols='OpenFlow13')
               for j in range(1, leaves+1) ]

        # Full-mesh spines <-> leaves
        for s in sp:
            for l in lf:
                self.addLink(s, l, cls=TCLink, bw=core_bw, delay=core_delay)

        # Hosts per leaf, round-robin VLANs
        vlans = [100, 200, 300, 400]
        for li, leaf in enumerate(lf, start=1):
            for hi in range(1, hosts_per_leaf+1):
                vlan = vlans[(hi-1) % len(vlans)]
                hname = 'h{li}_{hi}_v{v}'.format(li=li, hi=hi, v=vlan)
                # Store VLAN as a param; we’ll use it post-start
                self.addHost(hname, cls=Host, vlan=vlan)
                self.addLink(hname, leaf, cls=TCLink, bw=host_bw, delay=host_delay)

# ------- post-start helpers (safe for Python 2) -------
def forceOpenFlow13(net):
    info('\n*** Forcing OpenFlow13 on all OVS bridges\n')
    for s in net.switches:
        s.cmd('ovs-vsctl set bridge {b} protocols=OpenFlow13'.format(b=s.name))

def postStartVlanConfig(net):
    """
    After net.start():
      - Create eth0.<vlan> per host
      - Assign IP 10.<1|2|3|4>.<leaf>.<host>/24  (100->1, 200->2, 300->3, 400->4)
      - Set leaf host-facing ports as access (Port tag=<vlan>) so VLAN frames are handled
    """
    info('*** Configuring host VLAN subinterfaces, IPs, and leaf access ports\n')
    vmap = {100:1, 200:2, 300:3, 400:4}

    for h in net.hosts:
        vlan = int(getattr(h, 'params', {}).get('vlan', 100))

        # Parse h<li>_<hi>_v<vlan> to get leaf/host indices
        li, hi = 1, 1
        try:
            parts = h.name.split('_')
            li = int(parts[0][1:])  # after 'h'
            hi = int(parts[1])
        except Exception:
            pass

        base = h.defaultIntf().name              # e.g., h1_1_v100-eth0
        sub  = '{b}.{v}'.format(b=base, v=vlan)  # e.g., h1_1_v100-eth0.100

        # Create VLAN sub-if and bring up
        h.cmd('ip link add link {b} name {s} type vlan id {v} 2>/dev/null || true'
              .format(b=base, s=sub, v=vlan))
        h.cmd('ip link set dev {b} up'.format(b=base))
        h.cmd('ip link set dev {s} up'.format(s=sub))

        # Assign legal /24 within classful 10/8
        ip = '10.{o}.{l}.{h}/24'.format(o=vmap.get(vlan,1), l=li, h=hi)
        h.cmd('ip addr flush dev {b}'.format(b=base))
        h.cmd('ip addr add {ip} dev {s}'.format(ip=ip, s=sub))
        h.cmd('ip route add default dev {s} 2>/dev/null || true'.format(s=sub))

        # Find the peer leaf interface and set Port tag=<vlan>
        leaf_node, peer_intf = None, None
        for intf in h.intfList():
            if not intf.link:
                continue
            n1, n2 = intf.link.intf1.node, intf.link.intf2.node
            peer = n1 if n2 == h else n2
            if peer.name.startswith('l'):
                leaf_node = peer
                peer_intf = intf.link.intf1 if intf.link.intf2.node == h else intf.link.intf2
                break

        if leaf_node and peer_intf:
            leaf_node.cmd('ovs-vsctl set Port {p} tag={v}'.format(p=peer_intf.name, v=vlan))
            info('  {hn:14s} VLAN {v:<3d} -> {ip:18s}  (leaf {ln} port {pt})\n'
                 .format(hn=h.name, v=vlan, ip=ip, ln=leaf_node.name, pt=peer_intf.name))
        else:
            info('  ! Could not find leaf for {hn}\n'.format(hn=h.name))

# Export names so `--topo canvas` works
topos = {
    'canvas': (lambda **p: CanvasSpineLeaf(**p)),
    'CanvasSpineLeaf': (lambda **p: CanvasSpineLeaf(**p)),
}

# Allow running this file directly (applies helpers)
def _run():
    setLogLevel('info')
    topo = CanvasSpineLeaf()
    net = Mininet(topo=topo, controller=None, link=TCLink,
                  switch=OVSKernelSwitch, build=True,
                  autoSetMacs=True, autoStaticArp=True)
    net.start()
    forceOpenFlow13(net)
    postStartVlanConfig(net)
    info('\n*** Ready. Try same-VLAN pings (e.g., h1_1_v100 -> 10.1.2.1)\n')
    CLI(net)
    net.stop()

if __name__ == '__main__':
    _run()
