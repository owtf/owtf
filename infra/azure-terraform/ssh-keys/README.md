# SSH Keys Directory

This directory will store the SSH key pair generated for the OWTF VM.

After running `terraform apply`, the SSH keys will be stored here:
- `owtf-key` - Private key file

## Usage

SSH to the VM using:
```bash
ssh -i ssh-keys/owtf-key azureuser@<vm-public-ip>
```

**Important**: 
- Keep the private key secure and never commit it to version control
- The `.gitignore` should exclude `ssh-keys/owtf-key`
