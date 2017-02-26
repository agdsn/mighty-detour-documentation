from lib.Throttle import *
from lib.Forwarding import *
from nft.tables import *


def create_level(net, pref, level, preflength, translations):
    if level >= cfg()['netfilter']['preflength']:
        return create_leafs(net, pref, preflength=preflength, translations=translations)

    subnets = net.subnets(prefixlen_diff=preflength)

    src = ""

    i = 0
    for sub in subnets:
        newPref = pref + "-" + str(i)
        src += "add chain " + cfg()['netfilter']['translation']['table'] + " " + newPref + "\n"
        src += "add rule " + cfg()['netfilter']['translation']['table'] + " " + pref + " ip saddr " + str(sub) + " goto " + newPref + "\n"
        src += create_level(sub, newPref, level + 1, translations=translations, preflength=preflength) + "\n"
        i += 1;

    return src


def create_leafs(net, prefix, preflength, translations):
    subnets = net.subnets(prefixlen_diff=preflength)
    src = ""
    for sub in subnets:
        if sub in translations:
            # only add rule if translation is present
            src += "add rule " + cfg()['netfilter']['translation']['table'] + " " + prefix + " ip saddr " + str(sub) + " snat " + str(translations[sub]) + "\n"

    return src


def initialize(private_net, translations, throttles, forwardings, blacklist, whitelist, preflength=3):
    logging.debug("Begin generating initial nft configuration")
    src = "#!" + cfg()['netfilter']['nft']['call'] + "\n"
    src += "\n"

    # SNAT configuration
    src += "add table " + cfg()['netfilter']['translation']['table'] + "\n"
    src += "add chain " + cfg()['netfilter']['translation']['table'] + " postrouting { type nat hook postrouting priority 0 ;}\n"
    src += "add rule " + cfg()['netfilter']['translation']['table'] + " postrouting meta nftrace set 1\n"

    if private_net.prefixlen < 12:
        subnets = private_net.subnets(prefixlen_diff=12 - private_net.prefixlen)
        i = 0
        for sub in subnets:
            src += "add chain " + cfg()['netfilter']['translation']['table'] + " postrouting-level-" + str(i) + "\n"
            src += "add rule " + cfg()['netfilter']['translation']['table'] + " postrouting ip saddr "\
                   + str(sub) + " goto postrouting-level-" + str(i) + "\n"
            src += create_level(sub, "postrouting-level-" + str(i), 0, translations=translations, preflength=preflength) + "\n"
            i += 1
    else:
        src += "add chain " + cfg()['netfilter']['translation']['table'] + " postrouting-level-0\n"
        src += create_level(private_net, "postrouting-level-0", 0, translations=translations) + "\n"
        src += "add rule " + cfg()['netfilter']['translation']['table'] + " postrouting ip saddr " + str(private_net) + " goto postrouting-level-0\n"
    src += "\n"

    # Throttling
    src += "add table " + cfg()['netfilter']['throttle']['table'] + "\n"
    src += "add map " + cfg()['netfilter']['throttle']['table'] + " " + cfg()['netfilter']['throttle']['map'] + " { type ipv4_addr: verdict ; flags interval;}\n"
    for throttle in throttles:
        src += generate_throttle(throttle)
    # Throttle decision chain
    src += "add chain " + cfg()['netfilter']['throttle']['table'] + " ratelimit_map\n"
    src += "add rule " + cfg()['netfilter']['throttle']['table'] + " ratelimit_map ip saddr vmap @" + cfg()['netfilter']['throttle']['map'] + ";\n"
    # Exception chain
    src += "add chain " + cfg()['netfilter']['throttle']['table'] + " ratelimit_exceptions\n"
    for b in blacklist:
        src += "add rule " + cfg()['netfilter']['throttle']['table'] + " ratelimit_exceptions ip saddr " + str(b) + " goto ratelimit_map\n"
    src += "add rule " + cfg()['netfilter']['throttle']['table'] + " ratelimit_exceptions accept\n"
    # Throttle entry chain
    src += "add chain " + cfg()['netfilter']['throttle']['table'] + " ratelimit { type filter hook forward priority 0; }\n"
    for w in whitelist:
        src += "add rule " + cfg()['netfilter']['throttle']['table'] + " ratelimit ip saddr " + str(w) + " goto ratelimit_exceptions\n"
    src += "add rule " + cfg()['netfilter']['throttle']['table'] + " ratelimit goto ratelimit_map\n"
    src += "\n"

    # DNAT aka Portforwardings
    src += "add chain " + cfg()['netfilter']['translation']['table'] + " prerouting { type nat hook prerouting priority 0 ;}\n"
    src += generate_forwardings(forwardings)
    logging.debug("End generation initial nft configuration")

    # write stuff to tmpFile
    logging.debug("Write initial nft configuration to file: " + cfg()['netfilter']['nft']['tmpfile'])
    file = open(cfg()['netfilter']['nft']['tmpfile'], 'w')
    file.write(src)
    file.close()

    # drop previous content
    logging.debug("Drop previous configuration and apply new one")
    drop_table_if_exists(cfg()['netfilter']['translation']['table'])
    drop_table_if_exists(cfg()['netfilter']['throttle']['table'])
    # eXecutor!
    subprocess.call(cfg()['netfilter']['nft']['call'] + " -f " +  cfg()['netfilter']['nft']['tmpfile'], shell=True)
    # drop file
    if logging.getLogger().level > logging.DEBUG:
        subprocess.call("/bin/rm " + cfg()['netfilter']['nft']['tmpfile'], shell=True)