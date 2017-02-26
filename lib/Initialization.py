from lib.Throttle import *
from lib.Forwarding import *
from nft.tables import *

nftCall = cfg()['netfilter']['nft']['call']
nftPreamble = "#!" + nftCall
table = cfg()['netfilter']['translation']['table']
tmpFile = cfg()['netfilter']['nft']['tmpfile']
maxLevel = cfg()['netfilter']['preflength']


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
            src += "add rule " + table + " " + prefix + " ip saddr " + str(sub) + " snat " + str(translations[sub]) + "\n"

    return src


def initialize(private_net, translations, throttles, forwardings, blacklist, whitelist, preflength=3):
    logging.debug("Begin generating initial nft configuration")
    src = nftPreamble + "\n"
    src += "\n"

    # SNAT configuration
    src += "add table " + table + "\n"
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
    src += "\n"

    # Throttling
    src += "add table " + table_throttle + "\n"
    src += "add map " + table_throttle + " " + map_throttle + " { type ipv4_addr: verdict ; flags interval;}\n"
    for throttle in throttles:
        src += generate_throttle(throttle)
    # Throttle decision chain
    src += "add chain " + table_throttle + " ratelimit_map\n"
    src += "add rule " + table_throttle + " ratelimit_map ip saddr vmap @" + map_throttle + ";\n"
    # Exception chain
    src += "add chain " + table_throttle + " ratelimit_exceptions\n"
    for b in blacklist:
        src += "add rule " + table_throttle + " ratelimit_exceptions ip saddr " + str(b) + " goto ratelimit_map\n"
    src += "add rule " + table_throttle + " ratelimit_exceptions accept\n"
    # Throttle entry chain
    src += "add chain " + table_throttle + " ratelimit { type filter hook forward priority 0; }\n"
    for w in whitelist:
        src += "add rule " + table_throttle + " ratelimit ip saddr " + str(w) + " goto ratelimit_exceptions\n"
    src += "add rule " + table_throttle + " ratelimit goto ratelimit_map\n"
    src += "\n"

    # DNAT aka Portforwardings
    src += "add chain " + table + " prerouting { type nat hook prerouting priority 0 ;}\n"
    src += generate_forwardings(forwardings)
    logging.debug("End generation initial nft configuration")

    # write stuff to tmpFile
    logging.debug("Write initial nft configuration to file: " + tmpFile)
    file = open(tmpFile, 'w')
    file.write(src)
    file.close()

    # drop previous content
    logging.debug("Drop previous configuration and apply new one")
    drop_table_if_exists(table)
    drop_table_if_exists(table_throttle)
    # eXecutor!
    subprocess.call(nftCall + " -f " +  tmpFile, shell=True)
    # drop file
    if logging.getLogger().level > logging.DEBUG:
        subprocess.call("/bin/rm " + tmpFile, shell=True)