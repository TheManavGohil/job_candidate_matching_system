# Azure Production Deployment Guide

This document details the deployment strategy for the Job-Candidate Matching Engine, covering both the current live initial deployment and the fully optimized production architecture using Azure managed services.

## Current Initial Deployment (VM-Based)

The application has been initially deployed on an Azure Virtual Machine to demonstrate end-to-end functionality in a live environment. It runs the entire docker-compose stack (Frontend, API, Postgres, Redis, Celery).

- **Frontend Application:** [https://4.213.115.86:3000](https://4.213.115.86:3000)
- **Backend API Docs (Swagger):** [http://4.213.115.86:8000/docs](http://4.213.115.86:8000/docs)

While this approach works perfectly for demonstration and testing, running everything on a single node introduces single points of failure and scaling bottlenecks. To achieve true production-grade resilience and scale to handle millions of candidates, we recommend migrating to the managed cloud architecture outlined below.

---

## Fully Optimized Azure Production Architecture

Moving from a single VM to **managed microservices** is the standard approach for a scalable, decoupled, and highly available system. This architecture leverages Azure's managed services to handle load dynamically and guarantee uptime.

### 🏛️ Architecture Overview
1. **Azure Static Web Apps**: Hosts the React frontend with global CDN distribution.
2. **Azure Container Apps**: Serverless container execution for the FastAPI backend and Celery background workers. Scales instantly based on HTTP traffic or queue length.
3. **Azure Database for PostgreSQL (Flexible Server)**: Managed, highly available relational database for storing job descriptions, candidate profiles, and raw parsed data.
4. **Azure Cache for Redis**: High-performance distributed cache used as the Celery message broker and for caching API match results.
5. **Azure Files Share**: Centralized network storage mounted to both the API and Celery workers to share the generated FAISS indexes.

### 🛠️ Required Code Modifications for Cloud

Before transitioning from local `docker-compose` to Azure Managed Services, the following adjustments are required:

#### 1. Frontend Routing (CORS & API URL)
Instead of relying on Nginx reverse proxying inside a single Docker network, the React application must be built using Azure Static Web Apps. The `VITE_API_URL` environment variable is injected during the GitHub Actions build process to point to the live public URL of the backend Azure Container App.

#### 2. FAISS Shared Storage
In the VM deployment, FAISS indexes are stored in a local Docker volume. In the distributed cloud architecture, the `celery-worker` and `api-service` run in completely separate containers and environments.
- **Solution:** We create an **Azure Files Share** (in an Azure Storage Account) and mount it via SMB/NFS to both Container Apps at `/app/faiss_indexes`. When the Celery worker recalculates the embeddings and updates the FAISS files, the API service instantly sees the updated files.

---

## 🚀 Step-by-Step Production Deployment Plan

### Phase 1: Setup Managed Databases
1. **Azure Database for PostgreSQL**: 
   - Deploy a "Flexible Server" with connection pooling (PgBouncer) enabled.
2. **Azure Cache for Redis**:
   - Provision a standard Redis Cache instance to serve as the Celery broker and result backend.

### Phase 2: Create Azure Container Registry (ACR)
1. Provision an Azure Container Registry.
2. Configure Admin user access to allow Container Apps to pull images securely.

### Phase 3: Push Images to ACR
Authenticate and push the backend container:
```bash
docker login myregistry.azurecr.io -u <USERNAME> -p <PASSWORD>
docker build -t myregistry.azurecr.io/api:latest -f api/Dockerfile .
docker push myregistry.azurecr.io/api:latest
```

### Phase 4: Shared Storage for FAISS
1. Create an **Azure Storage account**.
2. Provision a **File share** named `faiss-index`.

### Phase 5: Deploy Azure Container Apps (ACA)
1. Create an **Azure Container Apps Environment**. Link the Azure File Share created above to this environment.
2. **Deploy the Backend API (`api-service`)**:
   - Create a Container App pulling the `api:latest` image.
   - Inject `DATABASE_URL` and `REDIS_URL` as secrets.
   - Mount the `faiss-index` file share to `/app/faiss_indexes`.
   - Enable **Ingress** targeting port `8000`.
3. **Deploy the Celery Worker (`celery-worker`)**:
   - Create a secondary Container App using the same `api:latest` image.
   - Override the startup command: `celery -A api.tasks worker --loglevel=info`
   - Mount the same `faiss-index` file share to `/app/faiss_indexes`.
   - Disable Ingress (background workers run asynchronously and do not accept HTTP requests).

### Phase 6: Deploy the Frontend
1. Push the React application code to GitHub.
2. Create an **Azure Static Web App** and link the repository.
3. Configure the build settings to inject the backend's Container App URL. Azure will automatically set up GitHub Actions to build and deploy the frontend to a global edge CDN.
