# Docker Setup Guide

This guide explains how to set up and run Shortify using Docker and Docker Compose.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 2.0 or higher)

### Installing Docker

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install docker.io docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker
```

**macOS:**
```bash
brew install --cask docker
```

**Windows:**
Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop)

## 🔧 Configuration

### 1. Clone the Repository

```bash
git clone https://github.com/Pratik8999/shortify.git
cd shortify
```

### 2. Create Environment File

Create a `.env` file in the project root:

```bash
touch .env
```

Add the following environment variables:

```env
# PostgreSQL Configuration
POSTGRES_USER=shortify_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=url_shortener
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# JWT Configuration
JWT_SECRET_KEY=your_super_secret_jwt_key_change_this_in_production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# IPInfo API (for geolocation)
IPINFO_ENDPOINT=https://ipinfo.io
IPINFO_API_KEY=your_ipinfo_api_key_here

# Admin Panel Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_admin_password_here

# Application Settings
BASE_URL=http://localhost
ENVIRONMENT=production
```

**Important:** Replace all placeholder values with secure credentials.

### 3. Get IPInfo API Key (Required)

Geolocation features require an IPInfo API key. Sign up for a free API key at [ipinfo.io](https://ipinfo.io/signup) and add it to your `.env` file.

## 🚀 Running the Application

### Option 1: Using Pre-built Images (Recommended)

The `docker-compose.yml` uses pre-built images from Docker Hub:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### Option 2: Building from Source

If you want to build the backend image locally:

```bash
# Build and start services
docker-compose up -d --build

# Or build only the backend
docker build -t your-username/url-shortener-backend:latest .
```

## 📦 Services Overview

The Docker Compose stack includes:

| Service | Port | Description |
|---------|------|-------------|
| **nginx** | 80 | Reverse proxy and frontend server |
| **app** | 8000 | FastAPI backend (internal) |
| **db** | 5432 | PostgreSQL database |
| **redis** | 6379 | Redis cache |
| **frontend** | - | React frontend (served by nginx) |

## 🔍 Accessing the Application

Once all services are running:

- **Frontend:** http://localhost
- **API Docs:** http://localhost/api/docs
- **Admin Panel:** http://localhost/admin

## 🛠️ Common Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f db
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes all data)
docker-compose down -v
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart app
```

### Execute Commands in Containers

```bash
# Access backend shell
docker-compose exec app bash

# Access PostgreSQL
docker-compose exec db psql -U shortify_user -d url_shortener

# Access Redis CLI
docker-compose exec redis redis-cli
```

### Database Migrations

```bash
# Run migrations
docker-compose exec app uv run alembic upgrade head

# Create new migration
docker-compose exec app uv run alembic revision --autogenerate -m "description"

# Rollback migration
docker-compose exec app uv run alembic downgrade -1
```

## 🔄 Updating the Application

### Pull Latest Images

```bash
# Stop services
docker-compose down

# Pull latest images
docker-compose pull

# Start with new images
docker-compose up -d
```

### Rebuild from Source

```bash
# Rebuild and restart
docker-compose up -d --build
```

## 🐛 Troubleshooting

### Port Already in Use

If port 80 is already in use, modify `docker-compose.yml`:

```yaml
nginx:
  ports:
    - "8080:80"  # Use port 8080 instead
```

### Database Connection Issues

Check if PostgreSQL is healthy:

```bash
docker-compose ps
docker-compose logs db
```

Ensure environment variables in `.env` match the database credentials.

### Redis Connection Issues

Verify Redis is running:

```bash
docker-compose exec redis redis-cli ping
# Should return: PONG
```

### View Backend Errors

```bash
docker-compose logs -f app
```

### Reset Everything

```bash
# Stop and remove all containers, networks, and volumes
docker-compose down -v

# Remove images (optional)
docker rmi pratik8999/url-shortener-backend:latest
docker rmi pratik8999/url-shortner-frontend:latest

# Start fresh
docker-compose up -d
```

## 📊 Health Checks

The compose file includes health checks for:

- **PostgreSQL:** Checks if database accepts connections
- **Redis:** Pings Redis server

Services dependent on these will wait until they're healthy before starting.

## 🔐 Security Best Practices

1. **Never commit `.env` file** - Add it to `.gitignore`
2. **Use strong passwords** - Especially for production
3. **Change default admin credentials** - After first login
4. **Use secrets in production** - Docker secrets or environment-specific configs
5. **Enable HTTPS** - Configure SSL certificates in nginx for production

## 🌐 Production Deployment

For production deployments:

1. Use a proper domain with SSL/TLS certificates
2. Configure nginx with SSL (Let's Encrypt recommended)
3. Use managed database services (AWS RDS, DigitalOcean Databases)
4. Use managed Redis (AWS ElastiCache, Redis Cloud)
5. Set up proper backup strategies
6. Configure monitoring and logging
7. Use Docker secrets or vault for sensitive data

### Example Production Nginx SSL Config

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # ... rest of config
}
```

## 📈 Monitoring

### View Container Stats

```bash
docker stats
```

### Check Disk Usage

```bash
docker system df
```

### Clean Up Unused Resources

```bash
# Remove unused containers, networks, images
docker system prune -a
```

## 🆘 Getting Help

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Verify environment variables in `.env`
3. Ensure all required ports are available
4. Check Docker and Docker Compose versions
5. Open an issue on GitHub with error logs

## 📝 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/docs/)
