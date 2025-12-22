# Shortify

A modern, fast, and scalable URL shortening service with analytics. Built with FastAPI and designed for easy deployment with Docker.

## ✨ Features

- **URL Shortening** - Generate short, shareable links instantly
- **User Management** - JWT-based authentication with user profiles
- **Analytics Dashboard** - Track clicks, locations, devices, and referrers
- **Expiration Support** - Set custom expiration dates for URLs
- **Redis Caching** - Lightning-fast redirects with intelligent caching
- **Admin Panel** - Built-in admin interface powered by SQLAdmin
- **Visit Tracking** - Monitor application traffic with geo-location data
- **Bulk Operations** - Delete multiple URLs efficiently
- **IP-based Geolocation** - Track user locations with ipinfo.io integration

## 🛠️ Tech Stack

**Backend**
- FastAPI - High-performance async web framework
- PostgreSQL - Reliable relational database
- Redis - In-memory caching for fast redirects
- SQLAlchemy - Robust ORM with Alembic migrations
- JWT - Secure token-based authentication

**Frontend**
- React - Modern UI framework

## 🚀 Quick Start

- See [DOCKER_SETUP.md](DOCKER_SETUP.md) for detailed Docker setup instructions
- For environment variable details, see `.env.example`

### Prerequisites

- Docker and Docker Compose installed
- `.env` file with required environment variables

### Run with Docker

```bash
# Clone the repository
git clone https://github.com/Pratik8999/shortify.git
cd shortify

# Start all services
docker-compose up -d
```

Access the application at `http://localhost`

## 📦 Project Structure

```
.
├── app/
│   ├── auth/          # Authentication & authorization
│   ├── url/           # URL shortening logic
│   ├── visit/         # Visit tracking
│   ├── admin/         # Admin panel
│   ├── models.py      # Database models
│   └── main.py        # FastAPI application
├── migrations/        # Alembic migrations
├── nginx/            # Nginx configuration
├── docker-compose.yml
└── Dockerfile
```

## 📄 License

MIT License - feel free to use this project for personal or commercial purposes.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
