data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["${var.ubuntu_ami_name}"]
  }

  filter {
    name   = "virtualization-type"
    values = ["${var.virt_type}"]
  }

  owners = ["${var.canonical_account}"]
}

resource "aws_security_group" "owtf_sg" {
  name   = "owtf_sg"
  vpc_id = aws_vpc.vpc.id

  ingress {
    from_port   = var.owtf_admin_port
    to_port     = var.owtf_admin_port
    protocol    = "tcp"
    cidr_blocks = [var.cidr_block]
  }
  ingress {
    from_port   = var.owtf_ui_port
    to_port     = var.owtf_ui_port
    protocol    = "tcp"
    cidr_blocks = [var.cidr_block]
  }
  ingress {
    from_port   = var.owtf_proxy_port
    to_port     = var.owtf_proxy_port
    protocol    = "tcp"
    cidr_blocks = [var.cidr_block]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.cidr_block]
  }
}

resource "aws_instance" "ec2" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  associate_public_ip_address = false
  subnet_id                   = aws_subnet.private_subnet.id
  vpc_security_group_ids      = ["${aws_security_group.owtf_sg.id}"]
  iam_instance_profile        = aws_iam_instance_profile.ec2_instance_profile.name

  root_block_device {
    delete_on_termination = true
    encrypted             = true
    volume_size           = var.volume_size
    volume_type           = var.volume_type
  }

  metadata_options {
    http_put_response_hop_limit = 2
    http_tokens                 = "required"
  }

  tags = {
    "Name" = "owtf_instance"
  }

  user_data  = <<-EOF
              #!/bin/bash
              LOGFILE=/var/log/setup.log
              exec > >(tee -a $LOGFILE) 2>&1
              sudo apt update -y && sudo apt upgrade -y && sudo apt autoremove -y
              sudo snap install amazon-ssm-agent --classic
              sudo snap start amazon-ssm-agent
              sudo apt install awscli software-properties-common apt-transport-https ca-certificates curl git docker-compose make -y
              curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
              echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
              sudo apt-cache policy docker-ce && sudo apt install docker-ce -y
              sudo usermod -aG docker ssm-user
              sudo systemctl restart docker
              git clone https://github.com/owtf/owtf.git
              cd owtf && docker-compose -f docker/docker-compose.dev.yml up --build -d
              EOF
  depends_on = [aws_lb.alb, aws_vpc.vpc]
}

resource "null_resource" "wait_for_ec2" {
  provisioner "local-exec" {
    command = <<EOT
    sleep 360
    EOT
  }
  depends_on = [aws_instance.ec2]
}