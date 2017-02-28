import ipaddress
from subprocess import call


IP = ipaddress.ip_address('192.168.30.0')

dest_ips = ""
for i in range(8900):
		dest_ips += str(IP) + " "
		IP += 1

SRC_IP = ipaddress.ip_address("100.64.0.10")

call("date", shell=True)

for i in range(30):
		call("nping -c 0 --tcp --interface eth1 -S " + str(SRC_IP) + " -g " + str(5000 + i) + " --rate 6000 " + dest_ips + ">> /dev/null &", shell=True)
		SRC_IP += 256

