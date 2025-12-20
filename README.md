# Shortify

**Shortify** is a scalable URL shortening service built with **FastAPI**, **PostgreSQL**, **Redis**, and **Celery**.  
It supports per-user short links, click analytics, caching, and asynchronous background tasks. Designed for easy deployment with Docker and AWS.

---

## 🚀 Features

- Create short URLs for any long link
- Per-user URL management
- Click tracking & analytics
- Expiration support for short URLs
- Redis caching for fast redirects
- Celery-powered async tasks for analytics and cleanup
- Optional AWS Lambda integration for scheduled maintenance
- Clean, minimal frontend for managing links (React or Jinja2 templates)

---

## 🧰 Tech Stack

- **Backend:** FastAPI  
- **Database:** PostgreSQL  
- **Cache:** Redis  
- **Task Queue:** Celery  
- **Containerization:** Docker & Docker Compose  
- **Frontend:** React / Jinja2 templates  
- **Cloud Deployment:** AWS EC2  
- **Optional:** AWS Lambda for scheduled jobs

---


## Executable permissions for the deployment files
- chmod +x deploy_first_time.sh deploy_update.sh
