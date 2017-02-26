import subprocess
import logging

from helper.config import cfg


def map_contains_element(element, map, table):
    command = cfg()['netfilter']['nft']['call'] + " list map " + table + " " + map + " | /bin/grep " + str(element)
    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)\
        .decode("utf-8").replace("\\t", "").replace("\\n", "").splitlines()
    if len(output) == 0:
        logging.debug("The element %s is not present in map %s", element, map)
        return False
    elif len(output) == 1:
        logging.debug("The element %s is present in map %s", element, map)
        return True
    else:
        logging.warning("The element %s is present multiple times in map %s!", element, map)
        for o in output:
            logging.warning("Occurance: %s", o)
        return True


def add_map_element(table, map, key, value):
    command = cfg()['netfilter']['nft']['call'] + " add element" + table + " " + map + " { " + str(key) + " : " + str(value) + " } "
    subprocess.call(command, shell=True)
    logging.debug("The element %s with value %s has been added to map %s in table %s", key, value, map, table)


def delete_map_element(table, map, key):
    command = cfg()['netfilter']['nft']['call'] + " delete element" + table + " " + map + " " + str(key)
    subprocess.call(command, shell=True)
    logging.debug("The element %s has been deleted from map %s in table %s", key, map, table)