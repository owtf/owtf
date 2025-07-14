resource "tls_private_key" "main" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "local_file" "private_key" {
  content         = tls_private_key.main.private_key_pem
  filename        = "${path.module}/ssh-keys/owtf-key"
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

  tags = {
    environment = "owtf"
  }
}

resource "null_resource" "owtf_setup" {
  depends_on = [azurerm_linux_virtual_machine.main, local_file.private_key]

  provisioner "local-exec" {
    command = <<EOT
      sleep 120;
      > inventory.ini;
      echo "[all]" | tee -a inventory.ini;
      echo "${azurerm_public_ip.main.ip_address} ansible_user=${var.admin_username} ansible_ssh_private_key_file=ssh-keys/owtf-key ansible_python_interpreter=/usr/bin/python3" | tee -a inventory.ini;
      export ANSIBLE_HOST_KEY_CHECKING=False;
      ansible-playbook -i inventory.ini owtf-setup.yml
    EOT
  }
}
