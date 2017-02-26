import subprocess
import logging

from ipaddress import IPv4Network
from helper.config import cfg
from nft.chains import chain_exists, add_chain, drop_chain
from nft.maps import map_contains_element, add_map_element, delete_map_element
from nft.rules import add_rule


def chain_throttle(translated_net):
    return "ratelimit-" + str(IPv4Network(translated_net).network_address).replace(".", "-")


def generate_throttle(throttle):
    chain_name = chain_throttle(throttle.translated_net)
    logging.info("Add throttling %s", throttle)
    src = "add chain " + cfg()['netfilter']['throttle']['table'] + " " + chain_name + "\n"
    src += "add element " + cfg()['netfilter']['throttle']['table'] + " " + cfg()['netfilter']['throttle']['map'] + " { " + str(throttle.translated_net)
    src += " : goto " + chain_name + " }\n"
    src += "add rule " + cfg()['netfilter']['throttle']['table'] + " " + chain_name + " limit rate " + str(throttle.speed)
    src += " kbytes/second accept\n"

    return src


def update_throttle(throttle):
    logging.critical("Not implemented yet!")


def add_throttle(throttle):
    chain_name = chain_throttle(throttle.translated_net)
    logging.info("Add throttling %s", throttle)
    if not chain_exists(chain_name=chain_name, table=cfg()['netfilter']['throttle']['table']):
        add_chain(chain_name, cfg()['netfilter']['throttle']['table'])
        add_rule(table=cfg()['netfilter']['throttle']['table'],
                 chain=chain_name,
                 rule="limit rate " + str(throttle.speed) + " kbytes/second accept")
    else:
        logging.debug("Throttle %s should be added, but the chain %s was already present!", throttle, chain_name)
    if not map_contains_element(table=cfg()['netfilter']['throttle']['table'],
                            map=cfg()['netfilter']['throttle']['map'],
                            element=throttle.translated_net):
        add_map_element(table=cfg()['netfilter']['throttle']['table'],
                            map=cfg()['netfilter']['throttle']['map'],
                            key=throttle.translated_net,
                            value="goto " + chain_name)
    else:
        logging.debug("Throttle %s should be added, but the element was already present in the map %s!", throttle, cfg()['netfilter']['throttle']['map'])


def drop_throttle(throttle):
    chain_name = chain_throttle(throttle.translated_net)
    table_name = cfg()['netfilter']['throttle']['table']
    map_name = cfg()['netfilter']['throttle']['map']
    if chain_exists(chain_name=chain_name, table=table_name):
        drop_chain(chain=chain_name, table=table_name)
    else:
        logging.debug("Throttle %s should be deleted, but the chain %s was not present in table %s!", chain_name, table_name)
    if map_contains_element(table=table_name, map=map_name, element=throttle.translated_net):
        delete_map_element(table=table_name, map=map_name, key=throttle.translated_net)
    else:
        logging.debug("Throttle %s should be deleted, but the element with key %s was not present in map %s!", throttle.translated_net, map_name)