from ipaddress import IPv4Address, IPv4Network

nftCall = "/usr/sbin/nft"
nftPreamble = "#!/usr/sbin/nft"
table = "nat"
tmpFile = "/tmp/nft.rules"
maxLevel = 3

def is_subnet_of(a, b):
   """
   Returns boolean: is `a` a subnet of `b`?
   """
   a_len = a.prefixlen
   b_len = b.prefixlen
   return a_len >= b_len and a.supernet(a_len - b_len) == b

def calculate_chain_name(priv_net, subnet, preflength):
    path = "postrouting-level-"
    subnets = priv_net.subnets(prefixlen_diff=12 - priv_net.prefixlen)
    current_net = IPv4Network('0.0.0.0/0')
    i = 0
    for sub in subnets:
        if is_subnet_of(subnet,sub):
            path += str(i)
            current_net = subnet
            break
        i += 1
    while current_net.prefixlen > subnet.prefixlen:
        path += "-"
        i = 0
        subnets = current_net.subnets(prefixlen_diff=preflength)
        for sub in subnets:
            if subnet in sub:
                path += str(i)
                current_net = subnet
                break
            i += 1
    return path


def createLevel(net, pref, level, preflength, translations):
    if level >= maxLevel:
        return createLeafs(net, pref, preflength=preflength, translations=translations)

    subnets = net.subnets(prefixlen_diff=preflength)

    src = ""

    i = 0
    for sub in subnets:
        newPref = pref + "-" + str(i)
        src += "add chain " + table + " " + newPref + "\n"
        src += "add rule " + table + " " + pref + " ip saddr " + str(sub) + " goto " + newPref + "\n"
        src += createLevel(sub, newPref, level + 1, translations=translations, preflength=preflength) + "\n"
        i += 1;

    return src


def createLeafs(net, prefix, preflength, translations):
    subnets = net.subnets(prefixlen_diff=preflength)
    src = ""
    for sub in subnets:
        if sub in translations:
            # only add rule if translation is present
            src += "add rule " + table + " " + prefix + " ip saddr " + str(sub) + " snat " + translations[sub] + "\n"

    return src


def initializeNAT(private_net, translations, preflength=3):
    src = nftPreamble + "\n"
    src += "\n"
    src += "add chain " + table + " prerouting { type nat hook prerouting priority 0 ;}\n"
    src += "add chain " + table + " postrouting { type nat hook postrouting priority 0 ;}\n"
    src += "add rule " + table + " postrouting meta nftrace set 1\n"

    if private_net.prefixlen < 12:
        subnets = private_net.subnets(prefixlen_diff=12 - private_net.prefixlen)
        i = 0
        for sub in subnets:
            src += "add chain " + table + " postrouting-level-" + str(i) + "\n"
            src += "add rule " + table + " postrouting ip saddr " + str(sub) + " goto postrouting-level-" + str(i) + "\n"
            src += createLevel(sub, "postrouting-level-" + str(i), 0, translations=translations, preflength=preflength) + "\n"
            i += 1
    else:
        src += "add chain " + table + " postrouting-level-0\n"
        src += createLevel(private_net, "postrouting-level-0", 0, translations=translations) + "\n"
        src += "add rule " + table + " postrouting ip saddr " + str(private_net) + " goto postrouting-level-0\n"

    # write stuff to tmpFile
    file = open(tmpFile, 'w')
    file.write(src)
    file.close()

    # drop previous content
    #call(nftCall + " flush table " + table, shell=True)
    # eXecutor!
    #call(nftCall + " -f " +  tmpFile, shell=True)
    # drop file
    #call("/bin/rm " + tmpFile, shell=True)


def generateRateLimitMap():
    print('#!/usr/sbin/nft')
    src = "add chain " + table + " ratelimit { type filter hook forward priority 0; } "
    src += "add map " + table + " iptoverdict { type ipv4_addr: verdict ; flags interval;}"
    src += "add rule ip " + table + " ratelimit ip saddr vmap @iptoverdict;"

    net = IPv4Network("100.64.0.0/21", False)
    subnets = net.subnets(prefixlen_diff=3)
    for sub in subnets:
        src += "add chain " + table + " ratelimit-" + str(sub)
        src += "add element " + table + " iptoverdict { " + str(sub) + " : goto " + " ratelimit-" + str(sub) + " }"
        src += "add rule " + table + " ratelimit-" + str(sub) + " limit rate 1 mbytes/second accept"

def generateSingleDNAT():
    print('#!/usr/sbin/nft')
    src = "add chain " + table + " postrouting { type nat hook postrouting priority 100 ;}"
    src += "add chain " + table + " prerouting { type nat hook prerouting priority 0 ;}"
    src += "add rule nat prerouting ip daddr 192.168.0.10 tcp dport 9999 dnat 100.64.1.1"