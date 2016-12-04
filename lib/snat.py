from flask import request
from subprocess import call
from flask_restful import Resource
from dsnat import conf
from ipaddress import ip_address,ip_network

class addSNAT(Resource):
    def get(self):
        post_data = request.get_json(force=True)

        source_net = ip_network(post_data['source'])
        destination_ip = ip_address(post_data['destination'])

        call("nft add element "
             + conf('Netfilter','SNATTable')
             + " "
             +  conf('Netfilter','SNATMap')
             + " { "
             + source_net
             + " : "
             + destination_ip
             + " }", shell=True)

        return {'message': 'External address ' + destination_ip + ' with internal network ' + source_net + ' has been added.'}


class removeSNAT(Resource):
    def get(self):
        post_data = request.get_json(force=True)

        source_net = ip_network(post_data['source'])

        call("nft delete element "
             + conf('Netfilter','SNATTable')
             + " "
             +  conf('Netfilter','SNATMap')
             + " { "
             + source_net
             + " }", shell=True)

        return {'message': 'Internal network ' + source_net + ' has been removed.'}