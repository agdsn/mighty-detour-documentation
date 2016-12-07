from subprocess import check_call, CalledProcessError
#from dsnat import conf
from ipaddress import ip_address,ip_network
import configparser

def conf(section='Network', value=''):
    config = configparser.ConfigParser()
    config.read('/home/felix/PycharmProjects/dsnat/dsnat.ini')

    return config.get(section, value)

def snat_add(source, destination):

    source_net = ip_network(source)
    destination_ip = ip_address(destination)

    command = "nft add element " + \
          conf('Netfilter','SNATTable') + \
          " " + \
           conf('Netfilter','SNATMap') + \
          " { " + \
          str(source_net) + \
          " : " + \
          str(destination_ip) + \
          " }"

    print(command)

    try:
        check_call(command, shell=True)
    except CalledProcessError as e:
        print("   Code: " + str(e.returncode))
        print("   Message: " + str(e))


    return {'message': '[SNAT] External address ' + str(destination_ip) + ' with internal network ' + str(source_net) + ' has been added.'}


def snat_remove(source):

    source_net = ip_network(source)

    check_call("nft delete element "
         + conf('Netfilter','SNATTable')
         + " "
         +  conf('Netfilter','SNATMap')
         + " { "
         + source_net
         + " }", shell=True)

    return {'message': '[SNAT] Internal network ' + source_net + ' has been removed.'}