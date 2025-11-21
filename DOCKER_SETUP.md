# Docker Setup Guide - Production-Grade Security

This guide explains how to set up the FPAS project using Docker with production-grade security practices.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Git

## Initial Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd fpas
```

### 2. Configure Environment Variables

**Important**: Never commit the `.env` file to version control!

```bash
# Copy the example file
cp .env.example .env

# Edit the .env file with your actual credentials
nano .env  # or use your preferred editor
```

### 3. Required Environment Variables

Edit your `.env` file and replace all `CHANGE_ME_*` values:

```env
# Neo4j Database - REQUIRED
NEO4J_PASSWORD=<your-secure-password>
NEO4J_AUTH=neo4j/<your-secure-password>

# OpenAI API - REQUIRED
OPENAI_API_KEY=<your-openai-api-key>

# API Security - REQUIRED
API_SECRET_KEY=<generate-random-secret-key>
```

**Generate a secure API secret key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Start the Services

```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 5. Access the Application

Once all services are healthy:

- **Frontend**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474

## Security Best Practices

### Environment Variables

1. **Never commit `.env` file** - It contains sensitive credentials
2. **Use strong passwords** - Minimum 16 characters, mix of letters, numbers, symbols
3. **Rotate credentials regularly** - Update passwords periodically
4. **Limit access** - Only share credentials with authorized team members

### Docker Security

1. **Non-root users** - All containers run as non-root users (UID 1000)
2. **Health checks** - All services have health checks for monitoring
3. **Network isolation** - Services communicate via internal Docker network
4. **Volume permissions** - Proper ownership and permissions on mounted volumes

### Production Deployment

For production environments, consider:

1. **Docker Secrets** (if using Docker Swarm):
   ```bash
   echo "your-password" | docker secret create neo4j_password -
   ```

2. **External secret management**:
   - HashiCorp Vault
   - AWS Secrets Manager
   - Azure Key Vault
   - Google Cloud Secret Manager

3. **Container registry**:
   - Use private registry for images
   - Scan images for vulnerabilities
   - Use image signing

4. **Network security**:
   - Use reverse proxy (nginx, traefik)
   - Enable TLS/SSL certificates
   - Configure firewalls

## Troubleshooting

### Maps Not Showing in Frontend

If maps don't render:

1. Check Streamlit config exists: `frontend/.streamlit/config.toml`
2. Verify CORS is enabled in config
3. Check browser console for errors
4. Restart frontend container: `docker-compose restart frontend`

### Database Connection Issues

If services can't connect to Neo4j:

1. Check Neo4j health: `docker-compose ps neo4j`
2. View Neo4j logs: `docker-compose logs neo4j`
3. Verify credentials in `.env` match `NEO4J_AUTH` format
4. Wait for Neo4j initialization (can take 60-120 seconds)

### Permission Errors

If you see permission errors:

```bash
# Fix ownership of volumes
sudo chown -R 1000:1000 ./neo4j ./cache ./logs
```

## Development vs Production

### Development (current setup)
- Fallback default values in docker-compose.yml
- `.env` file for configuration
- Source code mounted as volumes
- Debug logging enabled

### Production (recommended changes)
1. Remove all fallback default values from docker-compose.yml
2. Use external secret management
3. Copy code into container (no volume mounts)
4. Set `LOG_LEVEL=WARNING` or `ERROR`
5. Enable monitoring and alerting
6. Use container orchestration (Kubernetes, Docker Swarm)

## Maintenance

### Update Dependencies

```bash
# Rebuild containers with latest dependencies
docker-compose build --no-cache

# Restart services
docker-compose up -d
```

### Backup Data

```bash
# Backup Neo4j data
docker run --rm --volumes-from fpas-neo4j -v $(pwd):/backup ubuntu tar czf /backup/neo4j-backup.tar.gz /data

# Backup logs
docker run --rm --volumes-from fpas-api -v $(pwd):/backup ubuntu tar czf /backup/logs-backup.tar.gz /app/logs
```

### Clean Up

```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: deletes data!)
docker-compose down -v

# Remove unused images
docker image prune -a
```

## Support

For issues or questions:
1. Check logs: `docker-compose logs <service-name>`
2. Review documentation in `docs/` directory
3. Open an issue on GitHub

---

**Remember**: Security is an ongoing process. Keep your dependencies updated, rotate credentials regularly, and follow security best practices.
