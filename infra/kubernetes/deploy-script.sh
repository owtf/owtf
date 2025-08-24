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

###############################################################################
# Image build functions
###############################################################################

# Determine correct Dockerfile paths (prefer docker/ directory if present)
BACKEND_DOCKERFILE="docker/Dockerfile.backend"
FRONTEND_DOCKERFILE="docker/Dockerfile.frontend"
if [[ ! -f "$BACKEND_DOCKERFILE" && -f "infra/kubernetes/Dockerfile.backend" ]]; then
    BACKEND_DOCKERFILE="infra/kubernetes/Dockerfile.backend"
fi
if [[ ! -f "$FRONTEND_DOCKERFILE" && -f "infra/kubernetes/Dockerfile.frontend" ]]; then
    FRONTEND_DOCKERFILE="infra/kubernetes/Dockerfile.frontend"
fi

build_and_push_images() {
        local username="$1" tag="$2"
        echo ""
        echo "🔨 Building Docker Images for push (tag: $tag)..."
        echo "================================"

        # Build backend image
        echo "Building backend image (registry)..."
        docker build -f "$BACKEND_DOCKERFILE" -t "$username/owtf-backend:$tag" . || { echo "❌ Backend image build failed"; exit 1; }
        echo "✅ Backend image built"

        # Build frontend image
        echo "Building frontend image (registry)..."
        docker build -f "$FRONTEND_DOCKERFILE" -t "$username/owtf-frontend:$tag" . || { echo "❌ Frontend image build failed"; exit 1; }
        echo "✅ Frontend image built"

        echo ""
        echo "📤 Pushing Images to Registry..."
        echo "================================="
        docker push "$username/owtf-backend:$tag" || { echo "❌ Backend image push failed"; exit 1; }
        docker push "$username/owtf-frontend:$tag" || { echo "❌ Frontend image push failed"; exit 1; }
        echo "✅ Images pushed"

        echo ""
        echo "📋 Verifying pushed images..."
        echo "============================="
        for img in backend frontend; do
            if docker manifest inspect "$username/owtf-$img:$tag" >/dev/null 2>&1; then
                echo "✅ $img image verified in registry"
            else
                echo "⚠️  $img image verification failed"
            fi
        done
}

build_local_images() {
        echo ""
        echo "� Building local Docker Images (no push)..."
        echo "================================"
        echo "Tagging as owtf:backend and owtf:frontend to match deployment manifests"

        docker build -f "$BACKEND_DOCKERFILE" -t owtf:backend . || { echo "❌ Backend image build failed"; exit 1; }
        echo "✅ Backend image built (owtf:backend)"
        docker build -f "$FRONTEND_DOCKERFILE" -t owtf:frontend . || { echo "❌ Frontend image build failed"; exit 1; }
        echo "✅ Frontend image built (owtf:frontend)"

        # Attempt to load into kind cluster if available
        if command -v kind >/dev/null 2>&1; then
            local KIND_CLUSTER_NAME=${KIND_CLUSTER_NAME:-kind}
            if kind get clusters 2>/dev/null | grep -q "^$KIND_CLUSTER_NAME$"; then
                echo "📦 Loading images into kind cluster '$KIND_CLUSTER_NAME'"
                kind load docker-image owtf:backend --name "$KIND_CLUSTER_NAME" || echo "⚠️  Failed to load owtf:backend into kind"
                kind load docker-image owtf:frontend --name "$KIND_CLUSTER_NAME" || echo "⚠️  Failed to load owtf:frontend into kind"
            else
                echo "ℹ️  kind cluster '$KIND_CLUSTER_NAME' not found (skipping kind load)"
            fi
        else
            echo "ℹ️  'kind' not installed; skipping loading images into kind nodes"
        fi
}

# Function to apply Kubernetes deployments
apply_deployment() {
    local pushed="$1" username="$2" tag="$3"
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
    
    echo "Applying OWTF PVC and frontend ConfigMap..."
    kubectl apply -f owtf-pvc.yaml
    kubectl apply -f owtf-frontend-configmap.yaml
    
        if [[ "$pushed" == "true" ]]; then
            echo "Updating image references to use registry images..."
            cp owtf-backend-deployment.yaml owtf-backend-deployment.yaml.bak
            cp owtf-frontend-deployment.yaml owtf-frontend-deployment.yaml.bak

            # Cross-platform sed (Linux vs macOS)
            if sed --version >/dev/null 2>&1; then
                SED_INPLACE=(sed -i)
            else
                SED_INPLACE=(sed -i '')
            fi

            # Replace only the image lines for containers
            "${SED_INPLACE[@]}" -E "s|image:.*owtf.*backend.*|image: ${username}/owtf-backend:${tag}|" owtf-backend-deployment.yaml
            "${SED_INPLACE[@]}" -E "s|image:.*owtf.*frontend.*|image: ${username}/owtf-frontend:${tag}|" owtf-frontend-deployment.yaml
            echo "✅ Updated deployment manifests to registry images"

            echo ""
            echo "📋 Verifying deployment image references..."
            echo "Backend deployment image: $(grep 'image:' owtf-backend-deployment.yaml | head -1 | awk '{print $2}')"
            echo "Frontend deployment image: $(grep 'image:' owtf-frontend-deployment.yaml | head -1 | awk '{print $2}')"
        else
            echo "Using local images (owtf:backend, owtf:frontend) as defined in manifests"
        fi
    
        echo "Applying backend deployment & service..."
        kubectl apply -f owtf-backend-deployment.yaml || exit 1
        kubectl apply -f owtf-backend-service.yaml || exit 1

        echo "Applying frontend deployment & service..."
        kubectl apply -f owtf-frontend-deployment.yaml || exit 1
        kubectl apply -f owtf-frontend-service.yaml || exit 1

        # Restore original files if we modified them
        if [[ "$pushed" == "true" ]]; then
            mv owtf-backend-deployment.yaml.bak owtf-backend-deployment.yaml
            mv owtf-frontend-deployment.yaml.bak owtf-frontend-deployment.yaml
        fi
    
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
echo "This script can:"
echo "1. Build & push images to a Docker registry, then deploy"
echo "2. OR build images locally & (optionally) load into a kind cluster, then deploy"
echo ""

# Check prerequisites
check_docker

read -p "Do you want to push images to a Docker registry? (y/n): " PUSH_CHOICE
PUSH_CHOICE=$(echo "$PUSH_CHOICE" | tr '[:upper:]' '[:lower:]')

PUSH_IMAGES=false
if [[ "$PUSH_CHOICE" == "y" || "$PUSH_CHOICE" == "yes" ]]; then
    PUSH_IMAGES=true
    read -p "Enter Docker username: " USERNAME
    read -sp "Enter Docker password: " PASSWORD; echo
    read -p "Enter Docker email (optional, press Enter to skip): " EMAIL
    read -p "Enter image tag (default: latest): " IMAGE_TAG
    IMAGE_TAG=${IMAGE_TAG:-latest}
    if [[ -z "$USERNAME" || -z "$PASSWORD" ]]; then
        echo "❌ Username and password required to push images. Exiting."
        exit 1
    fi
    echo ""
    echo "🔐 Logging into Docker registry (Docker Hub assumed)..."
    echo "$PASSWORD" | docker login -u "$USERNAME" --password-stdin || { echo "❌ Docker login failed"; exit 1; }
    echo "✅ Docker login successful"
else
    echo "Proceeding with local image build only (no push)."
fi

echo ""
read -p "Proceed with build & deploy now? (y/n): " PROCEED
PROCEED=$(echo "$PROCEED" | tr '[:upper:]' '[:lower:]')
if [[ "$PROCEED" != "y" && "$PROCEED" != "yes" ]]; then
    echo "Cancelled by user."; exit 0; fi

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

# Execute main functions based on choice
if [[ "$PUSH_IMAGES" == "true" ]]; then
    build_and_push_images "$USERNAME" "${IMAGE_TAG:-latest}"
    apply_deployment true "$USERNAME" "${IMAGE_TAG:-latest}"
else
    build_local_images
    apply_deployment false "" ""
fi

echo ""
echo "🎉 OWTF deployment complete!"
echo "Check the ingress for external access or use port-forward for testing."
