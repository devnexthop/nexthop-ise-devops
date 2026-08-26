#!/usr/bin/env python3
"""
Cisco ISE Configuration Export Script
This script exports various configurations from Cisco ISE nodes.
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

class ISEExporter:
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
    
    def export_policies(self, node):
        """Export ISE policies"""
        policies = {}
        
        # Export Authorization Policies
        auth_policies_url = f"https://{node['ip_address']}/ers/config/authorizationpolicy"
        try:
            response = self.session.get(auth_policies_url, auth=(node['username'], node['password']))
            if response.status_code == 200:
                policies['authorization_policies'] = response.json()
                self.logger.info(f"Exported authorization policies from {node['hostname']}")
        except Exception as e:
            self.logger.error(f"Error exporting authorization policies: {str(e)}")
            
        # Export Authentication Policies
        authn_policies_url = f"https://{node['ip_address']}/ers/config/authenticationpolicy"
        try:
            response = self.session.get(authn_policies_url, auth=(node['username'], node['password']))
            if response.status_code == 200:
                policies['authentication_policies'] = response.json()
                self.logger.info(f"Exported authentication policies from {node['hostname']}")
        except Exception as e:
            self.logger.error(f"Error exporting authentication policies: {str(e)}")
            
        return policies
    
    def export_endpoints(self, node):
        """Export endpoint configurations"""
        endpoints_url = f"https://{node['ip_address']}/ers/config/endpoint"
        
        try:
            response = self.session.get(endpoints_url, auth=(node['username'], node['password']))
            if response.status_code == 200:
                self.logger.info(f"Exported endpoints from {node['hostname']}")
                return response.json()
            else:
                self.logger.error(f"Failed to export endpoints: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error exporting endpoints: {str(e)}")
            return None
    
    def export_network_devices(self, node):
        """Export network device configurations"""
        devices_url = f"https://{node['ip_address']}/ers/config/networkdevice"
        
        try:
            response = self.session.get(devices_url, auth=(node['username'], node['password']))
            if response.status_code == 200:
                self.logger.info(f"Exported network devices from {node['hostname']}")
                return response.json()
            else:
                self.logger.error(f"Failed to export network devices: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error exporting network devices: {str(e)}")
            return None
    
    def export_identity_groups(self, node):
        """Export identity groups"""
        groups_url = f"https://{node['ip_address']}/ers/config/identitygroup"
        
        try:
            response = self.session.get(groups_url, auth=(node['username'], node['password']))
            if response.status_code == 200:
                self.logger.info(f"Exported identity groups from {node['hostname']}")
                return response.json()
            else:
                self.logger.error(f"Failed to export identity groups: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error exporting identity groups: {str(e)}")
            return None
    
    def export_users(self, node):
        """Export user configurations"""
        users_url = f"https://{node['ip_address']}/ers/config/internaluser"
        
        try:
            response = self.session.get(users_url, auth=(node['username'], node['password']))
            if response.status_code == 200:
                self.logger.info(f"Exported users from {node['hostname']}")
                return response.json()
            else:
                self.logger.error(f"Failed to export users: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error exporting users: {str(e)}")
            return None
    
    def export_certificates(self, node):
        """Export certificate configurations"""
        certs_url = f"https://{node['ip_address']}/ers/config/certificateprofile"
        
        try:
            response = self.session.get(certs_url, auth=(node['username'], node['password']))
            if response.status_code == 200:
                self.logger.info(f"Exported certificates from {node['hostname']}")
                return response.json()
            else:
                self.logger.error(f"Failed to export certificates: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error exporting certificates: {str(e)}")
            return None
    
    def export_all_configs(self, node):
        """Export all configurations from a node"""
        self.logger.info(f"Starting export from {node['hostname']}")
        
        if not self.authenticate(node):
            return None
            
        export_data = {
            'node_info': {
                'hostname': node['hostname'],
                'ip_address': node['ip_address'],
                'node_type': node['node_type'],
                'export_timestamp': datetime.now().isoformat()
            },
            'configurations': {}
        }
        
        # Export based on settings
        if EXPORT_SETTINGS['config_types']:
            for config_type in EXPORT_SETTINGS['config_types']:
                if config_type == 'policies':
                    export_data['configurations']['policies'] = self.export_policies(node)
                elif config_type == 'endpoints':
                    export_data['configurations']['endpoints'] = self.export_endpoints(node)
                elif config_type == 'network_devices':
                    export_data['configurations']['network_devices'] = self.export_network_devices(node)
                elif config_type == 'identity_groups':
                    export_data['configurations']['identity_groups'] = self.export_identity_groups(node)
                elif config_type == 'users':
                    export_data['configurations']['users'] = self.export_users(node)
                elif config_type == 'certificates':
                    export_data['configurations']['certificates'] = self.export_certificates(node)
        
        return export_data
    
    def save_export(self, export_data, node):
        """Save exported data to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ise_export_{node['hostname']}_{timestamp}.json"
        
        # Create backup directory if it doesn't exist
        backup_dir = CUSTOMER_CONFIG['backup_settings']['backup_directory']
        os.makedirs(backup_dir, exist_ok=True)
        
        filepath = os.path.join(backup_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"Export saved to {filepath}")
            
            # Compress if enabled
            if EXPORT_SETTINGS['compress_output']:
                zip_filename = filepath.replace('.json', '.zip')
                with zipfile.ZipFile(zip_filename, 'w') as zipf:
                    zipf.write(filepath, filename)
                os.remove(filepath)  # Remove original file
                self.logger.info(f"Compressed export saved to {zip_filename}")
                return zip_filename
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving export: {str(e)}")
            return None
    
    def run_export(self):
        """Main export function"""
        self.logger.info("Starting ISE configuration export")
        
        for node in CUSTOMER_CONFIG['ise_nodes']:
            try:
                export_data = self.export_all_configs(node)
                if export_data:
                    saved_file = self.save_export(export_data, node)
                    if saved_file:
                        self.logger.info(f"Successfully exported configurations from {node['hostname']}")
                    else:
                        self.logger.error(f"Failed to save export from {node['hostname']}")
                else:
                    self.logger.error(f"Failed to export from {node['hostname']}")
            except Exception as e:
                self.logger.error(f"Error processing node {node['hostname']}: {str(e)}")
        
        self.logger.info("Export process completed")

if __name__ == "__main__":
    exporter = ISEExporter()
    exporter.run_export()

