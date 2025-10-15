# SentimentAgent Backend Systemd Service

## Installation

### 1. Create Service User

```bash
sudo useradd -r -s /bin/false sentimentagent
```

### 2. Install Application

```bash
# Create directory
sudo mkdir -p /opt/sentimentagent
sudo chown sentimentagent:sentimentagent /opt/sentimentagent

# Copy application files
sudo cp -r backend /opt/sentimentagent/
sudo chown -R sentimentagent:sentimentagent /opt/sentimentagent/backend

# Install Python dependencies
cd /opt/sentimentagent/backend
sudo pip3 install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy and edit environment file
sudo cp /opt/sentimentagent/backend/.env.example /opt/sentimentagent/backend/.env
sudo nano /opt/sentimentagent/backend/.env

# Set proper permissions
sudo chown sentimentagent:sentimentagent /opt/sentimentagent/backend/.env
sudo chmod 600 /opt/sentimentagent/backend/.env
```

### 4. Install Systemd Service

```bash
# Copy service file
sudo cp deployment/systemd/sentimentagent.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable sentimentagent.service
```

### 5. Start Service

```bash
# Start the service
sudo systemctl start sentimentagent.service

# Check status
sudo systemctl status sentimentagent.service

# View logs
sudo journalctl -u sentimentagent.service -f
```

## Service Management

### Check Status
```bash
sudo systemctl status sentimentagent.service
```

### Start/Stop/Restart
```bash
sudo systemctl start sentimentagent.service
sudo systemctl stop sentimentagent.service
sudo systemctl restart sentimentagent.service
```

### View Logs
```bash
# Follow logs
sudo journalctl -u sentimentagent.service -f

# Recent logs
sudo journalctl -u sentimentagent.service -n 100
```

## Monitoring

Check service health:
```bash
curl http://localhost:8000/api/v1/health
```

See full documentation in deployment/systemd/README.md
