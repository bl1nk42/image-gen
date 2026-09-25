# Deployment Guide

This guide provides detailed instructions for deploying the Image Generation Microservice in various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Production Considerations](#production-considerations)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)

## Prerequisites

### Google Cloud Setup

1. **Create a Google Cloud Project**
   ```bash
   gcloud projects create your-project-id
   gcloud config set project your-project-id
   ```

2. **Enable Required APIs**
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable storage.googleapis.com
   ```

3. **Create a Service Account**
   ```bash
   gcloud iam service-accounts create image-generation-sa \
     --display-name="Image Generation Service Account"
   ```

4. **Grant Required Permissions**
   ```bash
   gcloud projects add-iam-policy-binding your-project-id \
     --member="serviceAccount:image-generation-sa@your-project-id.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"

   gcloud projects add-iam-policy-binding your-project-id \
     --member="serviceAccount:image-generation-sa@your-project-id.iam.gserviceaccount.com" \
     --role="roles/storage.admin"
   ```

5. **Create and Download Service Account Key**
   ```bash
   gcloud iam service-accounts keys create service-account-key.json \
     --iam-account=image-generation-sa@your-project-id.iam.gserviceaccount.com
   ```

6. **Create Cloud Storage Bucket**
   ```bash
   gsutil mb gs://your-image-bucket
   gsutil iam ch allUsers:objectViewer gs://your-image-bucket
   ```

## Local Development

### Setup

1. **Clone and Install**
   ```bash
   git clone <repository-url>
   cd image-generation-service
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env`:
   ```env
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_BUCKET=your-image-bucket
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
   REDIS_URL=redis://localhost:6379  # Optional
   CACHE_EXPIRATION_HOURS=24
   API_HOST=0.0.0.0
   API_PORT=8000
   ```

3. **Start Redis (Optional)**
   ```bash
   # Using Docker
   docker run -d -p 6379:6379 redis:7-alpine
   
   # Or install locally
   # Ubuntu/Debian: sudo apt install redis-server
   # macOS: brew install redis
   ```

4. **Run the Service**
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Testing

```bash
# Health check
curl http://localhost:8000/health

# Generate image
curl -X POST http://localhost:8000/v1/images/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over mountains",
    "style": "photorealistic",
    "aspect_ratio": "16:9"
  }'
```

## Docker Deployment

### Single Container

1. **Build Image**
   ```bash
   docker build -t image-generation-service:latest .
   ```

2. **Run Container**
   ```bash
   docker run -d \
     --name image-generation-service \
     -p 8000:8000 \
     -e GOOGLE_CLOUD_PROJECT=your-project-id \
     -e GOOGLE_CLOUD_BUCKET=your-image-bucket \
     -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account-key.json \
     -v /path/to/service-account-key.json:/app/credentials/service-account-key.json:ro \
     image-generation-service:latest
   ```

### Docker Compose

1. **Setup Credentials**
   ```bash
   mkdir credentials
   cp /path/to/service-account-key.json credentials/
   ```

2. **Configure Environment**
   ```bash
   export GOOGLE_CLOUD_PROJECT=your-project-id
   export GOOGLE_CLOUD_BUCKET=your-image-bucket
   ```

3. **Deploy**
   ```bash
   docker-compose up -d
   ```

4. **Check Status**
   ```bash
   docker-compose ps
   docker-compose logs -f image-generation-service
   ```

## Cloud Deployment

### Google Cloud Run

1. **Build and Push to Container Registry**
   ```bash
   # Configure Docker for GCR
   gcloud auth configure-docker
   
   # Build and tag
   docker build -t gcr.io/your-project-id/image-generation-service:latest .
   
   # Push
   docker push gcr.io/your-project-id/image-generation-service:latest
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy image-generation-service \
     --image gcr.io/your-project-id/image-generation-service:latest \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars GOOGLE_CLOUD_PROJECT=your-project-id \
     --set-env-vars GOOGLE_CLOUD_BUCKET=your-image-bucket \
     --memory 2Gi \
     --cpu 2 \
     --timeout 300 \
     --max-instances 10
   ```

### Google Kubernetes Engine (GKE)

1. **Create Cluster**
   ```bash
   gcloud container clusters create image-generation-cluster \
     --zone us-central1-a \
     --num-nodes 3 \
     --machine-type e2-standard-2
   ```

2. **Create Kubernetes Manifests**
   
   `k8s/deployment.yaml`:
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: image-generation-service
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: image-generation-service
     template:
       metadata:
         labels:
           app: image-generation-service
       spec:
         containers:
         - name: image-generation-service
           image: gcr.io/your-project-id/image-generation-service:latest
           ports:
           - containerPort: 8000
           env:
           - name: GOOGLE_CLOUD_PROJECT
             value: "your-project-id"
           - name: GOOGLE_CLOUD_BUCKET
             value: "your-image-bucket"
           resources:
             requests:
               memory: "1Gi"
               cpu: "500m"
             limits:
               memory: "2Gi"
               cpu: "1000m"
   ```
   
   `k8s/service.yaml`:
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: image-generation-service
   spec:
     selector:
       app: image-generation-service
     ports:
     - port: 80
       targetPort: 8000
     type: LoadBalancer
   ```

3. **Deploy**
   ```bash
   kubectl apply -f k8s/
   ```

## Production Considerations

### Security

1. **Use Workload Identity (GKE)**
   ```bash
   # Create Kubernetes Service Account
   kubectl create serviceaccount image-generation-ksa
   
   # Bind to Google Service Account
   gcloud iam service-accounts add-iam-policy-binding \
     --role roles/iam.workloadIdentityUser \
     --member "serviceAccount:your-project-id.svc.id.goog[default/image-generation-ksa]" \
     image-generation-sa@your-project-id.iam.gserviceaccount.com
   
   # Annotate Kubernetes Service Account
   kubectl annotate serviceaccount image-generation-ksa \
     iam.gke.io/gcp-service-account=image-generation-sa@your-project-id.iam.gserviceaccount.com
   ```

2. **Network Security**
   - Use VPC with private subnets
   - Configure firewall rules
   - Enable Cloud Armor for DDoS protection

3. **Secrets Management**
   - Use Google Secret Manager
   - Avoid hardcoding credentials
   - Rotate keys regularly

### Scaling

1. **Horizontal Pod Autoscaler (HPA)**
   ```yaml
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: image-generation-hpa
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: image-generation-service
     minReplicas: 3
     maxReplicas: 20
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70
   ```

2. **Redis Cluster for Caching**
   ```bash
   # Deploy Redis cluster
   helm repo add bitnami https://charts.bitnami.com/bitnami
   helm install redis bitnami/redis-cluster
   ```

### Monitoring

1. **Health Checks**
   ```yaml
   livenessProbe:
     httpGet:
       path: /health
       port: 8000
     initialDelaySeconds: 30
     periodSeconds: 10
   
   readinessProbe:
     httpGet:
       path: /health
       port: 8000
     initialDelaySeconds: 5
     periodSeconds: 5
   ```

2. **Logging**
   - Use structured logging (JSON format)
   - Configure log levels appropriately
   - Use Google Cloud Logging for centralized logs

3. **Metrics**
   - Monitor request latency
   - Track cache hit/miss ratios
   - Monitor resource utilization

## Monitoring and Maintenance

### Key Metrics to Monitor

1. **Application Metrics**
   - Request rate and latency
   - Error rates
   - Cache hit/miss ratio
   - Image generation success rate

2. **Infrastructure Metrics**
   - CPU and memory utilization
   - Network I/O
   - Storage usage
   - Container restart count

3. **Business Metrics**
   - API usage patterns
   - Cost per image generated
   - User satisfaction metrics

### Maintenance Tasks

1. **Regular Updates**
   - Update base images
   - Update dependencies
   - Security patches

2. **Cost Optimization**
   - Monitor Vertex AI usage
   - Optimize cache settings
   - Review storage lifecycle policies

3. **Performance Tuning**
   - Adjust cache expiration
   - Optimize container resources
   - Fine-tune autoscaling parameters

### Backup and Disaster Recovery

1. **Configuration Backup**
   - Store configurations in version control
   - Backup environment variables
   - Document deployment procedures

2. **Data Backup**
   - Regular backup of generated images
   - Cache data backup strategy
   - Database backups (if applicable)

3. **Disaster Recovery Plan**
   - Multi-region deployment
   - Automated failover procedures
   - Recovery time objectives (RTO)
   - Recovery point objectives (RPO)

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   ```bash
   # Check service account permissions
   gcloud projects get-iam-policy your-project-id
   
   # Verify credentials
   gcloud auth activate-service-account --key-file=service-account-key.json
   ```

2. **Storage Issues**
   ```bash
   # Check bucket permissions
   gsutil iam get gs://your-image-bucket
   
   # Test upload
   echo "test" | gsutil cp - gs://your-image-bucket/test.txt
   ```

3. **Performance Issues**
   - Check cache hit rates
   - Monitor resource utilization
   - Review API quotas and limits

### Log Analysis

```bash
# Docker logs
docker logs image-generation-service

# Kubernetes logs
kubectl logs -f deployment/image-generation-service

# Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision"
```

This deployment guide provides comprehensive instructions for deploying the Image Generation Microservice across different environments. Choose the deployment method that best fits your requirements and infrastructure.

