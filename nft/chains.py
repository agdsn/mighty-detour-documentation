import subprocess
import logging

from helper.config import cfg


def chain_exists(chain_name, table):
    command = cfg()['netfilter']['nft']['call'] + " list table " + table
    output = subprocess.check_output(command, shell=True)\
        .decode("utf-8").replace("\\t", "").replace("\\n", "").splitlines()
    output_matched = []
    for l in output:
        if "chain " + str(chain_name) in l:
            output_matched.append(l.strip())
    if len(output_matched) == 0:
        logging.debug("The chain %s is not present", str(chain_name))
        return False
    elif len(output_matched) == 1:
        logging.debug("The chain %s is present", str(chain_name))
        return True
    else:
        logging.warning("The forwarding chain %s is present multiple times!", chain_name)
        for o in output_matched:
            logging.warning("Occurance: %s", o)
        return True


def add_chain(chain, table):
    command = cfg()['netfilter']['nft']['call'] + " add chain " + table + " " + str(chain)
    subprocess.call(command, shell=True)
    logging.debug("The chain %s in table %s has been created", chain, table)


def chain_rulecount(chain, table):
    command = cfg()['netfilter']['nft']['call'] + " list chain " + table + " " + chain
    logging.debug("Execute: " + command)
    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)\
        .decode("utf-8").replace("\\t", "").replace("\\n", "").splitlines()
    logging.debug("The chain %s in table %s contains %s rules", chain, table, len(output))
    return len(output)


def drop_chain(chain, table):
    #command = cfg()['netfilter']['nft']['call'] + " flush chain " + table + " " + chain
    #logging.debug("Execute: " + command)
    #subprocess.call(command, shell=True)
    #command = cfg()['netfilter']['nft']['call'] + " delete chain " + table + " " + chain
    #logging.debug("Execute: " + command)
    #subprocess.call(command, shell=True)
    logging.debug("The chain %s in table %s has neither been flushed nor deleted, but this should not be a problem", chain, table)