import subprocess
import logging

from ipaddress import IPv4Network, IPv4Address
from helper.config import cfg
from nft.chains import chain_exists, add_chain, drop_chain
from nft.maps import map_contains_element, add_map_element, delete_map_element
from nft.rules import add_rule


def chain_throttle(ip):
    return "ratelimit-" + str(IPv4Address(ip)).replace(".", "-")


def generate_throttle_map_elements_cgn(throttles):
    logging.debug("Generate throttling map %s entries", cfg()['netfilter']['throttle']['map'] + "_cgn")
    ret = []
    for throttle in throttles:
        ret.append(throttle.translated_net + " : goto " + chain_throttle(throttle.public_ip))
    return ret


def generate_throttle_map_elements_inet(throttles):
    logging.debug("Generate throttling map %s entries", cfg()['netfilter']['throttle']['map'] + "_inet")
    ret = []
    for throttle in throttles:
        ret.append(throttle.public_ip + " : goto " + chain_throttle(throttle.public_ip))
    return ret


def add_throttle(throttle):
    chain_name = chain_throttle(throttle.translated_net)
    logging.info("Add throttling %s", throttle)
    if not chain_exists(chain_name=chain_name, table=cfg()['netfilter']['throttle']['table']):
        add_chain(chain_name, cfg()['netfilter']['throttle']['table'], options="policy drop;")
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
        logging.debug("Throttle %s should be added, but the element %s was already present in the map %s!",
                      throttle, throttle.translated_net, cfg()['netfilter']['throttle']['map'])
    if not map_contains_element(table=cfg()['netfilter']['throttle']['table'],
                                    map=cfg()['netfilter']['throttle']['map'],
                                    element=throttle.public_ip):
        add_map_element(table=cfg()['netfilter']['throttle']['table'],
                            map=cfg()['netfilter']['throttle']['map'],
                            key=throttle.public_ip,
                            value="goto " + chain_name)
    else:
        logging.debug("Throttle %s should be added, but the element %s was already present in the map %s!",
                      throttle, throttle.public_ip, cfg()['netfilter']['throttle']['map'])


def drop_throttle(private_net, public_ip):
    chain_name = chain_throttle(public_ip)
    table_name = cfg()['netfilter']['throttle']['table']
    map_name = cfg()['netfilter']['throttle']['map']
    if chain_exists(chain_name=chain_name, table=table_name):
        drop_chain(chain=chain_name, table=table_name)
    else:
        logging.debug("Throttle should be deleted, but the chain %s was not present in table %s!", chain_name, table_name)
    if map_contains_element(table=table_name, map=map_name, element=private_net):
        delete_map_element(table=table_name, map=map_name, key=private_net)
    else:
        logging.debug("Throttle should be deleted, but the element with key %s was not present in map %s!",
                      private_net, map_name)
    if map_contains_element(table=table_name, map=map_name, element=public_ip):
        delete_map_element(table=table_name, map=map_name, key=public_ip)
    else:
        logging.debug("Throttle should be deleted, but the element with key %s was not present in map %s!",
                      public_ip, map_name)