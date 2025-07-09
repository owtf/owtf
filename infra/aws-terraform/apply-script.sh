#!/bin/bash

# Define variables
FILE_TO_MODIFY="ec2.tf"

# Function to check if a command was successful
check_success() {
    if [ $? -ne 0 ]; then
        echo "Error occurred during $1. Exiting."
        exit 1
    fi
}

# Detect the operating system
OS_TYPE=$(uname)

# Function to run sed command based on OS
run_sed() {
    if [ "$OS_TYPE" = "Darwin" ]; then
        # macOS
        sed -i '' 's/dev\./dev.unsafe./' "$FILE_TO_MODIFY"
    else
        # Linux
        sed -i 's/dev\./dev.unsafe./' "$FILE_TO_MODIFY"
    fi
    check_success "sed command"
}

# Function to remove unsafe modifications
remove_unsafe() {
    if [ "$OS_TYPE" = "Darwin" ]; then
        # macOS
        sed -i '' 's/dev.unsafe./dev./' "$FILE_TO_MODIFY"
    else
        # Linux
        sed -i 's/dev.unsafe./dev./' "$FILE_TO_MODIFY"
    fi
    check_success "remove unsafe sed command"
}

# Function to check if unsafe modifications exist
check_unsafe() {
    if grep -q 'dev.unsafe.' "$FILE_TO_MODIFY"; then
        return 0  # Unsafe modifications found
    else
        return 1  # No unsafe modifications
    fi
}

# Check for unsafe modifications
if check_unsafe; then
    echo "Modifications found. Removing them..."
    remove_unsafe
else
    echo "No modifications found."
fi

# Prompt user for mode
read -p "Do you want to run in safe mode (yes/y/no/n)? " user_input

# Check user input and handle file modification
case "$user_input" in
    [yY][eE][sS]|[yY])
        echo "Running in safe mode. Skipping sed modification..."
        ;;
    [nN][oO]|[nN])
        echo "Running in unsafe mode..."
        # Modify the Terraform file using sed
        echo "Modifying file with sed..."
        run_sed
        ;;
    *)
        echo "Invalid input. Please enter 'yes', 'y', 'no', or 'n'."
        exit 1
        ;;
esac

# Format Terraform files
echo "Formatting Terraform files..."
terraform fmt
check_success "terraform fmt"

# Initialize Terraform
echo "Initializing Terraform..."
terraform init
check_success "terraform init"

# Validate Terraform files
echo "Validating Terraform configuration..."
terraform validate
check_success "terraform validate"

# Plan Terraform changes
echo "Planning Terraform changes..."
terraform plan
check_success "terraform plan"