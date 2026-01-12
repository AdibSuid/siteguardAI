# Deployment Guide - SiteGuard AI

This guide covers deployment options for SiteGuard AI in various environments.

## Table of Contents

- [Streamlit Cloud](#streamlit-cloud)
- [Docker Deployment](#docker-deployment)
- [AWS Deployment](#aws-deployment)
- [Google Cloud Platform](#google-cloud-platform)
- [Azure Deployment](#azure-deployment)
- [Production Considerations](#production-considerations)

## Streamlit Cloud

### Prerequisites
- GitHub repository
- Streamlit Cloud account
- API keys (OpenAI/Gemini)

### Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to https://share.streamlit.io
   - Click "New app"
   - Select your repository
   - Main file: `app/streamlit_app.py`
   - Python version: 3.10

3. **Configure Secrets**
   In Streamlit Cloud dashboard, add secrets:
   ```toml
   OPENAI_API_KEY = "sk-..."
   GEMINI_API_KEY = "..."
   CONFIDENCE_THRESHOLD = "0.5"
   LOG_LEVEL = "INFO"
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait for build to complete
   - Your app will be live at: `https://your-app.streamlit.app`

### Custom Domain
```bash
# In Streamlit Cloud settings
Custom domain: siteguard.yourdomain.com
```

## Docker Deployment

### Local Docker

1. **Build Image**
   ```bash
   docker build -t siteguard-ai:latest .
   ```

2. **Run Container**
   ```bash
   docker run -d \
     -p 8501:8501 \
     -p 8000:8000 \
     -e OPENAI_API_KEY="your-key" \
     --name siteguard \
     siteguard-ai:latest
   ```

3. **Access Application**
   - Streamlit: http://localhost:8501
   - API: http://localhost:8000

### Docker Compose

1. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your keys
   ```

2. **Start Services**
   ```bash
   docker-compose up -d
   ```

3. **View Logs**
   ```bash
   docker-compose logs -f
   ```

4. **Stop Services**
   ```bash
   docker-compose down
   ```

## AWS Deployment

### EC2 Instance

1. **Launch EC2 Instance**
   - AMI: Ubuntu 22.04 LTS
   - Instance type: t3.medium or larger
   - Security group: Allow ports 8501, 8000, 22

2. **Connect and Setup**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker ubuntu
   
   # Clone repository
   git clone https://github.com/yourusername/siteguard-ai.git
   cd siteguard-ai
   
   # Configure
   cp .env.example .env
   nano .env  # Add your API keys
   
   # Deploy
   docker-compose up -d
   ```

3. **Configure Nginx (Optional)**
   ```bash
   sudo apt install nginx -y
   sudo nano /etc/nginx/sites-available/siteguard
   ```
   
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
       }
       
       location /api {
           proxy_pass http://localhost:8000;
       }
   }
   ```

4. **Enable Site**
   ```bash
   sudo ln -s /etc/nginx/sites-available/siteguard /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

### ECS (Elastic Container Service)

1. **Push to ECR**
   ```bash
   aws ecr create-repository --repository-name siteguard-ai
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
   
   docker build -t siteguard-ai .
   docker tag siteguard-ai:latest YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/siteguard-ai:latest
   docker push YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/siteguard-ai:latest
   ```

2. **Create ECS Task Definition**
   ```json
   {
     "family": "siteguard-ai",
     "containerDefinitions": [
       {
         "name": "siteguard",
         "image": "YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/siteguard-ai:latest",
         "portMappings": [
           {"containerPort": 8501},
           {"containerPort": 8000}
         ],
         "environment": [
           {"name": "OPENAI_API_KEY", "value": "your-key"}
         ]
       }
     ]
   }
   ```

3. **Deploy Service**
   ```bash
   aws ecs create-service \
     --cluster siteguard-cluster \
     --service-name siteguard-service \
     --task-definition siteguard-ai \
     --desired-count 1
   ```

## Google Cloud Platform

### Cloud Run

1. **Build and Push**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/siteguard-ai
   ```

2. **Deploy**
   ```bash
   gcloud run deploy siteguard-ai \
     --image gcr.io/PROJECT_ID/siteguard-ai \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars OPENAI_API_KEY=your-key
   ```

3. **Access**
   - Your service URL will be provided
   - Configure custom domain in Cloud Run settings

### Compute Engine

Similar to AWS EC2 deployment:

1. **Create VM**
   ```bash
   gcloud compute instances create siteguard-vm \
     --machine-type n1-standard-2 \
     --image-family ubuntu-2204-lts \
     --image-project ubuntu-os-cloud
   ```

2. **SSH and Setup**
   ```bash
   gcloud compute ssh siteguard-vm
   # Follow EC2 setup steps
   ```

## Azure Deployment

### Container Instances

1. **Login**
   ```bash
   az login
   ```

2. **Create Container Registry**
   ```bash
   az acr create --resource-group myResourceGroup \
     --name siteguardregistry --sku Basic
   ```

3. **Build and Push**
   ```bash
   az acr build --registry siteguardregistry \
     --image siteguard-ai:latest .
   ```

4. **Deploy**
   ```bash
   az container create \
     --resource-group myResourceGroup \
     --name siteguard-ai \
     --image siteguardregistry.azurecr.io/siteguard-ai:latest \
     --dns-name-label siteguard-ai \
     --ports 8501 8000 \
     --environment-variables OPENAI_API_KEY=your-key
   ```

## Production Considerations

### Security

1. **Environment Variables**
   - Never commit API keys
   - Use secrets management (AWS Secrets Manager, Azure Key Vault)
   - Rotate keys regularly

2. **HTTPS**
   ```bash
   # Install certbot
   sudo apt install certbot python3-certbot-nginx
   
   # Get certificate
   sudo certbot --nginx -d your-domain.com
   ```

3. **Rate Limiting**
   - Implement API rate limiting
   - Use Redis for distributed rate limiting
   - Monitor API usage

### Monitoring

1. **Application Monitoring**
   ```python
   # Add Sentry
   import sentry_sdk
   sentry_sdk.init(dsn="your-sentry-dsn")
   ```

2. **Infrastructure Monitoring**
   - CloudWatch (AWS)
   - Cloud Monitoring (GCP)
   - Azure Monitor
   - Or use Prometheus + Grafana

3. **Logging**
   - Centralized logging (ELK stack, CloudWatch Logs)
   - Log rotation
   - Error alerting

### Performance

1. **Scaling**
   - Horizontal scaling with load balancer
   - Auto-scaling based on CPU/memory
   - Consider GPU instances for faster inference

2. **Caching**
   ```python
   # Redis caching
   import redis
   cache = redis.Redis(host='localhost', port=6379)
   ```

3. **Optimization**
   - Use ONNX for faster inference
   - Batch processing
   - Async API endpoints

### Backup

1. **Database Backup**
   ```bash
   # Automated backup
   crontab -e
   0 2 * * * /path/to/backup_script.sh
   ```

2. **Model Versioning**
   - Version control for models
   - A/B testing capabilities
   - Rollback procedures

### CI/CD

1. **GitHub Actions**
   ```yaml
   name: Deploy
   on:
     push:
       branches: [main]
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Deploy to Streamlit
           run: |
             # Your deployment script
   ```

2. **Automated Testing**
   - Run tests before deployment
   - Integration tests
   - Load testing

## Health Checks

```python
# Add to your application
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }
```

## Support

For deployment issues:
- Check logs: `docker-compose logs`
- Verify environment variables
- Test API keys
- Check firewall rules
- Monitor resource usage

---

**Need help?** Open an issue or contact: adibcom.as@gmail.com