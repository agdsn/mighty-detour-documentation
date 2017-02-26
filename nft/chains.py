import subprocess
import logging
from helper.config import cfg

nftCall = cfg()['netfilter']['nft']['call']


def chain_exists(chain_name, table):
    command = nftCall + " list chains " + table + " " + str(chain_name) + " | /bin/grep " + str(chain_name)
    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT).decode("utf-8").replace("\\t", "").replace("\\n", "").splitlines()
    if len(output) == 0:
        logging.debug("The chain %s is not present", str(chain_name))
        return False
    elif len(output) == 1:
        logging.debug("The chain %s is present", str(chain_name))
        return True
    else:
        logging.warning("The forwarding chain %s is present multiple times!", chain_name)
        for o in output:
            logging.warning("Occurance: %s", o)
        return True


def add_chain(chain, table):
    command = nftCall + " add chain " + table + " " + str(chain)
    subprocess.call(command, shell=True)
    logging.debug("The chain %s in table %s has been created", chain, table)


def chain_rulecount(chain, table):
    command = nftCall + " list chain " + table + " " + chain
    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT).decode("utf-8").replace("\\t", "").replace("\\n", "").splitlines()
    logging.debug("The chain %s in table %s contains %s rules", chain, table, len(output))
    return len(output)


def drop_chain(chain, table):
    command = nftCall + " flush chain " + table + " " + chain
    subprocess.call(command, shell=True)
    command = nftCall + " delete chain " + table + " " + chain
    subprocess.call(command, shell=True)
    logging.debug("The chain %s in table %s has been deleted", chain, table)