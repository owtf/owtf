## OWTF Kubernetes Deployment

This directory contains Kubernetes manifests and a helper script to build images and deploy the OWTF (Offensive Web Testing Framework) stack. The deployment script now supports two flows:

1. Push Mode: Build images, push them to a Docker registry (e.g. Docker Hub), patch manifests to use those images, deploy.
2. Local Mode: Build images locally (tagged `owtf:backend` and `owtf:frontend`), optionally load them into a kind cluster, deploy using existing manifests (imagePullPolicy: Never).

### Prerequisites ###

Kubernetes Cluster: Ensure you have a running Kubernetes cluster using [Kind](https://kind.sigs.k8s.io/), [Minikube](https://minikube.sigs.k8s.io/docs/start/)
Kubectl: Make sure [kubectl](https://kubernetes.io/docs/tasks/tools/) is installed and configured to interact with your Kubernetes cluster.

Docker: Required for building images (both push and local modes). Kind optional (only used to preload images when not pushing to a registry).

Storage: As we will be building and storing images and data associated with them, please make sure you have 30 GB of space (excluding OS occupied space)

1. **Using Kind Cluster (simple example)**

        Create a basic kind cluster:

                kind create cluster

        (Optional) If you need host port mappings or extra config, adjust with a config file per kind docs.

2. **Using Minikube Cluster**

        Install Minikube (see official docs) then start:

                minikube start --driver=docker

        Verify cluster components:

                kubectl get nodes

        (Optional) If you plan to build images directly inside minikube's Docker daemon:

                eval $(minikube docker-env)


### Deployment Steps ###

1. **Clone the Repository**

    First, clone the repository containing the deployment script and Kubernetes manifests:

        git clone https://github.com/owtf/owtf.git

2. **Execute the Deployment Script**

    From the project root or this directory run:

        bash infra/kubernetes/deploy-script.sh

    You will be asked:
    * Push images to a registry? (y/n)
    * (If yes) Docker username, password, optional email, tag (default: latest)
    * Confirm to proceed with build & deploy

    Push Mode does:
    * Docker login (password via stdin)
    * Build backend & frontend images: `<username>/owtf-backend:<tag>`, `<username>/owtf-frontend:<tag>`
    * Push images
    * Patch deployment manifests (temporarily) to use pushed images
    * Apply secrets, PVCs, DB deployment & service, frontend ConfigMap, backend & frontend deployments/services
    * Restore original manifest files locally

    Local Mode does:
    * Build local images `owtf:backend` and `owtf:frontend`
    * If `kind` installed and default cluster exists, load images into kind nodes
    * Apply manifests without altering image references (uses `imagePullPolicy: Never`)

    Notes:
    * The script currently applies `owtf-frontend-configmap.yaml` if present.
    * No ingress manifest is included by default; expose services via port-forward or add an ingress separately.
    * Backend depends on Postgres; there is no readiness wait loop yet—consider adding one for production.

3. **Verify Deployment**

        Check resources:

                kubectl get all -n owtf

        Port-forward services to gain access to Application (run each in its own terminal or background them):

        Frontend (UI):

                kubectl port-forward svc/owtf-frontend-service -n owtf 8019:8019

        Backend (API, proxy) – all ports in one command:

                kubectl port-forward svc/owtf-backend-service -n owtf 8008:8008 8009:8009 8010:8010

Essential access summary:
* UI: http://localhost:8019/
* API: http://localhost:8009/
* Proxy: http://localhost:8010/

4. **Logs & Debugging**

                kubectl logs deployment/owtf-backend -n owtf
                kubectl logs deployment/owtf-frontend -n owtf
                kubectl logs deployment/db -n owtf

        For a specific pod:

                kubectl logs <pod-name> -n owtf

        Describe resources for troubleshooting:

                kubectl describe pod <pod-name> -n owtf
                kubectl describe deployment owtf-backend -n owtf

5. **Cleaning Up**

                kubectl delete namespace owtf

6. **SMTP Verification Note**

        If SMTP isn’t configured, check backend pod logs to retrieve any verification link needed during login.

7. **Future Enhancements (Not Yet Implemented)**
        * Auto-wait for Postgres readiness.
        * Readiness/liveness probes (currently commented in deployment YAMLs).
        * Optional NetworkPolicies & Ingress TLS.
        * ImagePullPolicy adjustment when using pushed images.

For questions or support, please open a GitHub issue.
