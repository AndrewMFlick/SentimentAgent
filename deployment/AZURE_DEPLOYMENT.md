# Azure Deployment Guide

This guide covers deploying the Reddit Sentiment Analysis app to Azure.

## Deployment Options

### Option 1: Azure Container Apps (Recommended)

Azure Container Apps provides a serverless container platform ideal for this application.

#### Prerequisites
- Azure CLI installed
- Azure subscription
- Docker installed

#### Steps

1. **Create Resource Group**
```bash
az group create --name sentiment-analysis-rg --location eastus
```

2. **Create Container Registry**
```bash
az acr create --resource-group sentiment-analysis-rg \
  --name sentimentregistry --sku Basic
```

3. **Build and Push Images**
```bash
# Login to ACR
az acr login --name sentimentregistry

# Build backend
docker build -f deployment/docker/Dockerfile.backend -t sentimentregistry.azurecr.io/sentiment-backend:latest .
docker push sentimentregistry.azurecr.io/sentiment-backend:latest

# Build frontend
docker build -f deployment/docker/Dockerfile.frontend -t sentimentregistry.azurecr.io/sentiment-frontend:latest .
docker push sentimentregistry.azurecr.io/sentiment-frontend:latest
```

4. **Create Container Apps Environment**
```bash
az containerapp env create \
  --name sentiment-env \
  --resource-group sentiment-analysis-rg \
  --location eastus
```

5. **Deploy Backend**
```bash
az containerapp create \
  --name sentiment-backend \
  --resource-group sentiment-analysis-rg \
  --environment sentiment-env \
  --image sentimentregistry.azurecr.io/sentiment-backend:latest \
  --target-port 8000 \
  --ingress external \
  --secrets \
    reddit-client-id=${REDDIT_CLIENT_ID} \
    reddit-client-secret=${REDDIT_CLIENT_SECRET} \
    cosmos-endpoint=${COSMOS_ENDPOINT} \
    cosmos-key=${COSMOS_KEY} \
  --env-vars \
    REDDIT_CLIENT_ID=secretref:reddit-client-id \
    REDDIT_CLIENT_SECRET=secretref:reddit-client-secret \
    COSMOS_ENDPOINT=secretref:cosmos-endpoint \
    COSMOS_KEY=secretref:cosmos-key
```

6. **Deploy Frontend**
```bash
az containerapp create \
  --name sentiment-frontend \
  --resource-group sentiment-analysis-rg \
  --environment sentiment-env \
  --image sentimentregistry.azurecr.io/sentiment-frontend:latest \
  --target-port 80 \
  --ingress external
```

### Option 2: Azure Kubernetes Service (AKS)

For more control and scalability, use AKS.

1. **Create AKS Cluster**
```bash
az aks create \
  --resource-group sentiment-analysis-rg \
  --name sentiment-aks \
  --node-count 2 \
  --enable-addons monitoring \
  --generate-ssh-keys
```

2. **Get Credentials**
```bash
az aks get-credentials --resource-group sentiment-analysis-rg --name sentiment-aks
```

3. **Create Secrets**
```bash
kubectl create secret generic sentiment-secrets \
  --from-literal=reddit-client-id=${REDDIT_CLIENT_ID} \
  --from-literal=reddit-client-secret=${REDDIT_CLIENT_SECRET} \
  --from-literal=cosmos-endpoint=${COSMOS_ENDPOINT} \
  --from-literal=cosmos-key=${COSMOS_KEY}
```

4. **Deploy Application**
```bash
kubectl apply -f deployment/azure/kubernetes-deployment.yaml
```

## Required Azure Resources

### 1. CosmosDB
```bash
az cosmosdb create \
  --name sentiment-cosmos \
  --resource-group sentiment-analysis-rg \
  --default-consistency-level Session \
  --locations regionName=eastus
```

### 2. Azure OpenAI (Optional)
```bash
az cognitiveservices account create \
  --name sentiment-openai \
  --resource-group sentiment-analysis-rg \
  --kind OpenAI \
  --sku S0 \
  --location eastus
```

## Monitoring and Logging

### Enable Application Insights
```bash
az monitor app-insights component create \
  --app sentiment-insights \
  --location eastus \
  --resource-group sentiment-analysis-rg
```

### View Logs
```bash
# Container Apps
az containerapp logs show --name sentiment-backend --resource-group sentiment-analysis-rg

# AKS
kubectl logs -f deployment/sentiment-backend
```

## Scaling

### Container Apps Auto-scaling
```bash
az containerapp update \
  --name sentiment-backend \
  --resource-group sentiment-analysis-rg \
  --min-replicas 1 \
  --max-replicas 5
```

## Cost Optimization

- Start with Container Apps Basic tier
- Use Azure Cosmos DB serverless for development
- Enable auto-scaling to scale down during low usage
- Monitor costs with Azure Cost Management
