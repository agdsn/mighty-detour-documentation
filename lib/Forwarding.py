from ipaddress import IPv4Network
from nft.chains import *
from nft.rules import *

table = "nat"


def chain_forwarding(public_ip):
    return "forwarding-" + str(IPv4Network(str(public_ip)).network_address).replace(".","-")


def add_forwarding(forward):
    logging.info("Create forwarding %s", forward)
    forward_string = forward.protocol + " dport " + forward.source_port + " ip saddr " + forward.public_ip \
                     + " dnat to " + forward.private_ip + ":" + forward.destination_port
    jump_string = "ip saddr " + forward.public_ip + " goto " + chain_forwarding(forward.public_ip)
    if not chain_exists(chain_name=chain_forwarding(forward.public_ip), table=table):
        add_chain(chain=chain_forwarding(forward.public_ip), table=table)
    # Add rule to jump into the private chain
    if not rule_exists(table=table, chain="prerouting", value=jump_string):
        add_rule(table=table, chain="prerouting", rule=jump_string)
    # Add rule inside the private chain

    # TODO: verify ob similar rule exists (same public_ip and public_port)

    if rule_exists(table=table, chain=chain_forwarding(forward.public_ip), value=forward_string):
        logging.debug("A Forwarding for %s:%s (%s) to %s:%s already exists, nothing to do",
             forward.public_ip, forward.source_port,
             forward.protocol, forward.private_ip, forward.destination_port)
    else:
        add_rule(table=table, chain=chain_forwarding(forward.public_ip), rule=forward_string)
        logging.info("A forwarding for %s:%s (%s) to %s:%s has been added",
             forward.public_ip, forward.source_port,
             forward.protocol, forward.private_ip, forward.destination_port)


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
