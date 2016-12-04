from flask_restful import Resource, fields, marshal
from pyroute2 import IPRoute, NetlinkError
from dsnat import conf

class publicIPs(Resource):
    def get(self):
        ip = IPRoute()
        ips = []
        print(ip.get_addr(label=conf('ExternalInterface')))
        for ad in ip.get_addr(label=conf('ExternalInterface')):
            ips.append(ad['attrs'][0][1])

        resource_fields = {'interface': fields.String, 'ips': fields.List(fields.String)}
        data = {'interface': conf('ExternalInterface'), 'ips': ips}
        return marshal(data, resource_fields)

class add_ip(Resource):
    def get(self, ip_addr):
        ip = IPRoute()
        dev = ip.link_lookup(ifname=conf('ExternalInterface'))[0]
        try:
            ip.addr('add', index=dev,
                 address=ip_addr, mask=24)
        except NetlinkError as e:
            if e.code == 17:
                return {
                    'error': 'Ip address ' + ip_addr + ' could not be added: the address is already assigned to the interface!'}
            else:
                return {'error': e}
        else:
            return {'message': 'Ip address ' + ip_addr + ' has been added.'}

class remove_ip(Resource):
    def get(self, ip_addr):
        ip = IPRoute()
        dev = ip.link_lookup(ifname=conf('ExternalInterface'))[0]
        try:
            ip.flush_addr(address=ip_addr)
        except NetlinkError as e:
            if e.code == 99:
                return {'error': 'Ip address ' + ip_addr + ' could not be removed: the address was not assigned to the interface!'}
            else:
                return {'error': e}
        else:
            return {'message': 'Ip address ' + ip_addr + ' has been removed.'}
