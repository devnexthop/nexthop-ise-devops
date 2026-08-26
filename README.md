# Cisco ISE DevOps Configuration Management

This repository provides tools for exporting and importing Cisco ISE configurations in a customer-generic manner. All customer-specific settings are stored in a separate configuration file for easy customization.

## Features

- **Export ISE Configurations**: Export policies, endpoints, network devices, identity groups, users, and certificates
- **Import ISE Configurations**: Import configurations from exported files to target ISE nodes
- **Customer-Generic Design**: All customer-specific settings in separate configuration file
- **Compressed Output**: Optional compression of export files
- **Comprehensive Logging**: Detailed logging of all operations
- **Multi-Node Support**: Support for primary and secondary ISE nodes

## Prerequisites

- Python 3.7 or higher
- Cisco ISE with ERS API access
- Network connectivity to ISE nodes

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd nexthop-ise-devops
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Configure customer settings:
```bash
cp customer_config_example.py customer_config.py
# Edit customer_config.py with your specific settings
```

## Configuration

### Customer Configuration File (`customer_config.py`)

The customer configuration file contains all customer-specific settings:

```python
CUSTOMER_CONFIG = {
    "ise_nodes": [
        {
            "hostname": "ise-primary.yourdomain.com",
            "ip_address": "10.1.1.10",
            "username": "admin",
            "password": "YourSecurePassword123!",
            "node_type": "primary"
        }
    ],
    "backup_settings": {
        "backup_directory": "/tmp/ise_backups",
        "retention_days": 30,
        "encrypt_backups": True
    }
}
```

### Export Settings

Configure what to export:

```python
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
```

## Usage

### Export Configurations

Export configurations from all configured ISE nodes:

```bash
python ise_export.py
```

The script will:
1. Connect to each configured ISE node
2. Export the specified configuration types
3. Save the export to the backup directory
4. Optionally compress the output

### Import Configurations

Import configurations from an export file:

```bash
python ise_import.py /path/to/export/file.json
```

Or with compressed file:

```bash
python ise_import.py /path/to/export/file.zip
```

The script will:
1. Load the export file
2. Connect to each configured ISE node
3. Import the configurations
4. Log all operations

## Configuration Types

The following configuration types can be exported/imported:

- **policies**: Authorization and authentication policies
- **endpoints**: Endpoint configurations
- **certificates**: Certificate profiles
- **network_devices**: Network device configurations
- **identity_groups**: Identity group configurations
- **users**: Internal user configurations

## File Structure

```
nexthop-ise-devops/
├── customer_config.py              # Customer-specific configuration
├── customer_config_example.py      # Example configuration file
├── ise_export.py                   # Export script
├── ise_import.py                   # Import script
├── requirements.txt                 # Python dependencies
└── README.md                       # This file
```

## Logging

All operations are logged to:
- Console output
- `ise_operations.log` file

Log levels can be configured in the customer configuration file.

## Security Considerations

- **Credentials**: Store credentials securely and consider using environment variables or secret management systems
- **SSL Certificates**: The scripts disable SSL verification for self-signed certificates. Consider implementing proper certificate validation for production use
- **Network Access**: Ensure proper network security and access controls

## Troubleshooting

### Common Issues

1. **Authentication Failures**: Verify credentials and network connectivity
2. **SSL Errors**: Check certificate validity or disable SSL verification for testing
3. **Permission Errors**: Ensure the backup directory is writable
4. **Import Failures**: Check for conflicting configurations and dependencies

### Debug Mode

Enable debug logging by changing the log level in `customer_config.py`:

```python
LOGGING_CONFIG = {
    "log_level": "DEBUG",
    # ... other settings
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue in the repository
- Contact the development team
- Check the troubleshooting section above

