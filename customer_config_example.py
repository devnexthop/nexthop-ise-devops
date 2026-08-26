"""
Example Customer Configuration File for Cisco ISE DevOps
Copy this file to customer_config.py and modify with your specific settings.
"""

# Customer Configuration
CUSTOMER_CONFIG = {
    "ise_nodes": [
        {
            "hostname": "ise-primary.yourdomain.com",
            "ip_address": "10.1.1.10",
            "username": "admin",
            "password": "YourSecurePassword123!",
            "node_type": "primary"
        },
        {
            "hostname": "ise-secondary.yourdomain.com", 
            "ip_address": "10.1.1.11",
            "username": "admin",
            "password": "YourSecurePassword123!",
            "node_type": "secondary"
        }
    ],
    "backup_settings": {
        "backup_directory": "/tmp/ise_backups",
        "retention_days": 30,
        "encrypt_backups": True
    },
    "export_settings": {
        "include_passwords": False,
        "include_certificates": True,
        "include_policies": True,
        "include_endpoints": True
    }
}

# Export/Import Settings
EXPORT_SETTINGS = {
    "config_types": [
        "policies",
        "endpoints", 
        "certificates",
        "network_devices",
        "identity_groups",
        "users"
    ],
    "output_format": "json",
    "compress_output": True
}

# Logging Configuration
LOGGING_CONFIG = {
    "log_level": "INFO",
    "log_file": "ise_operations.log",
    "max_log_size": "10MB",
    "backup_count": 5
}

