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
