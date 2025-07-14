variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "East US"
}

variable "owtf_ui_port" {
  description = "Port for OWTF UI"
  type        = string
  default     = "8019"
}

variable "owtf_admin_port" {
  description = "Port for OWTF admin interface"
  type        = string
  default     = "8008"
}

variable "owtf_proxy_port" {
  description = "Port for OWTF proxy"
  type        = string
  default     = "8010"
}

variable "vm_size" {
  description = "Size of the VM (free tier eligible)"
  type        = string
  default     = "Standard_B1s"
}

variable "disk_size_gb" {
  description = "Size of the OS disk in GB (free tier: up to 64GB Standard LRS)"
  type        = number
  default     = 64
  validation {
    condition     = var.disk_size_gb >= 30 && var.disk_size_gb <= 64
    error_message = "Disk size must be between 30-64 GB for free tier Standard LRS."
  }
}

variable "vnet_address_space" {
  description = "Address space for the virtual network"
  type        = list(string)
  default     = ["10.1.0.0/16"]
}

variable "public_subnet_prefix" {
  description = "Address prefix for public subnet"
  type        = string
  default     = "10.1.1.0/24"
}

variable "private_subnet_prefix" {
  description = "Address prefix for private subnet"
  type        = string
  default     = "10.1.2.0/24"
}

variable "admin_username" {
  description = "Admin username for VM"
  type        = string
  default     = "azureuser"
  validation {
    condition     = length(var.admin_username) > 0 && var.admin_username != "admin" && var.admin_username != "root"
    error_message = "Admin username cannot be empty, 'admin', or 'root'."
  }
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "owtf-rg"
}

variable "allowed_ssh_cidr" {
  description = "CIDR blocks allowed for SSH access (default: your public IP)"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Change this to your public IP for security
}

variable "allowed_owtf_cidr" {
  description = "CIDR blocks allowed for OWTF access"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Change this to your public IP for security
}
