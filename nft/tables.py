import subprocess
import logging

nftCall = "/usr/local/sbin/nft"


def drop_table_if_exists(tab):
    logging.debug("Drop table %s if it exists", tab)
    command = nftCall + " list tables"
    output = subprocess.check_output(command, shell=True).decode("utf-8")
    if tab in output:
        command = nftCall + " delete table " + tab
        subprocess.call(command, shell=True)
        logging.info("Table %s has been dropped", tab)
    else:
        logging.debug("Table %s has not been dropped since it does not exist" , tab)