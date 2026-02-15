output "public_ip_address" {
  value       = azurerm_public_ip.main.ip_address
  description = "The public IP address of the OWTF instance"
}

output "owtf_url" {
  value       = "http://${azurerm_public_ip.main.ip_address}:${var.owtf_ui_port}"
  description = "URL to access OWTF web interface"
}

output "ssh_connection_command" {
  value       = "ssh -i ssh-keys/owtf-key ${var.admin_username}@${azurerm_public_ip.main.ip_address}"
  description = "SSH command to connect to the VM"
}

output "owtf_admin_url" {
  value       = "http://${azurerm_public_ip.main.ip_address}:${var.owtf_admin_port}"
  description = "URL to access OWTF admin interface"
}

output "owtf_proxy_url" {
  value       = "http://${azurerm_public_ip.main.ip_address}:${var.owtf_proxy_port}"
  description = "URL to access OWTF proxy interface"
}

output "debug_commands" {
  value = {
    ssh_connect    = "ssh -i ssh-keys/owtf-key ${var.admin_username}@${azurerm_public_ip.main.ip_address}"
    ansible_rerun  = "export ANSIBLE_HOST_KEY_CHECKING=False && ansible-playbook -i inventory.ini owtf-setup.yml"
    setup_complete = "ssh -i ssh-keys/owtf-key ${var.admin_username}@${azurerm_public_ip.main.ip_address} 'ls -la /var/log/owtf-setup-complete'"
    docker_status  = "ssh -i ssh-keys/owtf-key ${var.admin_username}@${azurerm_public_ip.main.ip_address} 'sudo docker ps'"
    owtf_logs      = "ssh -i ssh-keys/owtf-key ${var.admin_username}@${azurerm_public_ip.main.ip_address} 'cd owtf && docker compose logs'"
  }
  description = "Debug commands to monitor OWTF setup progress"
}
