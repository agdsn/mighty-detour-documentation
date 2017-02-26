import subprocess
import logging
from ipaddress import IPv4Network
from helper.config import cfg

map_throttle = cfg()['netfilter']['throttle']['map']
table_throttle = cfg()['netfilter']['throttle']['table']
nftCall = cfg()['netfilter']['nft']['call']


def chain_throttle(translated_net):
    return "ratelimit-" + str(IPv4Network(translated_net).network_address).replace(".", "-")


def generate_throttle(throttle):
    chain_name = chain_throttle(throttle.translated_net)
    logging.info("Add throttling %s", throttle)
    src = "add chain " + table_throttle + " " + chain_name + "\n"
    src += "add element " + table_throttle + " " + map_throttle + " { " + str(throttle.translated_net)
    src += " : goto " + chain_name + " }\n"
    src += "add rule " + table_throttle + " " + chain_name + " limit rate " + str(throttle.speed)
    src += " kbytes/second accept\n"

    return src


def update_throttle(throttle):
    logging.critical("Not implemented yet!")


def drop_throttle(translated_net):
    logging.info("Drop throttling for private net %s", translated_net)

    command = nftCall + " list map " + table_throttle + " " + map_throttle + " -a | /bin/grep " + str(translated_net)
    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)\
        .decode("utf-8").replace("\\t", "").replace("\\n", "").splitlines()
    if len(output) > 1:
        logging.warning("The throttling subnet %s is present multiple times!", translated_net)
        for o in output:
            parsed_handle = o.split(" # handle ")
            parsed_destination = parsed_handle[0].split(" to ")
            logging.warning("It is already mapped to %s", parsed_destination[1])

    logging.debug("Command output: " + output[0])

    # TODO: if possible (ask netfilter-dev!), implement simgle entry drop

    command = nftCall + " flush chain " + chain_throttle(translated_net)
    subprocess.call(command, shell=True)
    command = nftCall + " delete chain " + chain_throttle(translated_net)
    subprocess.call(command, shell=True)