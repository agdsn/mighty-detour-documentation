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

    # Translation jump in configuration
    src += "table ip " + cfg()['netfilter']['translation']['table'] + " {\n"
    src += "\n"
    src += "    chain postrouting {\n"
    src += "        type nat hook postrouting priority 0;\n"
    src += "        meta nftrace set 1\n"
    src += "    }\n"
    src += "\n"
    # DNAT aka portforwarding
    forward_cache = {}
    for f in forwardings:
        if f.public_ip not in forward_cache.keys():
            forward_cache[f.public_ip] = []
        forward_cache[f.public_ip].append(str(f.protocol) + " dport " + str(f.source_port) + " ip saddr "
                                          + str(f.public_ip) + " dnat to "
                                          + str(f.private_ip) + ":"
                                          + str(f.destination_port))
    src += "    chain prerouting {\n"
    src += "        type nat hook prerouting priority 0;\n"
    for f_public_ip in forward_cache.keys():
        src += "        ip saddr " + f_public_ip + " goto " + chain_forwarding(f_public_ip) + "\n"
    src += "    }\n"
    src += "\n"
    for f_public_ip in forward_cache.keys():
        src += "    chain " + chain_forwarding(f_public_ip) + " {\n"
        for f_port_rule in forward_cache[f_public_ip]:
            src += "        " + f_port_rule + "\n"
        src += "    }\n"
        src +=  "\n"
    src += "}\n"
    src += "\n"

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
    src += "table ip " + cfg()['netfilter']['throttle']['table'] + " {\n"
    src += "    map " + cfg()['netfilter']['throttle']['map'] + " {\n"
    src += "        type ipv4_addr: verdict;\n"
    src += "        flags interval;\n"
    src += "        elements = {\n"
    src += "            " + ','.join(generate_throttle_map_elements(throttles)) + "\n"
    src += "        }\n"
    src += "    }\n"
    src += "\n"
    for throttle in throttles:
        src += "    chain " + chain_throttle(throttle.translated_net) + " {\n"
        src += "        limit rate " + str(throttle.speed) + " kbytes/second accept\n"
        src += "    }\n"
        src += "\n"
    # Throttle decision chain
    src += "    chain ratelimit_map {\n"
    src += "        ip saddr vmap @ " + cfg()['netfilter']['throttle']['map'] +"\n"
    src += "    }\n"
    src += "\n"
    # Exception chain (aka blacklist)
    src += "    chain ratelimit_exceptions {\n"
    for b in blacklist:
        src += "        ip saddr " + str(b) + " goto ratelimit_map\n"
    src += "        accept\n"
    src += "    }\n"
    src += "\n"
    # Throttle entry chain, including the whitelist
    src += "    chain ratelimit {\n"
    src += "        type filter hook forward priority 0;\n"
    src += "        policy accept;\n"
    for w in whitelist:
        src += "        ip saddr " + str(w) + " goto ratelimit_exceptions\n"
    src += "        goto ratelimit_map\n"
    src += "    }\n"
    src += "}\n"

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