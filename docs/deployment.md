# Deployment Guide

This guide covers different options for deploying the DeepSeek Wrapper application in various environments.

## Local Deployment

### Running for Development

For local development, you can run the application with:

```bash
python -m src.deepseek_wrapper.main
```

This will start the application with auto-reload enabled for development purposes.

### Running for Production

For a more production-ready local deployment:

```bash
uvicorn src.deepseek_wrapper.main:app --host 0.0.0.0 --port 8000 --workers 4
```

This uses the Uvicorn ASGI server with multiple worker processes for better performance.

## Docker Deployment

### Building the Docker Image

1. Ensure Docker is installed on your system
2. Build the image:
   ```bash
   docker build -t deepseek-wrapper .
   ```

### Running with Docker

```bash
docker run -d -p 8000:8000 --env-file .env --name deepseek-wrapper deepseek-wrapper
```

This will:
- Run the container in detached mode (`-d`)
- Map port 8000 from the container to your host
- Use your local `.env` file for environment variables
- Name the container "deepseek-wrapper"

### Docker Compose

For easier management, you can use Docker Compose:

```yaml
# docker-compose.yml
version: '3'
services:
  deepseek-wrapper:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    volumes:
      - ./uploads:/app/uploads
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
```

## Cloud Deployment

### Deploying to Heroku

1. Install the Heroku CLI and login
2. Initialize a Git repository if not already done:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```
3. Create a Heroku app and deploy:
   ```bash
   heroku create deepseek-wrapper
   heroku config:set DEEPSEEK_API_KEY=your_api_key_here
   git push heroku main
   ```

### Deploying to AWS Elastic Beanstalk

1. Install the EB CLI and initialize your project:
   ```bash
   pip install awsebcli
   eb init
   ```
2. Create and deploy to an environment:
   ```bash
   eb create deepseek-wrapper-env
   ```
3. Set environment variables:
   ```bash
   eb setenv DEEPSEEK_API_KEY=your_api_key_here
   ```

### Deploying to Azure App Service

1. Install the Azure CLI and login:
   ```bash
   az login
   ```
2. Create an App Service and deploy:
   ```bash
   az webapp up --name deepseek-wrapper --resource-group your-resource-group --runtime "PYTHON:3.9"
   ```
3. Set environment variables:
   ```bash
   az webapp config appsettings set --name deepseek-wrapper --resource-group your-resource-group --settings DEEPSEEK_API_KEY=your_api_key_here
   ```

## Environment Variables

The following environment variables can be configured for deployment:

| Variable | Description | Default |
|----------|-------------|---------|
| `DEEPSEEK_API_KEY` | Your DeepSeek API key (required) | None |
| `HOST` | Host to bind the server to | 0.0.0.0 |
| `PORT` | Port to run the server on | 8000 |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |
| `UPLOAD_DIR` | Directory for file uploads | ./uploads |
| `MAX_UPLOAD_SIZE` | Maximum file upload size in MB | 10 |

## Scaling Considerations

For high-traffic deployments, consider:

1. Using a reverse proxy like Nginx in front of the application
2. Implementing Redis for session storage
3. Deploying with multiple workers/instances
4. Setting up a load balancer for horizontal scaling

## Security Recommendations

1. Always use HTTPS in production
2. Set up proper authentication if exposing to public internet
3. Keep your API key secure and use environment variables
4. Regularly update dependencies
5. Consider using a WAF (Web Application Firewall)

## Monitoring

For production deployments, set up monitoring:

1. Application logs
2. Server metrics (CPU, memory, disk usage)
3. Request/response times
4. Error rates

Popular monitoring tools include Prometheus, Grafana, or cloud provider monitoring services. 