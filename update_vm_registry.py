import yaml
import requests
from atlassian import Confluence
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import re
import time

# No SSL warning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Gets configuration
def load_config(config_file='config.yml'):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

# Gets node list from Proxmox
def get_nodes(proxmox_config):
    headers = {
        'Authorization': f'PVEAPIToken={proxmox_config["token_id"]}={proxmox_config["token_secret"]}'
    }
    url = f"{proxmox_config['url']}/api2/json/nodes"
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()  
    return response.json().get('data', [])

# Gets VMs for the specific node
def get_vms_for_node(proxmox_config, node):
    headers = {
        'Authorization': f'PVEAPIToken={proxmox_config["token_id"]}={proxmox_config["token_secret"]}'
    }
    url = f"{proxmox_config['url']}/api2/json/nodes/{node}/qemu"
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()  
    return response.json().get('data', [])

# Gets needed VM info
def get_vm_details(proxmox_config, node, vmid):
    headers = {
        'Authorization': f'PVEAPIToken={proxmox_config["token_id"]}={proxmox_config["token_secret"]}'
    }
    url = f"{proxmox_config['url']}/api2/json/nodes/{node}/qemu/{vmid}/config"
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()  
    return response.json().get('data', {})

# Gets MAC Address and VLAN Tag from "net0" API value
def parse_net0(net0_str):
    mac_address = None
    vlan_tag = None

    # Searching for MAC Address and VLAN Tag using regex
    mac_match = re.search(r'([0-9A-Fa-f:]{17,})', net0_str)
    vlan_match = re.search(r'tag=(\d+)', net0_str)

    if mac_match:
        mac_address = mac_match.group(1)
    if vlan_match:
        vlan_tag = vlan_match.group(1)
    
    return mac_address, vlan_tag

# Converts bytes to kilobytes
def bytes_to_gb(byte_value):
    return round(byte_value / (1024 ** 3), 2)

# Gets final VM list from Proxmox
def get_vm_list(proxmox_config):
    nodes = get_nodes(proxmox_config)
    vm_list = []
    for node in nodes:
        node_name = node['node']
        vms = get_vms_for_node(proxmox_config, node_name)
        for vm in vms:
            vm_details = get_vm_details(proxmox_config, node_name, vm['vmid'])
            net0_str = vm_details.get('net0', '')
            mac_address, vlan_tag = parse_net0(net0_str)
            
            vm_info = {
                'vmid': vm.get('vmid', 'N/A'),
                'name': vm.get('name', 'N/A'),
                'status': vm.get('status', 'N/A'),
                'maxmem': bytes_to_gb(vm.get('maxmem', 0)),  # converts to GB
                'maxdisk': bytes_to_gb(vm.get('maxdisk', 0)),  # converts to GB
                'node': node_name,
                'vlan_tag': vlan_tag if vlan_tag else 'N/A',
                'mac_address': mac_address if mac_address else 'N/A',
                'processors': vm_details.get('cores', 'N/A'),  # CPU cores count
                'description': (vm_details.get('description', 'N/A').replace('\n', '<br />'))  # VM description
            }
            vm_list.append(vm_info)
    
    # Sorting VMs by VMID
    vm_list.sort(key=lambda x: x['vmid'])
    return vm_list

# Gets page info
def get_page_content(confluence_config, page_id):
    url = f"{confluence_config['url']}/rest/api/content/{page_id}?expand=body.storage"
    headers = {
        'Authorization': f'Bearer {confluence_config["token"]}'
    }
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    return response.json()

# Updates Confluence page
def update_confluence_page(confluence_config, vm_list):
    confluence = Confluence(
        url=confluence_config['url'],
        token=confluence_config['token'],
        verify_ssl=False
    )
    
    page_data = get_page_content(confluence_config, confluence_config['page_id'])
    page_title = page_data['title']
    
    # Creating fresh VM info table with markdown tags
    new_content = '<table><tr><th>VMID</th><th>Node</th><th>VM Name</th><th>Status</th><th>Max CPU</th><th>Max RAM, Gb</th><th>Main disk size, Gb</th><th>VLAN Tag</th><th>MAC-address</th><th>Description</th></tr>'
    for vm in vm_list:
        new_content += (
            f'<tr><td>{vm.get("vmid", "N/A")}</td>'
            f'<td>{vm.get("node", "N/A")}</td>'
            f'<td>{vm.get("name", "N/A")}</td>'
            f'<td>{vm.get("status", "N/A")}</td>'
            f'<td>{vm.get("processors", "N/A")}</td>'
            f'<td>{vm.get("maxmem", "N/A")}</td>'
            f'<td>{vm.get("maxdisk", "N/A")}</td>'
            f'<td>{vm.get("vlan_tag", "N/A")}</td>'
            f'<td>{vm.get("mac_address", "N/A")}</td>'
            f'<td>{vm.get("description", "N/A")}</td></tr>'
        )
    new_content += '</table>'
    
    print("New content to be updated:\n", new_content)
    
    confluence.update_page(
        page_id=confluence_config['page_id'],
        title=page_title,
        body=new_content,
        representation='storage'
    )

def main():
    config = load_config()
    proxmox_config = config['proxmox']
    confluence_config = config['confluence']
    
    while True:
        try:
            vm_list = get_vm_list(proxmox_config)
            print("VM List:\n", vm_list)
            update_confluence_page(confluence_config, vm_list)
        except Exception as e:
            print(f"Error occurred: {e}")
        
        # Sleeps 60 seconds before next update. Change it if necessary
        time.sleep(60)

if __name__ == "__main__":
    main()