from flask import Flask
from lib.ip import *
from lib.snat import *
import configparser
from flask_restful import Api


def conf(self, section='Network', value=''):
    config = configparser.ConfigParser()
    config.read('/home/felix/PycharmProjects/dsnat/dsnat.ini')

    return config.get(section, value)


app = Flask(__name__)
api = Api(app)

api.add_resource(publicIPs, '/ip')
api.add_resource(add_ip, '/ip/add/<ip_addr>')
api.add_resource(remove_ip, '/ip/remove/<ip_addr>')

api.add_resource(addSNAT, '/snat/add')
api.add_resource(removeSNAT, '/snat/remove')

if __name__ == '__main__':
    app.run(debug=True)