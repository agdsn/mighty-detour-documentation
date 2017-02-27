import subprocess
import logging

from helper.config import cfg


def add_rule(rule, chain, table):
    command = cfg()['netfilter']['nft']['call'] + " add rule " + table + " " + chain + " " + rule
    subprocess.call(command, shell=True)
    logging.debug("The rule %s has been added to table %s chain %s", rule, table, chain)


def replace_rule(handle, rule, chain, table):
    command = cfg()['netfilter']['nft']['call'] + " replace rule " + table + " " + chain + " handle " + handle + " " + rule
    subprocess.call(command, shell=True)
    logging.debug("The rule with handle %s has been replaced with %s at table %s chain %s", handle, rule, table, chain)


def drop_rule(handle, chain, table):
    command = cfg()['netfilter']['nft']['call'] + " delete rule " + table + " " + chain + " handle " + str(handle)
    subprocess.call(command, shell=True)
    logging.debug("The rule with handle %s has been deleted from table %s chain %s", handle, table, chain)


# This returns False, if the rule does not exist. Otherwise, the handle is returned
# The first rule matching the expression will be used
def rule_exists(value, table, chain=None):
    logging.debug("Check if a rule in table %s chain %s contains %s", table, chain, value)
    if chain is None:
        logging.debug("No chain specified, searching in whole nft table %s", table)
        command = cfg()['netfilter']['nft']['call'] + " list table " + table + " -a -nnn | /bin/grep '" + str(value) + "'"
    else:
        command = cfg()['netfilter']['nft']['call'] + " list chain " + table + " " + chain + " -a -nnn | /bin/grep '" + str(value) + "'"
    logging.debug("Execute: " + command)
    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT).decode("utf-8").replace("\\t", "").replace("\\n", "").splitlines()
    if len(output) > 1:
        logging.warning("There are multiple rules present in table %s chain %s that contain %s", table, chain, value)
        for o in output:
            logging.warning("Rule: %s", o)
    elif len(output) == 0:
        logging.debug("There is no rule that contains %s in table %s chain %s", value, table, chain)
        return False
    if "handle" not in output[0]:
        logging.warning("There is no handle for %s in table %s chain %s in the first matched output line", value, table, chain)
        return False
    parsed_handle = output[0].split(" # handle ")
    # Return the handle number
    logging.debug("The handle for the rule that contains %s in table %s chain %s is %s",
                  value, table, chain, parsed_handle[1])
    return int(parsed_handle[1])