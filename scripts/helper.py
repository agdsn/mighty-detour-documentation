#!/usr/bin/python

import ipaddress

nftBase = ""
table = "nat"
interface = "eth1"
public_ip = ipaddress.ip_address("192.168.0.0")
private_net = ipaddress.ip_network("100.64.0.0/10", False)


def createLevel(net, pref, level):
    if level >= 3:
        return createLeafs(net, pref)

    subnets = net.subnets(prefixlen_diff=3)

    i = 0
    for sub in subnets:
        newPref = pref + "-" + str(i)
        print(nftBase + "add chain " + table + " " + newPref)
        print(nftBase + "add rule " + table + " " + pref + " ip saddr " + str(sub) + " oif " + interface + " goto " + newPref)
        createLevel(sub, newPref, level + 1)
        i += 1


def createLeafs(net, prefix):
    global public_ip
    subnets = net.subnets(prefixlen_diff=3)
    for sub in subnets:
        print(nftBase + "add rule " + table + " " + prefix + " ip saddr " + str(sub) + " oif " + interface + " snat " + str(public_ip))
        public_ip += 1


def generateTree():
    print('#!/usr/sbin/nft')
    print(nftBase + "add chain " + table + " postrouting { type nat hook postrouting priority 0 ;}")
    print(nftBase + "add chain " + table + " postrouting-level-0")
    print(
        nftBase + "add rule " + table + " postrouting ip saddr 100.64.0.0/12 oif " + interface + " goto postrouting-level-0")
    network1 = ipaddress.ip_network("100.64.0.0/12", False)
    createLevel(network1, "postrouting-level-0", 0)

    print(nftBase + "add chain nat postrouting-level-1")
    print(nftBase + "add rule nat postrouting ip saddr 100.80.0.0/12 oif eth0 goto postrouting-level-1")
    network2 = ipaddress.ip_network("100.80.0.0/12", False)
    createLevel(network2, "postrouting-level-1", 0)


def generateMap():
    global public_ip
    print('#!/usr/sbin/nft')
    print(nftBase + "add chain " + table + " postrouting { type nat hook postrouting priority 100 ;}")
    print(nftBase + "add chain " + table + " prerouting { type nat hook prerouting priority 0 ;}")
    print(nftBase + "add map " + table + " subnettoip { type ipv4_addr: ipv4_addr ; flags interval ; }")
    print(nftBase + "add rule ip " + table + " postrouting snat ip saddr map @subnettoip;")

    subnets = private_net.subnets(prefixlen_diff=14)
    for sub in subnets:
        print(nftBase + "add element " + table + " subnettoip { " + str(sub) + " : " + str(public_ip) + " }")
        public_ip += 1


def generateRateLimitMap():
    print('#!/usr/sbin/nft')
    print(nftBase + "add chain " + table + " ratelimit { type filter hook forward priority 0; } ")
    print(nftBase + "add map " + table + " iptoverdict { type ipv4_addr: verdict ; flags interval;}")
    print(nftBase + "add rule ip " + table + " ratelimit ip saddr vmap @iptoverdict;")

    net = ipaddress.ip_network("100.64.0.0/21", False)
    subnets = net.subnets(prefixlen_diff=3)
    for sub in subnets:
        print(nftBase + "add chain " + table + " ratelimit-" + str(sub))
        print(nftBase + "add element " + table + " iptoverdict { " + str(sub) + " : goto " + " ratelimit-" + str(sub) + " }")
        print(nftBase + "add rule " + table + " ratelimit-" + str(sub) + " limit rate 1 mbytes/second accept")


generateTree()
#generateMap()
#generateRateLimitMap()
