from ipaddress import IPv4Network

from helper.conntrack import drop_conntrack
from nft.rules import *


def chain_translation(subnet):
    return "postrouting-" + str(IPv4Network(subnet).supernet(new_prefix=cfg()['netfilter']['tree']['lowlevel'])).replace(".", "-").replace("/", "-")


def add_translation(translation):
    logging.debug("Adding translation %s", translation)
    translation_string = "ip saddr " + str(translation.translated_net) \
                        + " snat to " + str(translation.public_ip)
    chain_name = chain_translation(subnet=translation.translated_net)
    handle = rule_exists(value=translation_string, chain=chain_name, table=cfg()['netfilter']['translation']['table'])
    if not handle:
        logging.debug("The exact translation %s does not yet exist", translation)
        drop_conntrack(translation.translated_net)

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


def drop_translation(translated_net):
    logging.debug("Deleting translation for private net %s", translated_net)
    chain_name = chain_translation(subnet=translated_net)
    generic_string = "ip saddr " + str(translated_net)
    handle = rule_exists(value=generic_string, chain=chain_name, table=cfg()['netfilter']['translation']['table'])
    if not handle:
        logging.debug("There is no translation present for private net %s", translated_net)
    else:
        drop_conntrack(translated_net)
        drop_rule(handle=handle, chain=chain_name, table=cfg()['netfilter']['translation']['table'])

