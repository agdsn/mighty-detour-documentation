from ipaddress import IPv4Network
from nft.chains import *
from nft.rules import *

table = "nat"


def chain_forwarding(public_ip):
    return "forwarding-" + str(IPv4Network(str(public_ip)).network_address).replace(".","-")


def generate_forwardings(forwards):
    src = ""
    chains = []
    for forward in forwards:
        if forward.public_ip not in chains:
            src += "add chain " + table + " " + chain_forwarding(forward.public_ip) + "\n"
            chains.append(forward.public_ip)
            src += "add rule " + table + " prerouting ip saddr " + str(forward.public_ip) + " goto chain_forwarding(forward.public_ip)\n"
        src += "add rule " + table + " " + chain_forwarding(forward.public_ip) + " " + str(forward.protocol) + " "
        src += "dport  " + str(forward.source_port) + " ip saddr " + str(forward.public_ip) + " "
        src += "dnat to " + str(forward.private_ip) + ":" + str(forward.destination_port) + "\n"
    return src


def add_forwarding(forward):
    logging.info("Create forwarding %s", forward)
    chain_name = chain_forwarding(forward.public_ip)
    forward_string = str(forward.protocol) + " dport " + str(forward.source_port) + " ip saddr " + str(forward.public_ip) \
                     + " dnat to " + str(forward.private_ip) + ":" + str(forward.destination_port)
    jump_string = "ip saddr " + str(forward.public_ip) + " goto " + chain_name
    if not chain_exists(chain_name=chain_name, table=table):
        add_chain(chain=chain_name, table=table)
    # Add rule to jump into the private chain
    if not rule_exists(table=table, chain="prerouting", value=jump_string):
        add_rule(table=table, chain="prerouting", rule=jump_string)
    # Add rule inside the private chain
    if rule_exists(table=table, chain=chain_name, value=forward_string):
        logging.debug("Forwarding %s already existed", forward)
    else:
        # Verify if an similar rule already exists (same public_ip, public_port and protocol)
        generic_string = forward.protocol + " dport " + str(forward.source_port) + " ip saddr " + str(forward.public_ip)
        handle = rule_exists(table=table, chain=chain_name, value=generic_string)
        if not handle:
            add_rule(table=table, chain=chain_name, rule=forward_string)
            logging.info("Added forwarding %s", forward)
        else:
            replace_rule(handle=handle, rule=forward_string, chain=chain_name, table=table)
            logging.info("Updated forwarding %s with previous rule handle %s", forward, handle)


def drop_forwarding(forward):
    logging.info("Drop forwarding %s", forward)
    forward_string = forward.protocol + " dport " + forward.source_port + " ip saddr " + forward.public_ip \
                     + " dnat to " + forward.private_ip + ":" + forward.destination_port
    jump_string = "ip saddr " + forward.public_ip + " goto " + chain_forwarding(forward.public_ip)
    if chain_exists(chain_name=chain_forwarding(forward.public_ip), table=table):
        # look at the number of rules in the user chain
        count = chain_rulecount(chain_name=chain_forwarding(forward.public_ip), table=table)
        if count == 0:
            logging.warning("The chain %s in table %s was empty, but a forward was expected: %s", table, chain_exists(table=table, chain_name=chain_forwarding(forward.public_ip)), forward)
        elif count == 1:
            drop_chain(chain=chain_forwarding(forward.public_ip), table=table)
        else:
            drop_rule(rule_exists(table=table, chain=chain_forwarding(forward.public_ip), value=forward_string))
    else:
        logging.info("The public ip chain %s for the forwarding %s was not deleted because it does not exist", chain_forwarding(forward.public_ip), forward)


def drop_all_forwardings(public_ip):
    logging.debug("Dropping all forwardings for %s", public_ip)
    chain_name = chain_forwarding(public_ip)
    if chain_exists(chain_name=chain_forwarding(public_ip), table=table):
        drop_chain(table=table, chain=chain_name)
        logging.info("All forwardings for %s dropped", public_ip)
    else:
        logging.debug("No forwardings for %s dropped, because none existed", public_ip)
