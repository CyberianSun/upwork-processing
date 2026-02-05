# PostgreSQL Setup - Actual Status Check

**Last Checked**: 2026-02-05 01:50 UTC
**Purpose**: Verify actual PostgreSQL installation and configuration

---

## What We Actually Have

### Local PostgreSQL Service (Active ✅)

| Property | Value |
|----------|-------|
| **Service** | postgresql@16-main |
| **Status** | ✅ Active and running (20h uptime) |
| **Version** | PostgreSQL 16.11 |
| **Listening** | 127.0.0.1:5432 (localhost only) |
| **Process** | `/usr/bin/pg_ctlcluster --skip-systemctl-redirect 16-main start` |

---

### Users & Databases

#### Users

| Role | Permissions |
|------|-------------|
| postgres | Superuser, Create role, Create DB, Replication, Bypass RLS |
| ytflow | Regular user (for other apps) |

#### Databases

| Name | Owner | Purpose |
|------|-------|---------|
| postgres | postgres | Default database |
| template0 | postgres | Template database |
| template1 | postgres | Template database |
| upwork_processing | postgres | ✅ Created for this app |
| yt_knowledge | ytflow | Other application database |

---

### pgvector Extension Status

| Property | Status |
|--------|--------|
| **Installed** | ❌ NO - Not available |
| **Extension File** | `/usr/share/postgresql/16/extension/vector.control` - Missing |
| **HDB Error** | `extension "vector" is not available` |

**What this means**:
- pgvector must be compiled and installed manually
- Cannot use via `CREATE EXTENSION vector` until installation is complete

---

### System Requirements for pgvector

| Component | Status |
|-----------|--------|
| **GCC** | ✅ 13.3.0 - Available |
| **pg_config** | ✅ PostgreSQL 16.11 - Available |
| **PostgreSQL headers** | Need to install `postgresql-server-dev-16` |

---

## Installation Options

### Option 1: Install pgvector from Source (Recommended)

**Steps**:

```bash
# 1. Install PostgreSQL development headers
sudo apt update
sudo apt install -y postgresql-server-dev-16 build-essential git

# 2. Clone pgvector repository
cd /tmp
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector

# 3. Compile and install
make
sudo make install

# 4. Enable extension in database
sudo -u postgres psql -d upwork_processing -c "CREATE EXTENSION vector;"

# 5. Verify
sudo -u postgres psql -d upwork_processing -c "\dx vector"
```

**Time required**: ~5 minutes

---

### Option 2: Use Vector Search Without pgvector (Alternative)

If pgvector installation fails, use alternative approaches:

| Alternative | Complexity | Notes |
|-------------|------------|-------|
| **Embedding in Python** | Medium | Use `numpy` + `faiss` for vector similarity search |
| **External Vector DB** | Low | Use Pinecone/Qdrant managed service |
| **PostgreSQL with similarity** | Low | Use text similarity functions (less accurate) |

**Recommendation**: Install pgvector for production. It's the best opion for self-hosted RAG.

---

### Option 3: Docker PostgreSQL with pgvector Pre-installed

If local installation fails, use Docker:

**Steps**:

```bash
docker run -d \
  --name upwork-postgres \
  -p 5433:5432 \
  -e POSTGRES_DB=upwork_processing \
  -e POSTGRES_PASSWORD=your_password \
  pgvector/pgvector:pg16
```

**Connection string**:
```
postgresql+asyncpg://postgres:your_password@localhost:5433/upwork_processing
```

**Time required**: ~2 minutes (pull image + start container)

---

## Current Connection Details

### Local Service (Recommended if pgvector installed)

```bash
# Connection string (no password required for postgres user on localhost)
DATABASE_URL=postgresql+asyncpg://postgres@localhost:5432/upwork_processing
```

**Test connection**:
```bash
sudo -u postgres psql -d upwork_processing -c "SELECT version();"
```

---

### Available Docker Containers (Alternative)

| Container | Image | Status | Connection |
|-----------|-------|--------|------------|
| postgresql-bs8c... | postgres:16-alpine | Healthy (3 days) | `docker exec -it postgresql-bs8c... psql -U postgres` |
| coolify-db | postgres:15-alpine | Healthy (3 days) | `docker exec -it coolify-db psql -U postgres` |

**Note**: These containers use different users/credentials. Would need to check their actual connection details.

---

## Recommended Next Steps

### Step 1: Install pgvector (5 minutes)

```bash
sudo apt install -y postgresql-server-dev-16 build-essential git
cd /tmp && git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git && cd pgvector
make && sudo make install
sudo -u postgres psql -d upwork_processing -c "CREATE EXTENSION vector;"
```

### Step 2: Verify Installation

```bash
sudo -u postgres psql -d upwork_processing -c "\dx vector"
```

Expected output:
```
List of installed extensions
 Name  |  Version |   Schema   |               Description
-------+----------+------------+---------------------------------------
 vector | 0.5.1    | public     | vector data type and ivfflat and hnsw access methods
```

### Step 3: Set Environment Variable

```bash
# Add to .env file
DATABASE_URL=postgresql+asyncpg://postgres@localhost:5432/upwork_processing
```

---

## If pgvector Installation Fails

**Fallback Plan**: Use Docker with pgvector pre-installed

```bash
docker stop upwork-postgres 2>/dev/null; docker rm upwork-postgres 2>/dev/null
docker run -d \
  --name upwork-postgres \
  --restart unless-stopped \
  -p 5433:5432 \
  -e POSTGRES_DB=upwork_processing \
  -e POSTGRES_HOST_AUTH_METHOD=trust \
  pgvector/pgvector:pg16
```

**Connection string**:
```bash
DATABASE_URL=postgresql+asyncpg://postgres@localhost:5433/upwork_processing
```

---

## Summary

| Item | Status |
|------|--------|
| PostgreSQL 16 service | ✅ Running |
| Database `upwork_processing` | ✅ Created |
| User `postgres` | ✅ Superuser |
| pgvector extension | ❌ NOT installed (needs manual compilation) |
| GCC compiler | ✅ Available |
| pg_config | ✅ Available |
| PostgreSQL headers | ❌ Need to install `postgresql-server-dev-16` |

**Recommendation**: Install pgvector manually. If that fails, use Docker.

---

**Checked**: 2026-02-05 01:50 UTC
**Status**: Ready for pgvector installation