from pyroute2 import IPRoute, NetlinkError
#from dsnat import conf
import configparser

def conf(section='Network', value=''):
    config = configparser.ConfigParser()
    config.read('/home/felix/PycharmProjects/dsnat/dsnat.ini')
    return config.get(section, value)

def get_ips():
        ip = IPRoute()
        ips = []
        for ad in ip.get_addr(label=conf(section='Network',value='ExternalInterface')):
            ips.append(ad['attrs'][0][1])
        return {'interface': conf(section='Network',value='ExternalInterface'), 'ips': ips}


def add_ip(ip_addr):
    ip = IPRoute()
    dev = ip.link_lookup(ifname=conf(section='Network',value='ExternalInterface'))[0]
    try:
           ip.addr('add', index=dev, address=ip_addr, mask=24)
    except NetlinkError as e:
        if e.code == 17:
            return {
                'error': '[IP] Ip address ' + ip_addr + ' could not be added: the address is already assigned to the interface!'}
        else:
            return {'error': e}
    else:
        return {'message': '[IP] Ip address ' + ip_addr + ' has been added.'}

def remove_ip(ip_addr):
    ip = IPRoute()
    dev = ip.link_lookup(ifname=conf(section='Network',value='ExternalInterface'))[0]
    try:
        ip.flush_addr(address=ip_addr)
    except NetlinkError as e:
        if e.code == 99:
            return {'error': '[IP] Ip address ' + ip_addr + ' could not be removed: the address was not assigned to the interface!'}
        else:
            return {'error': e}
    else:
        return {'message': '[IP] Ip address ' + ip_addr + ' has been removed.'}
