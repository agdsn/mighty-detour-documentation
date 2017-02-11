from celery import Celery

from subprocess import call


app = Celery('tasks', broker = 'pyamqp://guest@localhost//')


app = Flask(__name__)
api = Api(app)

#call("nft flush table " + conf(section='Netfilter', value='SNATTable'), shell=True)
#call("nft add table " + conf(section='Netfilter', value='SNATTable'), shell=True)
#call("nft add chain " + conf(section='Netfilter', value='SNATTable') + " " + conf(section='Netfilter',value='SNATChain')
#     + " { type nat hook postrouting priority 0 \; }", shell=True)
#call("nft add map " + conf(section='Netfilter', value='SNATTable') + " " + conf(section='Netfilter', value='SNATMap')
#     + " { type ipv4_addr: ipv4_addr\; flags interval \; }", shell=True)
#call("add rule ip " + conf(section='Netfilter', value='SNATTable')
#     + " " + conf(section='Netfilter',value='SNATChain')
#     + " snat ip saddr map @" + conf(section='Netfilter', value='SNATMap') + ";", shell=True)

api.add_resource(network_list, '/networks')
api.add_resource(network_add, '/network/add')
api.add_resource(network_remove, '/network/remove')

if __name__ == '__main__':
    app.run(debuovirtg=True)