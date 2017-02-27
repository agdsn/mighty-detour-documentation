import math

from helper.conntrack import drop_conntrack
from lib.Throttle import *
from lib.Forwarding import *
from nft.tables import *


def chain_translation_name(net):
    return "postrouting-" + str(IPv4Network(net)).replace(".", "-").replace("/", "-")


def initialize(translations, throttles, forwardings, blacklist, whitelist):
    logging.debug("Begin generating initial nft configuration")

    translos = {}
    # Preprocess translations
    for translated_net in translations.keys():
        private_scale_net = translated_net.supernet(new_prefix=cfg()['netfilter']['tree']['lowlevel'])
        if private_scale_net not in translos.keys():
            translos[private_scale_net] = []
        translos[private_scale_net].append("ip saddr " + str(translated_net) + " snat to " + str(translations[translated_net]))

    src = "#!" + cfg()['netfilter']['nft']['call'] + "\n"
    src += "\n"

    # Translation
    src += "table " + cfg()['netfilter']['translation']['table'] + " {\n"
    src += "\n"
    src += "    chain postrouting {\n"
    src += "        type nat hook postrouting priority 0;\n"
    src += "        meta nftrace set 1\n"

    # Last tree level net size: cfg()['netfilter']['tree']['lowlevel']
    lowlevel = int(cfg()['netfilter']['tree']['lowlevel'])
    # Maximum jumps per tree level: cfg()['netfilter']['tree']['jumpcount']
    jumps = int(cfg()['netfilter']['tree']['jumpcount'])
    # Private address range: cfg()['cgn']['net']
    cgn = IPv4Network(cfg()['cgn']['net'])
    # calculate levels:
    cidr_level_size = math.ceil(math.log2(jumps))
    if cidr_level_size < 1 or cidr_level_size > cgn.prefixlen:
        logging.critical("The calculated level size %s is invalid for the private network %s!", cidr_level_size, cgn)
    cidr_range_tree = lowlevel - cgn.prefixlen
    if cidr_range_tree < 1:
        logging.critical("The range (%s) of the calculated CIDR tree size is negative!", cidr_range_tree)
    cidr_tree_first_level = cidr_range_tree % cidr_level_size
    logging.debug("The level size for the first tree split is %s", cidr_tree_first_level)
    if cidr_tree_first_level > 0:
        subnets = cgn.subnets(prefixlen_diff=cidr_tree_first_level)
        i = 0
        for sub in subnets:
            src += "        ip saddr " + str(sub) + " goto " + chain_translation_name(sub) + "\n"
            i += 1
    else:
        src += "        ip saddr " + str(cgn) + " goto " + chain_translation_name(cgn) + "\n"

    src += "    }\n"
    src += "\n"
    cidr_mask = cgn.prefixlen
    depth = 0
    while cidr_mask <= lowlevel:
        for sub in cgn.subnets(prefixlen_diff=cidr_level_size*depth + cidr_tree_first_level):
            src += "    # Depth: " + str(depth) + "\n"
            src += "    chain " + chain_translation_name(sub) + " {\n"
            if cidr_mask + cidr_level_size <= lowlevel:
                for s in sub.subnets(prefixlen_diff=cidr_level_size):
                    src += "        ip saddr " + str(s) + " goto " + chain_translation_name(s) + "\n"
            elif sub in translos.keys():
                for ent in translos[sub]:
                    src += "        " + ent + "\n"
            src += "    }\n"
            src += "\n"
        cidr_mask += cidr_level_size
        depth += 1
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

    # Throttling
    src += "table netdev " + cfg()['netfilter']['throttle']['table'] + " {\n"
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
        src += "        drop\n"
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
    src += "        type filter hook ingress device " + cfg()['cgn']['interface'] + " priority 0;\n"
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
    drop_conntrack(cfg()['cgn']['net'])
    logging.debug("Drop previous configuration and apply new one")
    drop_table_if_exists(cfg()['netfilter']['translation']['table'])
    drop_table_if_exists(cfg()['netfilter']['throttle']['table'])
    # eXecutor!
    subprocess.call(cfg()['netfilter']['nft']['call'] + " -f " +  cfg()['netfilter']['nft']['tmpfile'], shell=True)
    # drop file
    if logging.getLogger().level > logging.DEBUG:
        subprocess.call("/bin/rm " + cfg()['netfilter']['nft']['tmpfile'], shell=True)