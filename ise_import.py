#!/usr/bin/env python3
"""
Cisco ISE Configuration Import Script
This script imports configurations to Cisco ISE nodes from exported files.
"""

import requests
import json
import os
import sys
import logging
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning
import zipfile
from customer_config import CUSTOMER_CONFIG, EXPORT_SETTINGS, LOGGING_CONFIG

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class ISEImporter:
    def __init__(self):
        self.setup_logging()
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification for ISE
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, LOGGING_CONFIG['log_level']),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOGGING_CONFIG['log_file']),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def authenticate(self, node):
        """Authenticate with ISE node"""
        auth_url = f"https://{node['ip_address']}/ers/config/op/systemconfig"
        
        try:
            response = self.session.get(
                auth_url,
                auth=(node['username'], node['password']),
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.info(f"Successfully authenticated with {node['hostname']}")
                return True
            else:
                self.logger.error(f"Authentication failed for {node['hostname']}: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Authentication error for {node['hostname']}: {str(e)}")
            return False
    
    def load_export_file(self, filepath):
        """Load exported configuration file"""
        try:
            # Handle compressed files
            if filepath.endswith('.zip'):
                with zipfile.ZipFile(filepath, 'r') as zipf:
                    # Extract the first JSON file
                    json_files = [f for f in zipf.namelist() if f.endswith('.json')]
                    if json_files:
                        with zipf.open(json_files[0]) as f:
                            return json.load(f)
                    else:
                        self.logger.error("No JSON file found in zip archive")
                        return None
            else:
                with open(filepath, 'r') as f:
                    return json.load(f)
                    
        except Exception as e:
            self.logger.error(f"Error loading export file {filepath}: {str(e)}")
            return None
    
    def import_authorization_policies(self, node, policies):
        """Import authorization policies"""
        if not policies or 'authorization_policies' not in policies:
            return True
            
        auth_policies = policies['authorization_policies']
        imported_count = 0
        
        if 'SearchResult' in auth_policies and 'resources' in auth_policies['SearchResult']:
            for policy in auth_policies['SearchResult']['resources']:
                try:
                    # Get full policy details
                    policy_url = f"https://{node['ip_address']}/ers/config/authorizationpolicy/{policy['id']}"
                    response = self.session.get(policy_url, auth=(node['username'], node['password']))
                    
                    if response.status_code == 200:
                        policy_data = response.json()['AuthorizationPolicy']
                        
                        # Create new policy (remove ID for import)
                        if 'id' in policy_data:
                            del policy_data['id']
                        
                        create_url = f"https://{node['ip_address']}/ers/config/authorizationpolicy"
                        create_response = self.session.post(
                            create_url,
                            json=policy_data,
                            auth=(node['username'], node['password']),
                            headers={'Content-Type': 'application/json'}
                        )
                        
                        if create_response.status_code in [200, 201]:
                            imported_count += 1
                            self.logger.info(f"Imported authorization policy: {policy_data.get('name', 'Unknown')}")
                        else:
                            self.logger.warning(f"Failed to import policy {policy_data.get('name', 'Unknown')}: {create_response.status_code}")
                            
                except Exception as e:
                    self.logger.error(f"Error importing authorization policy: {str(e)}")
        
        self.logger.info(f"Imported {imported_count} authorization policies")
        return True
    
    def import_authentication_policies(self, node, policies):
        """Import authentication policies"""
        if not policies or 'authentication_policies' not in policies:
            return True
            
        authn_policies = policies['authentication_policies']
        imported_count = 0
        
        if 'SearchResult' in authn_policies and 'resources' in authn_policies['SearchResult']:
            for policy in authn_policies['SearchResult']['resources']:
                try:
                    # Get full policy details
                    policy_url = f"https://{node['ip_address']}/ers/config/authenticationpolicy/{policy['id']}"
                    response = self.session.get(policy_url, auth=(node['username'], node['password']))
                    
                    if response.status_code == 200:
                        policy_data = response.json()['AuthenticationPolicy']
                        
                        # Create new policy (remove ID for import)
                        if 'id' in policy_data:
                            del policy_data['id']
                        
                        create_url = f"https://{node['ip_address']}/ers/config/authenticationpolicy"
                        create_response = self.session.post(
                            create_url,
                            json=policy_data,
                            auth=(node['username'], node['password']),
                            headers={'Content-Type': 'application/json'}
                        )
                        
                        if create_response.status_code in [200, 201]:
                            imported_count += 1
                            self.logger.info(f"Imported authentication policy: {policy_data.get('name', 'Unknown')}")
                        else:
                            self.logger.warning(f"Failed to import policy {policy_data.get('name', 'Unknown')}: {create_response.status_code}")
                            
                except Exception as e:
                    self.logger.error(f"Error importing authentication policy: {str(e)}")
        
        self.logger.info(f"Imported {imported_count} authentication policies")
        return True
    
    def import_endpoints(self, node, endpoints):
        """Import endpoint configurations"""
        if not endpoints:
            return True
            
        imported_count = 0
        
        if 'SearchResult' in endpoints and 'resources' in endpoints['SearchResult']:
            for endpoint in endpoints['SearchResult']['resources']:
                try:
                    # Get full endpoint details
                    endpoint_url = f"https://{node['ip_address']}/ers/config/endpoint/{endpoint['id']}"
                    response = self.session.get(endpoint_url, auth=(node['username'], node['password']))
                    
                    if response.status_code == 200:
                        endpoint_data = response.json()['ERSEndPoint']
                        
                        # Create new endpoint (remove ID for import)
                        if 'id' in endpoint_data:
                            del endpoint_data['id']
                        
                        create_url = f"https://{node['ip_address']}/ers/config/endpoint"
                        create_response = self.session.post(
                            create_url,
                            json=endpoint_data,
                            auth=(node['username'], node['password']),
                            headers={'Content-Type': 'application/json'}
                        )
                        
                        if create_response.status_code in [200, 201]:
                            imported_count += 1
                            self.logger.info(f"Imported endpoint: {endpoint_data.get('name', 'Unknown')}")
                        else:
                            self.logger.warning(f"Failed to import endpoint {endpoint_data.get('name', 'Unknown')}: {create_response.status_code}")
                            
                except Exception as e:
                    self.logger.error(f"Error importing endpoint: {str(e)}")
        
        self.logger.info(f"Imported {imported_count} endpoints")
        return True
    
    def import_network_devices(self, node, devices):
        """Import network device configurations"""
        if not devices:
            return True
            
        imported_count = 0
        
        if 'SearchResult' in devices and 'resources' in devices['SearchResult']:
            for device in devices['SearchResult']['resources']:
                try:
                    # Get full device details
                    device_url = f"https://{node['ip_address']}/ers/config/networkdevice/{device['id']}"
                    response = self.session.get(device_url, auth=(node['username'], node['password']))
                    
                    if response.status_code == 200:
                        device_data = response.json()['NetworkDevice']
                        
                        # Create new device (remove ID for import)
                        if 'id' in device_data:
                            del device_data['id']
                        
                        create_url = f"https://{node['ip_address']}/ers/config/networkdevice"
                        create_response = self.session.post(
                            create_url,
                            json=device_data,
                            auth=(node['username'], node['password']),
                            headers={'Content-Type': 'application/json'}
                        )
                        
                        if create_response.status_code in [200, 201]:
                            imported_count += 1
                            self.logger.info(f"Imported network device: {device_data.get('name', 'Unknown')}")
                        else:
                            self.logger.warning(f"Failed to import device {device_data.get('name', 'Unknown')}: {create_response.status_code}")
                            
                except Exception as e:
                    self.logger.error(f"Error importing network device: {str(e)}")
        
        self.logger.info(f"Imported {imported_count} network devices")
        return True
    
    def import_identity_groups(self, node, groups):
        """Import identity groups"""
        if not groups:
            return True
            
        imported_count = 0
        
        if 'SearchResult' in groups and 'resources' in groups['SearchResult']:
            for group in groups['SearchResult']['resources']:
                try:
                    # Get full group details
                    group_url = f"https://{node['ip_address']}/ers/config/identitygroup/{group['id']}"
                    response = self.session.get(group_url, auth=(node['username'], node['password']))
                    
                    if response.status_code == 200:
                        group_data = response.json()['IdentityGroup']
                        
                        # Create new group (remove ID for import)
                        if 'id' in group_data:
                            del group_data['id']
                        
                        create_url = f"https://{node['ip_address']}/ers/config/identitygroup"
                        create_response = self.session.post(
                            create_url,
                            json=group_data,
                            auth=(node['username'], node['password']),
                            headers={'Content-Type': 'application/json'}
                        )
                        
                        if create_response.status_code in [200, 201]:
                            imported_count += 1
                            self.logger.info(f"Imported identity group: {group_data.get('name', 'Unknown')}")
                        else:
                            self.logger.warning(f"Failed to import group {group_data.get('name', 'Unknown')}: {create_response.status_code}")
                            
                except Exception as e:
                    self.logger.error(f"Error importing identity group: {str(e)}")
        
        self.logger.info(f"Imported {imported_count} identity groups")
        return True
    
    def import_users(self, node, users):
        """Import user configurations"""
        if not users:
            return True
            
        imported_count = 0
        
        if 'SearchResult' in users and 'resources' in users['SearchResult']:
            for user in users['SearchResult']['resources']:
                try:
                    # Get full user details
                    user_url = f"https://{node['ip_address']}/ers/config/internaluser/{user['id']}"
                    response = self.session.get(user_url, auth=(node['username'], node['password']))
                    
                    if response.status_code == 200:
                        user_data = response.json()['InternalUser']
                        
                        # Create new user (remove ID for import)
                        if 'id' in user_data:
                            del user_data['id']
                        
                        create_url = f"https://{node['ip_address']}/ers/config/internaluser"
                        create_response = self.session.post(
                            create_url,
                            json=user_data,
                            auth=(node['username'], node['password']),
                            headers={'Content-Type': 'application/json'}
                        )
                        
                        if create_response.status_code in [200, 201]:
                            imported_count += 1
                            self.logger.info(f"Imported user: {user_data.get('name', 'Unknown')}")
                        else:
                            self.logger.warning(f"Failed to import user {user_data.get('name', 'Unknown')}: {create_response.status_code}")
                            
                except Exception as e:
                    self.logger.error(f"Error importing user: {str(e)}")
        
        self.logger.info(f"Imported {imported_count} users")
        return True
    
    def import_certificates(self, node, certificates):
        """Import certificate configurations"""
        if not certificates:
            return True
            
        imported_count = 0
        
        if 'SearchResult' in certificates and 'resources' in certificates['SearchResult']:
            for cert in certificates['SearchResult']['resources']:
                try:
                    # Get full certificate details
                    cert_url = f"https://{node['ip_address']}/ers/config/certificateprofile/{cert['id']}"
                    response = self.session.get(cert_url, auth=(node['username'], node['password']))
                    
                    if response.status_code == 200:
                        cert_data = response.json()['CertificateProfile']
                        
                        # Create new certificate (remove ID for import)
                        if 'id' in cert_data:
                            del cert_data['id']
                        
                        create_url = f"https://{node['ip_address']}/ers/config/certificateprofile"
                        create_response = self.session.post(
                            create_url,
                            json=cert_data,
                            auth=(node['username'], node['password']),
                            headers={'Content-Type': 'application/json'}
                        )
                        
                        if create_response.status_code in [200, 201]:
                            imported_count += 1
                            self.logger.info(f"Imported certificate: {cert_data.get('name', 'Unknown')}")
                        else:
                            self.logger.warning(f"Failed to import certificate {cert_data.get('name', 'Unknown')}: {create_response.status_code}")
                            
                except Exception as e:
                    self.logger.error(f"Error importing certificate: {str(e)}")
        
        self.logger.info(f"Imported {imported_count} certificates")
        return True
    
    def import_all_configs(self, node, export_data):
        """Import all configurations to a node"""
        self.logger.info(f"Starting import to {node['hostname']}")
        
        if not self.authenticate(node):
            return False
            
        configurations = export_data.get('configurations', {})
        success = True
        
        # Import based on available configurations
        if 'policies' in configurations:
            if not self.import_authorization_policies(node, configurations['policies']):
                success = False
            if not self.import_authentication_policies(node, configurations['policies']):
                success = False
                
        if 'endpoints' in configurations:
            if not self.import_endpoints(node, configurations['endpoints']):
                success = False
                
        if 'network_devices' in configurations:
            if not self.import_network_devices(node, configurations['network_devices']):
                success = False
                
        if 'identity_groups' in configurations:
            if not self.import_identity_groups(node, configurations['identity_groups']):
                success = False
                
        if 'users' in configurations:
            if not self.import_users(node, configurations['users']):
                success = False
                
        if 'certificates' in configurations:
            if not self.import_certificates(node, configurations['certificates']):
                success = False
        
        return success
    
    def run_import(self, export_file):
        """Main import function"""
        self.logger.info(f"Starting ISE configuration import from {export_file}")
        
        # Load export data
        export_data = self.load_export_file(export_file)
        if not export_data:
            self.logger.error("Failed to load export file")
            return False
        
        # Import to each configured node
        for node in CUSTOMER_CONFIG['ise_nodes']:
            try:
                success = self.import_all_configs(node, export_data)
                if success:
                    self.logger.info(f"Successfully imported configurations to {node['hostname']}")
                else:
                    self.logger.error(f"Failed to import configurations to {node['hostname']}")
            except Exception as e:
                self.logger.error(f"Error processing node {node['hostname']}: {str(e)}")
        
        self.logger.info("Import process completed")
        return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ise_import.py <export_file_path>")
        sys.exit(1)
    
    import_file = sys.argv[1]
    importer = ISEImporter()
    importer.run_import(import_file)

