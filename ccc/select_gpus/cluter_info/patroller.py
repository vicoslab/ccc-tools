import json
import re
from urllib import request

from collections import OrderedDict as OrderedDict

from . import ClusterInfo

def get_url_request(url):
    # if host URL contains password then extract password and username, and remove it from the URL (make sure to retain http or https)
    if "@" in url:
        username = url.split("//")[1].split(":")[0]
        password = url.split("//")[1].split(":")[1].split("@")[0]
        url = url.split("//")[0] + "//" + url.split("//")[1].split("@")[1]

        passman = request.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, username, password)
        authhandler = request.HTTPBasicAuthHandler(passman)
        opener = request.build_opener(authhandler)
        request.install_opener(opener)

        return request.urlopen(url)
    else:
        return request.urlopen(url)

def parse_host_whitelist(host):
    match = re.search(r'\(([^)]+)\)', host)
    if match:
        host_ids = match.group(1).split('+') # get ids
        host = host[:host.index("(")] # name
    else:
        host_ids = []
    
    return host, list(map(int,host_ids))

class PatrollerClusterInfo(ClusterInfo):

    def __init__(self, cluster_info,):
        with open(cluster_info) as f:
            self.cluster_info = json.load(f)


    def get_host_status(self, host="claims", hostname="localhost"):
        try:
            status = json.loads(get_url_request(f"{host}/status").read())
            devices = json.loads(get_url_request(f"{host}/devices").read())

            for gpus in status.keys():
                status[gpus]["device"] = devices[gpus]
                status[gpus]["host"] = hostname

            return status
        except:
            return {}


    def get_cluster_status(self, only_hosts=None, ignore_hosts=()):

        cluster_status = OrderedDict()

        host_list = self.cluster_info['host_priority'] if only_hosts is None else only_hosts

        ignore_hosts_with_ids = dict()
        for host in ignore_hosts:
            host,host_ids = parse_host_whitelist(host)
            ignore_hosts_with_ids[host] = host_ids

        for host in host_list:
            # extract gpu id if specificed at the end of hostname, e.g., host values can be ['crushinator(2+3+4+5+6+7+8+9)', 'morbo(2+3)', 'donbot']
            host,host_ids = parse_host_whitelist(host)
            
            # skip hosts in ignore_hosts list (ones without explicit gpu ids)
            ignore_host_ids = ignore_hosts_with_ids[host] if host in ignore_hosts_with_ids else []
            if host in ignore_hosts_with_ids and len(ignore_host_ids) == 0:
                continue

            status = self.get_host_status(self.cluster_info['hosts'][host], host)
            status = OrderedDict(status)

            # retain only gpus in host_ids and ones not in ignore_host_ids
            if len(host_ids) > 0:
                status = {gpu_id:stat  for gpu_id,stat in status.items() if stat['device']['number'] in host_ids}
            if len(ignore_host_ids) > 0:
                status = {gpu_id:stat  for gpu_id,stat in status.items() if stat['device']['number'] not in ignore_host_ids}

            # sort OrderedDict based on claim.age
            status = OrderedDict(sorted(status.items(), key=lambda x: x[1]["claim"]["age"], reverse=True))

            cluster_status.update(status)

        return cluster_status