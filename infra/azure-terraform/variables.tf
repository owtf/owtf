variable "location" {
  default = "East US"
}

variable "owtf_ui_port" {
  default = "8019"
}

variable "owtf_admin_port" {
  default = "8008"
}

variable "owtf_proxy_port" {
  default = "8010"
}

variable "vm_size" {
  default = "Standard_B1s"  # Free tier eligible
}

variable "disk_size_gb" {
  default = 30
}

variable "vnet_address_space" {
  default = ["10.1.0.0/16"]
}

variable "public_subnet_prefix" {
  default = "10.1.1.0/24"
}

variable "private_subnet_prefix" {
  default = "10.1.2.0/24"
}

variable "admin_username" {
  default = "azureuser"
}

variable "resource_group_name" {
  default = "owtf-rg"
}
