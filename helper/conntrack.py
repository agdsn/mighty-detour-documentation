import logging
import subprocess

from helper.config import cfg


def drop_conntrack(ip):
    command = cfg()['conntrack']['call'] + " -D -s " + str(ip)
    subprocess.call(command, shell=True)
    logging.info("The conntrack state for %s has been dropped", ip)