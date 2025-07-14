resource "tls_private_key" "main" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "local_file" "private_key" {
  content  = tls_private_key.main.private_key_pem
  filename = "${path.module}/ssh-keys/owtf-key"
  file_permission = "0600"
}

resource "azurerm_ssh_public_key" "main" {
  name                = "owtf-ssh-key"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  public_key          = tls_private_key.main.public_key_openssh
}

resource "azurerm_linux_virtual_machine" "main" {
  name                = "owtf-vm"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  size                = var.vm_size
  admin_username      = var.admin_username

  disable_password_authentication = true

  network_interface_ids = [
    azurerm_network_interface.main.id,
  ]

  admin_ssh_key {
    username   = var.admin_username
    public_key = azurerm_ssh_public_key.main.public_key
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
    disk_size_gb         = var.disk_size_gb
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  custom_data = base64encode(<<-EOF
    #!/bin/bash
    LOGFILE=/var/log/setup.log
    exec > >(tee -a $LOGFILE) 2>&1
    
    # Update system
    apt update -y && apt upgrade -y
    
    # Install required packages
    apt install -y software-properties-common apt-transport-https ca-certificates curl git make
    
    # Install Docker
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io
    
    # Install Docker Compose
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Add user to docker group
    usermod -aG docker ${var.admin_username}
    
    # Start Docker
    systemctl enable docker
    systemctl start docker
    
    # Clone OWTF repository
    cd /home/${var.admin_username}
    git clone https://github.com/owtf/owtf.git
    chown -R ${var.admin_username}:${var.admin_username} owtf
    
    # Start OWTF
    cd owtf
    docker-compose -f docker/docker-compose.dev.yml up --build -d
    EOF
  )

  tags = {
    environment = "owtf"
  }
}

resource "null_resource" "wait_for_vm" {
  provisioner "local-exec" {
    command = "sleep 300"
  }
  depends_on = [azurerm_linux_virtual_machine.main]
}
