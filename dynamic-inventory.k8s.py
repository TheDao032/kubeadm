#!/usr/bin/env python

import argparse
import json
import subprocess

class VirtualBoxInventory(object):
    def __init__(self):
        self.inventory = {}
        self.read_cli_args()

        if self.args.list:
            self.inventory = self.get_inventory()
        if self.args.host:
            self.inventory = self.get_host_info(self.args.host)
        else:
            self.inventory = self.empty_inventory()

        print(json.dumps(self.inventory, indent=2))

    def read_cli_args(self):
        parser = argparse.ArgumentParser(description='VirtualBox Dynamic Inventory Script')
        parser.add_argument('--list', action='store_true', help='List all VMs and their IPs')
        parser.add_argument('--host', type=str, help='Get details of a specific VM')
        self.args = parser.parse_args()

    def get_inventory(self):
        inventory = {
            'all': {
                'hosts': [],
                'vars': {},
                'children': [
                    'master',
                    'worker'
                ]
            },
            'master': {
                'hosts': [],
                'vars': {}
            },
            'worker': {
                'hosts': [],
                'vars': {}
            }
        }
        vms = self.get_all_vms()

        for vm in vms:
            ip = self.get_vm_ip(vm)
            if ip:
                inventory['all']['hosts'].append(vm)
                if vm.__contains__("controlplane"):
                    inventory["master"] = {
                        'hosts': [vm],
                        'vars': {
                            "ansible_host": ip
                        }
                    }
                elif vm.__contains__("node"):
                    inventory["worker"] = {
                        'hosts': [vm],
                        'vars': {
                            "ansible_host": ip
                        }
                    }
                else:
                    pass

        return inventory

    def get_host_info(self, hostname):
        ip = self.get_vm_ip(hostname)
        if ip:
            return {hostname: {'ansible_host': ip}}
        else:
            return self.empty_inventory()

    def get_all_vms(self):
        try:
            result = subprocess.run(['VBoxManage', 'list', 'vms'], capture_output=True, text=True, check=True)
            vms = [line.split('"')[1] for line in result.stdout.splitlines()]
            print(vms)
            return vms
        except subprocess.CalledProcessError:
            return []

    def get_vm_ip(self, vm_name):
        try:
            result = subprocess.run(['VBoxManage', 'guestproperty', 'enumerate', vm_name], capture_output=True, text=True, check=True)
            for line in result.stdout.splitlines():
                if '1/V4/IP' in line:
                    return line.strip().split("'")[1].strip()
            return None
        except subprocess.CalledProcessError:
            return None

    def empty_inventory(self):
        return {'_meta': {'hostvars': {}}}

if __name__ == '__main__':
    VirtualBoxInventory()
