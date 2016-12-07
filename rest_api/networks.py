from flask_restful import Resource, fields, marshal, reqparse
from lib import ip,snat

class network_list(Resource):
    def get(self):
        resource_fields = {'interface': fields.String, 'ips': fields.List(fields.String)}

        return marshal(ip.get_ips(), resource_fields)


class network_add(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        #parser.add_argument('rate', type=int, help='Rate cannot be converted')
        parser.add_argument('source')
        parser.add_argument('destination')
        args = parser.parse_args()

        ip.add_ip(args['destination'])
        return snat.snat_add(source=args['source'], destination=args['destination'])


class network_remove(Resource):
    def get(self, net_addr, ip_addr):
        ip.remove_ip(ip_addr)
        return snat.snat_remove(source=net_addr)