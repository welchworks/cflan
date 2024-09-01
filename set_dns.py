#!/usr/bin/env python3
# steven@makeitwork.cloud
# https://github.com/welchworks/cflan/blob/main/set_dns.py
#
# To run as NetworkManager script, place in /etc/NetworkManager/disapatcher.d/
# Accepts two optional positional arguments: 1) the NIC interface name, 2) the action, i.e. "up"
#
# Requires two YAML variables to be set in sops_vars.yaml:
# cf_token - Cloudflare API Token with DNS edit permissions
# cf_domain_name - Name of the DNS Zone in Cloudflare, i.e. mydomain.com

import socket
import CloudFlare
import sys
import yaml
import subprocess
import netifaces

print("Using local IP address " + socket.gethostbyname(socket.gethostname() + '.local') + " ...")
if "127.0.0" in socket.gethostbyname(socket.gethostname()):
    print("Failed!")
    sys.exit("The local IP address is within the localhost subnet.")

print("Parsing NetworkManager arguments...")
try:
    if netifaces.ifaddresses(sys.argv[1])[netifaces.AF_INET][0]['addr'] != socket.gethostbyname(socket.gethostname()):
        print("Failed!")
        sys.exit("The IP address " + netifaces.ifaddresses(sys.argv[1])[netifaces.AF_INET][0]['addr'] + " for the interface " + sys.argv[1] + " is not the same as the primary IP address of " + socket.gethostbyname(socket.gethostname()) + " .")
    if sys.argv[2] != "up":
        print("Failed!")
        sys.exit("The NetworkManager action '" + sys.argv[2] + "' does not match the required action of 'up'.")
except KeyError:
    print("Failed!")
    sys.exit("IP address for interface not set.")
except ValueError:
    print("Failed!")
    sys.exit("Invalid NetworkManager interface value for this script.")
except IndexError:
    print("NetworkManager argument(s) were not set. Proceeding...")

print("Getting SOPS encrypted values from sops_vars.yaml ...")
try:
    r = subprocess.run(['sops', 'decrypt', 'sops_vars.yaml'], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    if r.returncode != 0:
        print(r.stderr.decode('utf-8'))
        sys.exit("Failed getting SOPS values.")
except FileNotFoundError:
    print("Failed!")
    sys.exit("SOPS must be installed and configured to use this script.")

print("Getting YAML variables from SOPS output...")
sops_vars = yaml.safe_load(r.stdout.decode('utf-8'))

print("Initiating CloudFlare object using API Token...")
cf = CloudFlare.CloudFlare(token = sops_vars['cf_token'])

print("Getting CloudFlare DNS Zone ID and Name...")
zone_id = cf.zones.get(params={'per_page':'1', 'name':sops_vars['cf_domain_name']})[0]['id']
zone_name = cf.zones.get(params={'per_page':'1', 'name':sops_vars['cf_domain_name']})[0]['name']

print("Attempting to get existing DNS record for " + socket.gethostname() + "." + sops_vars['cf_domain_name'] + " ...")
try:
    dns_id = cf.zones.dns_records.get(zone_id, params={'name':socket.gethostname() + '.' + zone_name, 'match':'all', 'type':'A'})[0]['id']
except:
    print("Record not found...")
    print("Creating new record for " + socket.gethostname() + "." + sops_vars['cf_domain_name'] + " ...")
    try:
        cf.zones.dns_records.post(zone_id, data={'name':socket.gethostname(), 'type':'A', 'content':socket.gethostbyname(socket.gethostname())})
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        sys.exit('/zones.dns_records.post %s - %d %s' % (e, e, e))
    print("Success!")
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

print("Success!")
