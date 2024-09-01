#!/usr/bin/env python3
# steven@makeitwork.cloud
# GitHub URL
# https://blog.cloudflare.com/python-cloudflare/

import socket
import CloudFlare
import sys
import yaml
import subprocess

print("Getting SOPS encrypted values from sops_vars.yaml ...")
r = subprocess.run(['sops', 'decrypt', 'sops_vars.yaml'], stdout = subprocess.PIPE)
sops_vars = yaml.safe_load(r.stdout.decode('utf-8'))

print("Using local IP address " + socket.gethostbyname(socket.gethostname() + '.local') + " ...")

print("Setting CloudFlare access info...")
cf = CloudFlare.CloudFlare(token = sops_vars['cf_token'])

print("Getting CloudFlare DNS Zone ID and Name...")
zone_id = cf.zones.get(params={'per_page':'1', 'name':sops_vars['cf_domain_name']})[0]['id']
zone_name = cf.zones.get(params={'per_page':'1', 'name':sops_vars['cf_domain_name']})[0]['name']

print("Attempting to get existing DNS record for " + socket.gethostname() + "." + sops_vars['cf_domain_name'] + " ...")
try:
    dns_id = cf.zones.dns_records.get(zone_id, params={'name':socket.gethostname() + '.' + zone_name, 'match':'all', 'type':'A'})[0]['id']
except:
    print("Creating new record for " + socket.gethostname() + "." + sops_vars['cf_domain_name'] + " ...")
    try:
        cf.zones.dns_records.post(zone_id, data={'name':socket.gethostname(), 'type':'A', 'content':socket.gethostbyname(socket.gethostname())})
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        sys.exit('/zones.dns_records.post %s - %d %s' % (e, e, e))
    sys.exit()

print("Getting IP address for existing record...")
dns_content = cf.zones.dns_records.get(zone_id, params={'name':socket.gethostname() + '.' + zone_name, 'match':'all', 'type':'A'})[0]['content']


print("Evaluating if existing record matches current IP address...")
if dns_content == socket.gethostbyname(socket.gethostname() + '.local'):
    print("Record matches, exiting...")
    sys.exit()

print("Deleting existing record...")
cf.zones.dns_records.delete(zone_id, dns_id)

print("Creating new record for " + socket.gethostname() + "." + sops_vars['cf_domain_name'] + " ...")
try:
    cf.zones.dns_records.post(zone_id, data={'name':socket.gethostname(), 'type':'A', 'content':socket.gethostbyname(socket.gethostname() + '.local')})
except CloudFlare.exceptions.CloudFlareAPIError as e:
    sys.exit('/zones.dns_records.post %s - %d %s' % (e, e, e))
