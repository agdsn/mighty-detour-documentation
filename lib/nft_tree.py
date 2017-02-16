from ipaddress import IPv4Network, IPv4Address
import subprocess
import logging

nftCall = "/usr/local/sbin/nft"
nftPreamble = "#!/usr/local/sbin/nft"
table = "nat"
table_throttle = "filter"
tmpFile = "/tmp/nft.rules"
maxLevel = 3


def is_subnet_of(a, b):
    a_len = a.prefixlen
    b_len = b.prefixlen
    return a_len >= b_len and a.supernet(a_len - b_len) == b


def calculate_chain_name(priv_net, subnet, preflength):
    preflength = int(preflength)
    path = "postrouting-level-"
    subnets = priv_net.subnets(prefixlen_diff=12 - priv_net.prefixlen)
    current_net = IPv4Network('0.0.0.0/0')
    i = 0
    for sub in subnets:
        if is_subnet_of(subnet,sub):
            path += str(i)
            current_net = sub
            break
        i += 1
    while current_net.prefixlen + preflength < subnet.prefixlen:
        path += "-"
        i = 0
        subnets = current_net.subnets(prefixlen_diff=preflength)
        for sub in subnets:
            if is_subnet_of(subnet,sub):
                path += str(i)
                current_net = sub
                break
            i += 1
    return path


def update_single_mapping(private_net, public_ip, all_privs, preflength):
    logging.info("Should update a single mapping (private: %s, public: %s)", private_net, public_ip)
    command = nftCall + " list table " + table + " -a | /bin/grep " + str(private_net)
    logging.debug("Execute: " + command)
    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT).decode("utf-8").replace("\\t", "").replace("\\n", "").splitlines()
    if len(output) > 1:
        logging.warning("The private subnet %s is present multiple times!", private_net)
        for o in output:
            parsed_handle = o.split(" # handle ")
            parsed_destination = parsed_handle[0].split(" to ")
            logging.warning("It is already mapped to %s", parsed_destination[1])

    logging.debug("Command output: " + output[0])
    if "handle" in output[0]:
        # private net already mapped to something

        # TODO: delete existing conntrackd-state

        parsed_handle = output[0].split(" # handle ")
        parsed_destination = parsed_handle[0].split(" to ")

        if IPv4Address(parsed_destination[1]) == public_ip:
            logging.info("The new public_ip %s is already configured!", public_ip)
        else:
            logging.debug("Going to replace the current public ip %s with %s for private subnet %s", parsed_destination[1], public_ip, private_net)
            command = nftCall + " replace rule " + table + " " \
                        + calculate_chain_name(all_privs, private_net, preflength) \
                        + " handle " + parsed_handle[1] + " ip saddr " + str(private_net) \
                        + " snat to " + str(public_ip)
            logging.debug("Execute: " + command)
            subprocess.call(command, shell=True)
    else:
        # private net not yet mapped
        logging.debug("Going to add new public ip %s for private subnet %s", public_ip, private_net)
        command = nftCall + " add rule " + table + " " \
                        + calculate_chain_name(all_privs, private_net, preflength) \
                        + " ip saddr " + str(private_net) \
                        + " snat to " + str(public_ip)
        logging.debug("Execute: " + command)
        subprocess.call(command, shell=True)


def createLevel(net, pref, level, preflength, translations):
    if level >= maxLevel:
        return createLeafs(net, pref, preflength=preflength, translations=translations)

    subnets = net.subnets(prefixlen_diff=preflength)

    src = ""

    i = 0
    for sub in subnets:
        newPref = pref + "-" + str(i)
        src += "add chain " + table + " " + newPref + "\n"
        src += "add rule " + table + " " + pref + " ip saddr " + str(sub) + " goto " + newPref + "\n"
        src += createLevel(sub, newPref, level + 1, translations=translations, preflength=preflength) + "\n"
        i += 1;

    return src


def createLeafs(net, prefix, preflength, translations):
    subnets = net.subnets(prefixlen_diff=preflength)
    src = ""
    for sub in subnets:
        if sub in translations:
            # only add rule if translation is present
            src += "add rule " + table + " " + prefix + " ip saddr " + str(sub) + " snat " + str(translations[sub]) + "\n"

    return src


def initialize(private_net, translations, throttles, preflength=3):
    logging.debug("Begin generating initial nft configuration")
    src = nftPreamble + "\n"
    src += "\n"

    # SNAT configuration
    src += "add table " + table + "\n"
    src += "add chain " + table + " prerouting { type nat hook prerouting priority 0 ;}\n"
    src += "add chain " + table + " postrouting { type nat hook postrouting priority 0 ;}\n"
    src += "add rule " + table + " postrouting meta nftrace set 1\n"

    if private_net.prefixlen < 12:
        subnets = private_net.subnets(prefixlen_diff=12 - private_net.prefixlen)
        i = 0
        for sub in subnets:
            src += "add chain " + table + " postrouting-level-" + str(i) + "\n"
            src += "add rule " + table + " postrouting ip saddr " + str(sub) + " goto postrouting-level-" + str(i) + "\n"
            src += createLevel(sub, "postrouting-level-" + str(i), 0, translations=translations, preflength=preflength) + "\n"
            i += 1
    else:
        src += "add chain " + table + " postrouting-level-0\n"
        src += createLevel(private_net, "postrouting-level-0", 0, translations=translations) + "\n"
        src += "add rule " + table + " postrouting ip saddr " + str(private_net) + " goto postrouting-level-0\n"
    src += "\n"

    # Throttling
    src += "add table " + table_throttle + "\n"
    src += "add chain " + table_throttle + " ratelimit { type filter hook forward priority 0; }\n"
    src += "add map " + table_throttle + " iptoverdict { type ipv4_addr: verdict ; flags interval;}\n"
    src += "add rule ip " + table_throttle + " ratelimit ip saddr vmap @iptoverdict;\n"
    src += "\n"
    for throttle in throttles:
        src += add_throttle(throttle)
    logging.debug("End generation initial nft configuration")

    # write stuff to tmpFile
    logging.debug("Write initial nft configuration to file: " + tmpFile)
    file = open(tmpFile, 'w')
    file.write(src)
    file.close()

    # drop previous content
    logging.debug("Drop previous configuration and apply new one")
    subprocess.call(nftCall + " delete table " + table, shell=True)
    subprocess.call(nftCall + " delete table " + table_throttle, shell=True)
    # eXecutor!
    subprocess.call(nftCall + " -f " +  tmpFile, shell=True)
    # drop file
    #subprocess.call("/bin/rm " + tmpFile, shell=True)


def add_throttle(throttle):
    logging.info("Add throttling rule for private subnet %s with speed %s kbytes/sec",
                 throttle.translated_net, throttle.speed)
    chain_name = str(IPv4Network(throttle.translated_net).network_address).replace(".","-")
    src = "add chain " + table_throttle + " ratelimit-" + chain_name + "\n"
    src += "add element " + table_throttle + " iptoverdict { " + str(throttle.translated_net) + " : goto " + " ratelimit-" + chain_name + " }\n"
    src += "add rule " + table_throttle + " ratelimit-" + chain_name + " limit rate " + str(throttle.speed) + " kbytes/second accept\n"

    return src


def update_throttle(throttle):
    logging.critical("Not implemented yet!")


def generateSingleDNAT():
    print('#!/usr/sbin/nft')
    src = "add chain " + table + " postrouting { type nat hook postrouting priority 100 ;}"
    src += "add chain " + table + " prerouting { type nat hook prerouting priority 0 ;}"
    src += "add rule nat prerouting ip daddr 192.168.0.10 tcp dport 9999 dnat 100.64.1.1"