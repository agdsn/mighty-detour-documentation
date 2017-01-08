#!/usr/bin/python

import ipaddress

nftBase = ""
iptBase = "iptables "
table = "nat"
interface = "eth5.300"
public_ip = ipaddress.ip_address("192.168.0.19")
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
        i += 1;


def createLeafs(net, prefix):
    global public_ip
    subnets = net.subnets(prefixlen_diff=3)
    for sub in subnets:
        print(nftBase + "add rule " + table + " " + prefix + " ip saddr " + str(sub) + " oif " + interface + " snat " + str(public_ip))
        public_ip += 1


def generateTree():
    print('#!/usr/sbin/nft')
    print(nftBase + "add chain " + table + " prerouting { type nat hook prerouting priority 0 ;}")
    print(nftBase + "add chain " + table + " postrouting { type nat hook postrouting priority 0 ;}")
    print(nftBase + "add rule " + table + " postrouting meta nftrace set 1")
    #print(nftBase + "add rule " + table + " prerouting meta nftrace set 1")
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

def generateTreeIpTables():
    print('#!/bin/sh')
    print(iptBase + "-t " + table + " -N postrouting-level-0")
    print(iptBase + "-t " + table + " -A POSTROUTING -s 100.64.0.0/12 -o " + interface + " -j postrouting-level-0")
    network1 = ipaddress.ip_network("100.64.0.0/12", False)
    createLevelIptable(network1, "postrouting-level-0", 0)

    print(iptBase + "-t " + table + " -N postrouting-level-1")
    print(iptBase + "-t " + table + " -A POSTROUTING -s 100.80.0.0/12 -o " + interface + "-j postrouting-level-1")
    network2 = ipaddress.ip_network("100.80.0.0/12", False)
    createLevelIptable(network2, "postrouting-level-1", 0)

def createLeafsIptables(net, prefix):
    global public_ip
    subnets = net.subnets(prefixlen_diff=3)
    for sub in subnets:
        print(iptBase + "-t " + table + " -A " + prefix + " -s " + str(sub) + " -o " + interface + " -j SNAT --to " + str(public_ip))
        public_ip += 1

def createLevelIptable(net, pref, level):
    if level >= 3:
        return createLeafsIptables(net, pref)

    subnets = net.subnets(prefixlen_diff=3)

    i = 0
    for sub in subnets:
        newPref = pref + "-" + str(i)
        print(iptBase + "-t " + table + " -N " + newPref)
        print(iptBase + "-t " + table + " -A " + pref + " -s " + str(sub) + " -i " + interface + " -j " + newPref)
        createLevelIptable(sub, newPref, level + 1)
        i += 1

def generateSingleDNAT():
    print('#!/usr/sbin/nft')
    print(nftBase + "add chain " + table + " postrouting { type nat hook postrouting priority 100 ;}")
    print(nftBase + "add chain " + table + " prerouting { type nat hook prerouting priority 0 ;}")
    print(nftBase + "add rule nat prerouting ip daddr 192.168.0.10 tcp dport 9999 dnat 100.64.1.1")

def ip_interface():
    external_ip = ipaddress.ip_address("192.168.0.10")
    for i in range(0,6000):
         call("ip addr add " + str(external_ip) + "/16 dev " + interface, shell=True)
         external_ip = external_ip + 1



#generateTree()
generateTreeIpTables()
#generateMap()
#generateRateLimitMap()
#generateSingleDNAT()
