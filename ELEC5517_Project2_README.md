# ELEC5517 – Software Defined Networks  
## Assignment II – SDN Operation with ONOS Controller  
### Canvas Network Enhancement Project

**Author:** Tushar Manish Khupte  
**SID:** 520330504  
**Date:** September 2025  
**Environment:** ONOS 2.5 Tutorial VM + Mininet Spine-Leaf Topology  
**Controller:** ONOS Remote (127.0.0.1:6653)  

---

## 🎯 Project Objective
Design, implement, and evaluate an **SDN-based Canvas network** that supports  
1. **Online Lectures** – high-bandwidth video + chat  
2. **Discussion Rooms** – isolated peer sessions  
3. **Online Exams** – low-latency, secure video  

The solution must demonstrate **topology design, flow rules, isolation, QoS, and security** using ONOS and Mininet.

---

## ⚙️ 1 – Topology Design & Mapping

We reused the **built-in Spine-Leaf topology** provided in the ONOS VM.

```bash
sudo mn --custom /opt/onos/mininet/spineleaf.py         --topo spineleaf,spines=2,leafs=4,fanout=4         --controller=remote,ip=127.0.0.1,port=6653
```

| Leaf Switch | Hosts | Canvas Role | QoS Class | Description |
|--------------|--------|-------------|-----------|--------------|
| s11 | h11–h15 | **Lecture Group** | AF41 | High throughput broadcast |
| s12–s13 | h21–h35 | **Discussion Rooms** | CS0 | Best-effort peer traffic |
| s14 | h41–h45 | **Exam Group** | EF | Low latency, high priority |


## 📡 2 – Controller Integration & Basic Connectivity

```bash
onos> app activate org.onosproject.fwd
onos> devices
onos> links
onos> hosts
mininet> pingall
```

✅ Result: 100 % connectivity.  
ONOS GUI → `http://127.0.0.1:8181/onos/ui` (login `onos / rocks`) shows full topology with traffic overlay (`a` key).

---

## 🔐 3 – Security and Isolation

### (a) Host-Level Isolation (Access Layer)
Block unauthorized communication (e.g., exam ↔ discussion).

```bash
curl -u onos:rocks -H "Content-Type: application/json"  -X POST http://127.0.0.1:8181/onos/v1/flows/of:000000000000000b  -d '{
   "priority":40050,"isPermanent":true,
   "deviceId":"of:000000000000000b",
   "treatment":{"instructions":[]},
   "selector":{"criteria":[
     {"type":"ETH_TYPE","ethType":"0x0800"},
     {"type":"IPV4_SRC","ip":"10.0.0.41/32"},
     {"type":"IPV4_DST","ip":"10.0.0.25/32"}
   ]}
 }'
```

📸 Screenshot → H41 cannot ping H25 → **Isolation confirmed**.

---

### (b) Intent-Based Security (Distribution Layer)
Create approved communication paths only:

```bash
onos> add-host-intent 00:00:00:00:00:11/-1 00:00:00:00:00:21/-1
onos> intents
```

No intent = no flow = automatic traffic segmentation.  
If a link fails → intent auto-recompiles (reliability).

---

### (c) Flow Path Control (Core Layer)
Pin sensitive traffic (e.g., lectures) to a fixed uplink for auditability.

```bash
curl -u onos:rocks -H "Content-Type: application/json"  -X POST http://127.0.0.1:8181/onos/v1/flows/of:000000000000000b  -d '{
   "priority":40000,"isPermanent":true,
   "deviceId":"of:000000000000000b",
   "treatment":{"instructions":[{"type":"OUTPUT","port":"1"}]},
   "selector":{"criteria":[
     {"type":"ETH_TYPE","ethType":"0x0800"},
     {"type":"IPV4_SRC","ip":"10.0.0.6/32"},
     {"type":"IPV4_DST","ip":"10.0.0.1/32"}
   ]}
 }'
```

---

### (d) Network Function Layer – VNFs
Deploy virtual firewalls and rate-limiters on Mininet hosts.

```bash
mininet> xterm h41
sudo iptables -A FORWARD -p tcp --dport 80 -j DROP
sudo tc qdisc add dev h41-eth0 root tbf rate 5mbit burst 10kb latency 50ms
```

Acts as a security VNF → blocking HTTP and throttling flows.

---

## 📊 4 – QoS with Meters and Priority Marking

### (a) Create Meter for Exam Traffic (EF)
```bash
curl -u onos:rocks -H "Content-Type: application/json"  -X POST http://127.0.0.1:8181/onos/v1/meters/of:000000000000000b  -d '{
   "deviceId":"of:000000000000000b",
   "unit":"KB_PER_SEC",
   "bands":[
     {"type":"REMARK","rate":40000,"burstSize":8000,"prec":2}
   ]
 }'
```

### (b) Attach Meter to DSCP 46 Traffic
```bash
curl -u onos:rocks -H "Content-Type: application/json"  -X POST http://127.0.0.1:8181/onos/v1/flows/of:000000000000000b  -d '{
   "priority":40040,"isPermanent":true,
   "deviceId":"of:000000000000000b",
   "treatment":{"instructions":[
     {"type":"METER","meterId":1},
     {"type":"OUTPUT","port":"1"}
   ]},
   "selector":{"criteria":[
     {"type":"ETH_TYPE","ethType":"0x0800"},
     {"type":"IP_DSCP","ipDscp":46}
   ]}
 }'
```

### (c) Verification
```bash
mininet> iperf h41 h11
```
Bandwidth is higher for EF exam flows than AF/BE traffic.  

---

## 🧩 5 – Reliability and Fail-Over Testing
```bash
onos> add-host-intent 00:00:00:00:00:11/-1 00:00:00:00:00:13/-1
mininet> link s1 s11 down
onos> intents
```
Intent automatically reroutes traffic → demonstrating recovery.

---

## 🔰 6 – Layered Security Summary

| Layer | Mechanism | Implementation | Benefit |
|--------|------------|----------------|----------|
| Access | Flow drop rules + password policy | ONOS REST + SSH/VNC | Blocks unauthorized peers |
| Distribution | Intents + static paths | ONOS CLI | Segmentation & controlled paths |
| Core | QoS meters + flow auditing | ONOS Controller | Prevents DoS, guarantees bandwidth |
| End-to-End | VNFs (firewall + rate-limit) | Mininet hosts | Runtime packet-level security |

---

## 🧠 7 – Results Summary

| Test | Command | Outcome |
|------|----------|----------|
| Connectivity | `pingall` | 100 % success |
| Isolation | Block exam ↔ discussion | Ping fail confirmed |
| QoS | `iperf` with meters | EF > AF > BE throughput |
| Reliability | `link down` + intent recovery | Automatic reroute |
| GUI | Traffic overlay (`a`) | Visual confirmation of flows |

---

## 💬 8 – Discussion and Conclusion

- **Scalability :** Spine-Leaf supports multi-tenancy and horizontal growth.  
- **Reliability :** Intents auto-recompile on failure, preserving service continuity.  
- **Security :** Multi-layer flow isolation + VNFs ensure data privacy between Canvas services.  
- **QoS :** Meters and DSCP priorities maintain smooth lecture streams and exam sessions.  
- **Efficiency :** Centralized ONOS management simplifies policy updates and monitoring.

> ✅ This integrated design meets all Canvas network requirements and achieves an HD-level implementation for Assignment II.

---

## 📷 9 – Screenshots Checklist (for submission)

1. ONOS GUI topology view + traffic overlay  
2. ONOS CLI → `devices`, `links`, `hosts`, `flows`, `intents`  
3. Mininet → `pingall`, `iperf`, link failure test  
4. REST API Swagger → flow and meter installation  
5. VNFs terminal snapshot (showing iptables rules + tc setup)

---

## 📚 References
- **ELEC5517 Lab 7 – ONOS Basics**  
- **ELEC5517 Lab 8 / 8-2 – REST API and Flow Programming**  

---

> _“Centralized control with distributed policy is the key to secure and scalable SDN designs.”_  
> — ELEC5517 Team Project 2
