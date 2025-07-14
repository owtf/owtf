# Azure Terraform Configuration for OWTF Deployment

This directory contains Terraform configuration files to deploy OWTF on Microsoft Azure using free tier resources.

## Prerequisites

1. Azure CLI installed and configured
2. Terraform installed
3. SSH key pair generated (`~/.ssh/id_rsa.pub` should exist)

## Resources Created

- **Resource Group**: Container for all resources
- **Virtual Network**: Network infrastructure with public and private subnets  
- **Virtual Machine**: Standard_B1s (free tier eligible) running Ubuntu 22.04
- **Public IP**: Static IP for external access
- **Network Security Group**: Firewall rules for OWTF ports
- **SSH Key**: Generated automatically and stored in `ssh-keys/` folder during apply

## Usage

1. Initialize Terraform:
   ```bash
   terraform init
   ```

2. Plan the deployment:
   ```bash
   terraform plan
   ```

3. Apply the configuration:
   ```bash
   terraform apply
   ```

4. Access OWTF using the provided outputs

## Ports

- 8008: OWTF Admin interface  
- 8010: OWTF Proxy interface
- 8019: OWTF UI interface (main web interface)
- 22: SSH access

## Cleanup

To destroy the infrastructure:
```bash
terraform destroy
```
