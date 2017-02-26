from ipaddress import IPv4Network

from helper.network import is_subnet_of
from nft.rules import *


def chain_translation(priv_net, subnet, preflength):
    preflength = int(preflength)
    path = "postrouting-level-"
    subnets = priv_net.subnets(prefixlen_diff=12 - priv_net.prefixlen)
    current_net = IPv4Network('0.0.0.0/0')
    i = 0
    for sub in subnets:
        if is_subnet_of(subnet,sub):
            path += str(i)
            current_net = sub
            break
        i += 1
    while current_net.prefixlen + preflength < subnet.prefixlen:
        path += "-"
        i = 0
        subnets = current_net.subnets(prefixlen_diff=preflength)
        for sub in subnets:
            if is_subnet_of(subnet,sub):
                path += str(i)
                current_net = sub
                break
            i += 1
    return path


def add_translation(translation, all_privs, preflength):
    logging.debug("Adding translation %s", translation)
    translation_string = "ip saddr " + str(translation.translated_net) \
                        + " snat to " + str(translation.public_ip)
    chain_name = chain_translation(all_privs=all_privs, priv_net=translation.translated_net, preflength=preflength)
    handle = rule_exists(value=translation_string, chain=chain_name, table=cfg()['netfilter']['translation']['table'])
    if not handle:
        logging.debug("The exact translation %s does not yet exist", translation)

        # TODO: handle (e.g. drop) conntrackd state for the private nets

        generic_string = "ip saddr " + str(translation.translated_net)
        handle = rule_exists(value=generic_string, chain=chain_name, table=cfg()['netfilter']['translation']['table'])
        if not handle:
            logging.info("An translation for private net %s does not exist yet", translation.translated_net)
            add_rule(chain=chain_name, table=cfg()['netfilter']['translation']['table'], rule=translation_string)
        else:
            logging.info("An translation for private net %s already exists, replacing it", translation.translated_net)
            replace_rule(handle=handle,
                         rule=translation_string,
                         chain=chain_name,
                         table=cfg()['netfilter']['translation']['table'])
    else:
        logging.info("The translation %s is already present", translation)


def drop_translation(translated_net, all_privs, preflength):
    logging.debug("Deleting translation for private net %s", translated_net)
    chain_name = chain_translation(all_privs=all_privs, priv_net=translated_net, preflength=preflength)
    generic_string = "ip saddr " + str(translated_net)
    handle = rule_exists(value=generic_string, chain=chain_name, table=cfg()['netfilter']['translation']['table'])
    if not handle:
        logging.debug("There is no translation present for private net %s", translated_net)
    else:

        # TODO: drop conntrackd state

        drop_rule(handle=handle, chain=chain_name, table=cfg()['netfilter']['translation']['table'])

