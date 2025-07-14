#!/bin/bash
# Ansible installation script for OWTF Azure deployment

set -e

echo "🚀 Installing Ansible for OWTF deployment..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists apt; then
            echo "ubuntu"
        elif command_exists yum; then
            echo "rhel"
        elif command_exists dnf; then
            echo "fedora"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Check if Ansible is already installed
if command_exists ansible; then
    echo "✅ Ansible is already installed!"
    ansible --version | head -n1
    echo ""
    echo "Ready to deploy OWTF. Run:"
    echo "  terraform init"
    echo "  terraform plan"
    echo "  terraform apply"
    exit 0
fi

# Detect operating system
OS=$(detect_os)
echo "🔍 Detected OS: $OS"

# Install Ansible based on OS
case $OS in
    "macos")
        echo "📦 Installing Ansible on macOS..."
        if command_exists brew; then
            echo "Using Homebrew..."
            brew install ansible
        elif command_exists pip3; then
            echo "Using pip3..."
            pip3 install --user ansible
        elif command_exists pip; then
            echo "Using pip..."
            pip install --user ansible
        else
            echo "❌ Neither Homebrew nor pip found. Please install one of them first:"
            echo "  - Homebrew: https://brew.sh/"
            echo "  - Python: https://www.python.org/downloads/"
            exit 1
        fi
        ;;
    
    "ubuntu")
        echo "📦 Installing Ansible on Ubuntu/Debian..."
        sudo apt update
        sudo apt install -y software-properties-common
        sudo add-apt-repository --yes --update ppa:ansible/ansible
        sudo apt install -y ansible
        ;;
    
    "rhel")
        echo "📦 Installing Ansible on RHEL/CentOS..."
        sudo yum install -y epel-release
        sudo yum install -y ansible
        ;;
    
    "fedora")
        echo "📦 Installing Ansible on Fedora..."
        sudo dnf install -y ansible
        ;;
    
    "linux")
        echo "📦 Installing Ansible using pip..."
        if command_exists pip3; then
            pip3 install --user ansible
        elif command_exists pip; then
            pip install --user ansible
        else
            echo "❌ pip not found. Please install Python and pip first."
            exit 1
        fi
        ;;
    
    "windows")
        echo "🪟 Windows detected..."
        echo "For Windows, please use one of these options:"
        echo "1. Windows Subsystem for Linux (WSL) - Recommended"
        echo "2. Install Python and run: pip install ansible"
        echo "3. Use Docker: docker run --rm -it quay.io/ansible/ansible-runner"
        exit 1
        ;;
    
    *)
        echo "❓ Unknown OS detected. Trying pip installation..."
        if command_exists pip3; then
            pip3 install --user ansible
        elif command_exists pip; then
            pip install --user ansible
        else
            echo "❌ Cannot determine how to install Ansible on this system."
            echo "Please install Ansible manually: https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html"
            exit 1
        fi
        ;;
esac

# Verify installation
echo ""
echo "🔍 Verifying Ansible installation..."
if command_exists ansible; then
    echo "✅ Ansible installed successfully!"
    ansible --version | head -n1
    
    # Add to PATH if needed (for user installs)
    if [[ "$OS" == "macos" ]] || [[ "$OS" == "linux" ]]; then
        if ! command_exists ansible; then
            echo "⚠️  Ansible installed but not in PATH. You may need to add it manually."
            echo "For macOS/Linux with pip --user install, add this to your ~/.bashrc or ~/.zshrc:"
            echo "export PATH=\"\$HOME/.local/bin:\$PATH\""
        fi
    fi
else
    echo "❌ Ansible installation failed!"
    exit 1
fi

echo ""
echo "🎉 Setup complete! You can now deploy OWTF with:"
echo ""
echo "  1. Configure variables:"
echo "     cp terraform.tfvars.example terraform.tfvars"
echo "     # Edit terraform.tfvars as needed"
echo ""
echo "  2. Deploy infrastructure:"
echo "     terraform init"
echo "     terraform plan"
echo "     terraform apply"
echo ""
echo "  3. Access OWTF at the URLs shown in terraform outputs"
echo ""
echo "💡 Tip: The deployment will take ~10-15 minutes for complete OWTF setup"
