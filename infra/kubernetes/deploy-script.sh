#!/bin/bash

# OWTF Kubernetes Deployment Script
echo "========================================="
echo "OWTF Kubernetes Deployment Script"
echo "========================================="
echo ""

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker and try again."
        exit 1
    fi
    echo "✅ Docker is running"
}

# Function to build and push Docker images
build_and_push_images() {
    echo ""
    echo "🔨 Building Docker Images..."
    echo "================================"
    
    # Build backend image
    echo "Building backend image..."
    docker build -f infra/kubernetes/Dockerfile.backend -t "$USERNAME/owtf-backend:latest" .
    if [ $? -ne 0 ]; then
        echo "❌ Backend image build failed"
        exit 1
    fi
    echo "✅ Backend image built successfully"
    
    # Build frontend image  
    echo "Building frontend image..."
    docker build -f infra/kubernetes/Dockerfile.frontend -t "$USERNAME/owtf-frontend:latest" .
    if [ $? -ne 0 ]; then
        echo "❌ Frontend image build failed"
        exit 1
    fi
    echo "✅ Frontend image built successfully"
    
    echo ""
    echo "📤 Pushing Images to Registry..."
    echo "================================="
    
    # Push backend image
    echo "Pushing backend image..."
    docker push "$USERNAME/owtf-backend:latest"
    if [ $? -ne 0 ]; then
        echo "❌ Backend image push failed"
        exit 1
    fi
    echo "✅ Backend image pushed successfully"
    
    # Push frontend image
    echo "Pushing frontend image..."
    docker push "$USERNAME/owtf-frontend:latest"
    if [ $? -ne 0 ]; then
        echo "❌ Frontend image push failed"
        exit 1
    fi
    echo "✅ Frontend image pushed successfully"
    
    echo ""
    echo "📋 Verifying pushed images..."
    echo "============================="
    echo "Backend image: ${USERNAME}/owtf-backend:latest"
    echo "Frontend image: ${USERNAME}/owtf-frontend:latest"
    
    # Verify images exist in registry
    if docker manifest inspect "${USERNAME}/owtf-backend:latest" >/dev/null 2>&1; then
        echo "✅ Backend image verified in registry"
    else
        echo "⚠️  Backend image verification failed"
    fi
    
    if docker manifest inspect "${USERNAME}/owtf-frontend:latest" >/dev/null 2>&1; then
        echo "✅ Frontend image verified in registry"
    else
        echo "⚠️  Frontend image verification failed"
    fi
}

# Function to apply Kubernetes deployments
apply_deployment() {
    echo ""
    echo "🚀 Deploying to Kubernetes..."
    echo "=============================="
    
    # Create namespace if it doesn't exist
    echo "Creating namespace 'owtf'..."
    kubectl create namespace owtf --dry-run=client -o yaml | kubectl apply -f -
    
    echo "Applying database manifests..."
    kubectl apply -f db-secret.yaml
    kubectl apply -f db-pvc.yaml
    kubectl apply -f db-deployment.yaml
    kubectl apply -f db-service.yaml
    
    echo "Applying OWTF PVC..."
    kubectl apply -f owtf-pvc.yaml
    
    # Update image names in deployment files
    echo "Updating image references..."
    
    # Create temporary copies and update image references
    cp owtf-backend-deployment.yaml owtf-backend-deployment.yaml.bak
    cp owtf-frontend-deployment.yaml owtf-frontend-deployment.yaml.bak
    
    # Replace backend image reference
    sed -i "s|image: .*/owtf-backend:.*|image: ${USERNAME}/owtf-backend:latest|g" owtf-backend-deployment.yaml
    
    # Replace frontend image reference  
    sed -i "s|image: .*/owtf-frontend:.*|image: ${USERNAME}/owtf-frontend:latest|g" owtf-frontend-deployment.yaml
    
    echo "✅ Updated image references to use ${USERNAME}/owtf-backend:latest and ${USERNAME}/owtf-frontend:latest"
    
    # Verify the changes were applied
    echo ""
    echo "📋 Verifying deployment image references..."
    echo "Backend deployment image: $(grep 'image:' owtf-backend-deployment.yaml | head -1 | awk '{print $2}')"
    echo "Frontend deployment image: $(grep 'image:' owtf-frontend-deployment.yaml | head -1 | awk '{print $2}')"
    
    echo "Applying backend deployment..."
    kubectl apply -f owtf-backend-deployment.yaml
    kubectl apply -f owtf-backend-service.yaml
    
    echo "Applying frontend deployment..."
    kubectl apply -f owtf-frontend-deployment.yaml
    kubectl apply -f owtf-frontend-service.yaml
    
    echo "Applying ingress..."
    kubectl apply -f owtf-ingress.yaml
    
    # Restore original files
    mv owtf-backend-deployment.yaml.bak owtf-backend-deployment.yaml
    mv owtf-frontend-deployment.yaml.bak owtf-frontend-deployment.yaml
    
    echo ""
    echo "✅ Deployment completed successfully!"
    echo ""
    echo "📊 Service Information:"
    echo "======================="
    echo "- Frontend: Available via LoadBalancer on port 8019"
    echo "- Backend API: Available via ClusterIP on port 8008"
    echo "- Backend Proxy: Available via ClusterIP on port 8010"
    echo "- Database: Available via ClusterIP on port 5432"
    echo ""
    echo "🔍 Check deployment status with:"
    echo "kubectl get pods -n owtf"
    echo "kubectl get services -n owtf"
    echo "kubectl get ingress -n owtf"
}

# Main execution
echo "This script will:"
echo "1. Build Docker images for backend and frontend"
echo "2. Push images to Docker registry"
echo "3. Deploy to Kubernetes cluster"
echo ""

# Check prerequisites
check_docker

# Get Docker credentials
read -p "Enter Docker username: " USERNAME
read -sp "Enter Docker password: " PASSWORD
echo
read -p "Enter Docker email: " EMAIL

# Validate inputs
if [[ -z "$USERNAME" || -z "$PASSWORD" || -z "$EMAIL" ]]; then
    echo "❌ All fields are required. Exiting."
    exit 1
fi

# Docker login
echo ""
echo "🔐 Logging into Docker Hub..."
echo "$PASSWORD" | docker login -u "$USERNAME" --password-stdin
if [ $? -ne 0 ]; then
    echo "❌ Docker login failed. Please check your credentials."
    exit 1
fi
echo "✅ Docker login successful"

# Ask user if they want to proceed
echo ""
read -p "Do you want to proceed with building and deploying? (yes/y or no/n): " PROCEED
PROCEED=$(echo "$PROCEED" | tr '[:upper:]' '[:lower:]')

if [[ "$PROCEED" != "yes" && "$PROCEED" != "y" ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Navigate to kubernetes directory if not already there
if [[ ! -f "owtf-backend-deployment.yaml" ]]; then
    if [[ -d "infra/kubernetes" ]]; then
        echo "Changing to kubernetes directory..."
        cd infra/kubernetes
    else
        echo "❌ Cannot find kubernetes manifests. Please run from project root or kubernetes directory."
        exit 1
    fi
fi

# Execute main functions
build_and_push_images
apply_deployment

echo ""
echo "🎉 OWTF deployment complete!"
echo "Check the ingress for external access or use port-forward for testing."
