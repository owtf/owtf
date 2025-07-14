# Azure Terraform Configuration for OWTF Deployment

This directory contains Terraform configuration files to deploy OWTF on Microsoft Azure using **free tier resources only**. The deployment uses **Ansible** for reliable automated setup.

## Prerequisites

1. **Azure CLI** installed and configured (`az login`)
2. **Terraform** installed
3. **Ansible** installed - Run `./install-ansible.sh` to install

## Quick Start

1. **Install Ansible** (if not already installed):
   ```bash
   ./install-ansible.sh
   ```

2. **Configure variables**:
   ```bash
   # Edit variables.tf as needed
   ```

3. **Deploy**:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

4. **Access OWTF** (automatically set up via Ansible):
   - Web UI: `http://<public-ip>:8019`
   - Admin: `http://<public-ip>:8008`
   - Proxy: `http://<public-ip>:8010`

## How It Works

1. **Terraform** creates the Azure infrastructure (VM, network, security)
2. **Null Resource** with local-exec provisioner:
   - Waits for VM to be ready
   - Dynamically generates `inventory.ini` 
   - Runs `ansible-playbook` to configure OWTF
3. **Ansible Playbook** (`owtf-setup.yml`) automatically:
   - Installs Docker and security tools
   - Configures firewall
   - Clones and starts OWTF services

## Resources Created

- **Resource Group**: Container for all resources
- **Virtual Network**: Network infrastructure  
- **Virtual Machine**: Standard_B1s (free tier eligible) running Ubuntu 22.04
- **Public IP**: For external access
- **Network Security Group**: Firewall rules for OWTF ports
- **SSH Key**: Generated automatically and stored in `ssh-keys/` folder

## Debugging

If setup fails, you can re-run Ansible manually:
```bash
export ANSIBLE_HOST_KEY_CHECKING=False
ansible-playbook -i inventory.ini owtf-setup.yml
```

## Ports

- 8008: OWTF Admin interface  
- 8010: OWTF Proxy interface
- 8019: OWTF UI interface (main web interface)
- 22: SSH access

## Free Tier Compliance

All resources stay within Azure free tier limits:
- VM: Standard_B1s (750 hours/month)
- Storage: 30GB Standard LRS
- Network: All networking free
- No premium services used

## Cleanup

To destroy the infrastructure:
```bash
terraform destroy
```
