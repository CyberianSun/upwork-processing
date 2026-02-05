# PostgreSQL Setup Guide

**Purpose**: Database configuration for upwork-processing app
**Last Updated**: 2026-02-05

---

## Available PostgreSQL Instances

### Local PostgreSQL Service (Recommended)

| Property | Value |
|----------|-------|
| **Cluster** | PostgreSQL 16-main |
| **Status** | ✓ Active and running |
| **Location** | Local machine |
| **Connection Command** | `psql -U postgres -d postgres -h localhost -p 5432` |

**Default Credentials** (may need to verify):
- User: `postgres`
- Database: `postgres`
- Host: `localhost`
- Port: `5432`

---

### Docker Containers (Alternative Options)

| Container | Image | Status | Use |
|-----------|-------|--------|-----|
| **coolify-db** | postgres:15-alpine | Healthy (3 days) | Coolify's database |
| **postgresql-bs8c...** | postgres:16-alpine | Healthy (3 days) | Other application |
| **supabase** | supabase/postgres:17.4.1 | Unhealthy | Supabase database |
| **authentik-postgres** | Custom | Healthy (3 days) | Authentik auth |

---

## Recommended Setup

### Option 1: Create New Database on Local Service (Recommended)

**Why**: Clean separation from other applications. Easy to manage.

**Steps**:

1. **Connect to PostgreSQL**:
   ```bash
   psql -U postgres -h localhost
   ```

2. **Create database**:
   ```sql
   CREATE DATABASE upwork_processing;
   ```

3. **Create user** (optional, for better security):
   ```sql
   CREATE USER upwork_user WITH PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE upwork_processing TO upwork_user;
   ```

4. **Verify connection**:
   ```bash
   psql -U upwork_user -d upwork_processing -h localhost
   # or
   psql -U postgres -d upwork_processing -h localhost
   ```

5. **Set DATABASE_URL in .env**:
   ```bash
   DATABASE_URL=postgresql+asyncpg://upwork_user:your_secure_password@localhost:5432/upwork_processing
   # or simpler (default postgres user):
   DATABASE_URL=postgresql+asyncpg://postgres:your_postgres_password@localhost:5432/upwork_processing
   ```

---

### Option 2: Use Coolify Database (For VPS Deployment)

**Why**: Already configured, will be used when deploying to VPS via Coolify.

**Steps**:

1. **Connect to coolify-db container**:
   ```bash
   docker exec -it coolify-db psql -U postgres
   ```

2. **Create database**:
   ```sql
   CREATE DATABASE upwork_processing;
   ```

3. **Note credentials** (check Coolify dashboard):
   - User: `postgres` (or check container env)
   - Password: (check Coolify dashboard)
   - Host: `localhost` (from app container perspective)
   - Port: `5432`

4. **Set DATABASE_URL** (for VPS deployment):
   ```bash
   DATABASE_URL=postgresql+asyncpg://postgres:coolify_password@localhost:5432/upwork_processing
   ```

---

### Option 3: Standalone Docker Container (Isolated Development)

**Why**: Complete isolation, easy to reset/snapshot.

**Steps**:

1. **Run PostgreSQL container**:
   ```bash
   docker run -d \
     --name upwork-postgres \
     -e POSTGRES_DB=upwork_processing \
     -e POSTGRES_USER=upwork_user \
     -e POSTGRES_PASSWORD=your_secure_password \
     -p 5433:5432 \
     postgres:16-alpine
   ```

2. **Set DATABASE_URL**:
   ```bash
   DATABASE_URL=postgresql+asyncpg://upwork_user:your_secure_password@localhost:5433/upwork_processing
   ```

---

## Docker Compose Integration

### docker-compose.yml (Multi-container Setup)

```yaml
services:
  app:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    environment:
      - DATABASE_URL=postgresql+asyncpg://upwork_user:secure_password@postgres:5432/upwork_processing
      - CEREBRAS_API_KEY=${CEREBRAS_API_KEY}
    depends_on:
      - postgres
    ports:
      - "8000:8000"

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=upwork_processing
      - POSTGRES_USER=upwork_user
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U upwork_user -d upwork_processing"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

**Run**:
```bash
docker-compose up --build
```

---

## Migration Setup (Alembic)

### Initialize Alembic

```bash
# After database is set up
alembic init alembic
```

### Configure alembic.ini

```ini
# sqlalchemy.url = postgresql+asyncpg://upwork_user:your_secure_password@localhost:5432/upwork_processing
sqlalchemy.url = postgresql+asyncpg://postgres:your_password@localhost:5432/upwork_processing
```

### Create First Migration

```bash
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

---

## Environment Variables (.env)

### Required Database Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://upwork_user:your_secure_password@localhost:5432/upwork_processing

# Alternative (using default postgres user)
# DATABASE_URL=postgresql+asyncpg://postgres:your_postgres_password@localhost:5432/upwork_processing

# SSL/TLS (if required for production)
# DATABASE_URL=postgresql+asyncpg://upwork_user:your_secure_password@localhost:5432/upwork_processing?sslmode=require
```

---

## Connection Testing

### Test Python Connection

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://upwork_user:your_secure_password@localhost:5432/upwork_processing"

async def test_connection():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute("SELECT version()")
        print(result.fetchone())

    await engine.dispose()

asyncio.run(test_connection())
```

---

## For VPS Deployment (Coolify)

### Coolify Integration

When deploying to VPS via Coolify:

1. **Service Settings**:
   - **Database**: Use Coolify's managed PostgreSQL service
   - **Environment Variable**: `DATABASE_URL` will be auto-injected by Coolify

2. **Coolify Docker Compose**:
   ```yaml
   services:
     app:
       image: your-app:latest
       environment:
         - DATABASE_URL=${POSTGRES_URL}  # Coolify injects this
   ```

3. **Database Backup**:
   - Coolify provides automated backups
   - Access via Coolify dashboard > Databases

---

## pgvector Extension (RAG Support)

### Enable pgvector (after database creation)

```sql
-- Connect to database
\c upwork_processing

-- Enable extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify
\dx vector
```

### Verify pgvector Installation

```bash
docker exec -it your-postgres-container psql -U upwork_user -d upwork_processing -c "\dx vector"
```

---

## Troubleshooting

### Connection Refused

**Check service status**:
```bash
systemctl status postgresql@16-main
```

**Check if port is listening**:
```bash
sudo netstat -tlnp | grep 5432
```

**Check PostgreSQL logs**:
```bash
sudo journalctl -u postgresql@16-main -f
```

---

### Permission Denied

**Check pg_hba.conf**:
```bash
sudo cat /etc/postgresql/16/main/pg_hba.conf
```

**Should have**:
```
# IPv4 local connections
host    all             all             127.0.0.1/32            scram-sha-256
```

---

### Docker Container Issues

**View logs**:
```bash
docker logs coolify-db
```

**Connect to container**:
```bash
docker exec -it coolify-db psql -U postgres
```

---

## Summary

**Recommended Setup**: Create new `upwork_processing` database on local PostgreSQL service.

**Quick Setup**:
```bash
# 1. Create database
psql -U postgres -h localhost -c "CREATE DATABASE upwork_processing;"

# 2. Set environment variable
export DATABASE_URL="postgresql+asyncpg://postgres:your_password@localhost:5432/upwork_processing"

# 3. Test connection
python -c "import asyncio; from sqlalchemy.ext.asyncio import create_async_engine; asyncio.run(create_async_engine('$DATABASE_URL').connect())"
```

---

**Document Created**: 2026-02-05
**Status**: Ready for database setup
**Next**: Create database when ready to implement