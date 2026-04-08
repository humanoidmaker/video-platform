# Video Platform

Video hosting platform with channels, playlists, comments, and content management.

## Tech Stack

Python FastAPI + SQLAlchemy + PostgreSQL + React + MinIO + Redis

## Features

- **Video upload and processing**
- **Channel management**
- **Playlist creation**
- **Comment system with replies**
- **Like/dislike system**
- **Subscription system**
- **Category and tag management**
- **Video search**
- **Watch history tracking**
- **Creator analytics**

## Setup

### Using Docker (Recommended)

```bash
docker-compose up
```

### Manual Setup

**Backend:**
```bash
cd backend
pip install -r requirements.txt
# Set environment variables (copy .env.example to .env)
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Seed Data:**
```bash
cd backend
python -m scripts.seed_admin
python -m scripts.seed_sample_data
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description | Default |
|----------|-------------|---------|
| MONGODB_URI / DATABASE_URL | Database connection string | localhost |
| JWT_SECRET | Secret key for JWT tokens | (required) |
| CORS_ORIGINS | Allowed frontend origins | http://localhost:3000 |
| SMTP_HOST | SMTP server for emails | (optional) |
| SMTP_PORT | SMTP port | 587 |
| SMTP_USER | SMTP username | (optional) |
| SMTP_PASS | SMTP password | (optional) |

## Default Login

- **Admin:** admin@video.local / admin123

## License

MIT License — Copyright (c) 2026 Humanoid Maker (www.humanoidmaker.com)


## Deployment

### Docker Compose (Easiest)

```bash
# Clone the repository
git clone https://github.com/humanoidmaker/video-platform.git
cd video-platform

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### PM2 (Production Process Manager)

```bash
# Install PM2 globally
npm install -g pm2

# Install dependencies
cd backend && pip install -r requirements.txt && cd ..
cd frontend && npm install && cd ..

# Start all services
pm2 start ecosystem.config.js

# Monitor
pm2 monit

# View logs
pm2 logs

# Stop all
pm2 stop all

# Auto-restart on reboot
pm2 startup
pm2 save
```

### Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml

# Check status
kubectl get pods -n video-platform

# View logs
kubectl logs -f deployment/backend -n video-platform

# Scale
kubectl scale deployment/backend --replicas=3 -n video-platform
```

### Manual Setup

**1. Database:**
```bash
# Start PostgreSQL
pg_ctl start
```

**2. Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv/Scripts/activate  # Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your database URL and secrets


uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**3. Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**4. Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## License

MIT License — Copyright (c) 2026 Humanoid Maker (www.humanoidmaker.com)
