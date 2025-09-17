#!/usr/bin/python

"""
Noah Cherry 
9/4/2025

4 Layer Tree Topology For Mininet
This is a 4 layer mininet topology for SDN @Usyd
Network Parameters:
- 4 Layers
   - 3 Switch Layers
   - 1 Host Layer
- Fan = 3
- Link Delays
   - L1-L2
      - 10ms
   - l2-l3
      - 20ms
   - l3-Host
      - 10ms
"""

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.node import DefaultController

class TreeTopo(Topo):
    def constructTree(self, fanout=3, d1="10ms", d2="20ms", d3="10"):
        s1 = self.addSwitch('s0')

        l2 = []
        l3 = []
        hosts = []
        for layer2switch in range(fanout):
            l2.append(self.addSwitch(f's2_{layer2switch+1}'))
            self.addLink(s1, l2[-1], delay=d1) 
            for layer3switch in range(fanout):
                l3.append(self.addSwitch(f's3_{layer2switch*fanout+1+layer3switch}'))
                self.addLink(l2[-1], l3[-1], delay=d2)
                for host_num in range(fanout):
                    hosts.append(self.addHost(f'host_{len(hosts)+1}', mac=f'00:00:00:00:00:{(len(hosts)+1)//10}{(len(hosts)+1)%10}'))
                    self.addLink(l3[-1], hosts[-1], delay=d3)

                    print(l2)
                    print(l3)
                    print(f'HOST LENGTH: {len(hosts)}')

def performanceCheck(Mininet):
    net.start()
    
    print("--- Network Started ---")
    print("This script creates a 3-level tree topology with specific link delays.")
    print("The expected RTTs are:\n"
          "  - ~40ms (hosts on same L3 switch)\n"
          "  - ~120ms (hosts on same L2 switch)\n"
          "  - ~160ms (hosts on different L2 switches)\n")

    # --- Run Ping Tests to Verify RTTs ---
    print("\n--- Running Automated Ping Tests ---")
    
    # Get host objects from the network
    h1 = net.get('host_1')
    h2 = net.get('host_2')   # Same L3 switch as h1
    h4 = net.get('host_4')   # Same L2 switch as h1, different L3
    h10 = net.get('host_10') # Different L2 switch from h1

    # Test 1: Ping between hosts under the same Level 3 switch
    print(f"\n* Pinging h2 ({h2.IP()}) from h1 ({h1.IP()})... (Expected RTT: ~40ms)")
    result = h1.cmd(f'ping -c 3 {h2.IP()}')
    print(result)

    # Test 2: Ping between hosts under the same Level 2 switch
    print(f"\n* Pinging h4 ({h4.IP()}) from h1 ({h1.IP()})... (Expected RTT: ~120ms)")
    result = h1.cmd(f'ping -c 3 {h4.IP()}')
    print(result)

    # Test 3: Ping between hosts under different Level 2 switches
    print(f"\n* Pinging h10 ({h10.IP()}) from h1 ({h1.IP()})... (Expected RTT: ~160ms)")
    result = h1.cmd(f'ping -c 3 {h10.IP()}')
    print(result)

    # --- Start CLI ---
    print("\n--- Starting Mininet CLI ---")
    print("You can now run commands like 'pingall', 'h1 ping h27', etc.")
    CLI(net)

    # Stop the network when the CLI is exited
    net.stop()
                    
if __name__ == '__main__':
    # Set the logging level to 'info' to see key events
    setLogLevel('info')
    #run_network()
    testTopo = TreeTopo()
    testTopo.constructTree()
    net = Mininet(topo=testTopo, link=TCLink, controller=DefaultController)
    performanceCheck(net)
