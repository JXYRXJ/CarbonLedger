# CarbonLedger - Enterprise Carbon Asset Management Platform

**CarbonLedger** is a secure, production-hardened FastAPI backend providing a clean, service-oriented ledger solution for managing verified carbon standard registries, carbon projects, credit batch issuances, marketplace listing trades, weighted ownership tracking, and permanent credit retirements.

Designed following the principles of **Clean Architecture**, the application is optimized for performance, fully cached with Redis (using transparent in-memory fallbacks), rate-limited for security, and prepared for seamless smart-contract blockchain synchronization.

---

## 📖 Table of Contents
1. [Architecture Overview](#-architecture-overview)
2. [Folder Structure](#-folder-structure)
3. [Technology Stack](#-technology-stack)
4. [Local Development & Installation](#-local-development--installation)
5. [Docker Orchestration](#-docker-orchestration)
6. [Alembic DB Migrations](#-alembic-db-migrations)
7. [Automated Testing](#-automated-testing)
8. [API Endpoints Reference](#-api-endpoints-reference)
9. [Production Deployment to Render](#-production-deployment-to-render)
10. [Future Blockchain Integration Hook](#-future-blockchain-integration-hook)

---

## 🏛️ Architecture Overview

The system strictly adheres to **Clean Architecture** to ensure clean separation of concerns, robust testability, and decoupling of data access from core business processes.

```mermaid
graph TD
    API[API Layer: Routers & Controllers] -->|Invokes| Service[Service Layer: Core Business Logic]
    Service -->|Uses| Repositories[Repository Layer: SQL Alchemy ORM Queries]
    Repositories -->|Queries| DB[(Database Layer: PostgreSQL / SQLite)]
    Service -->|Checks/Sets| Cache[Caching Layer: Redis / Memory Fallback]
```

### 1. API Layer (`app/api/`)
* Declares thin, fast routers handling HTTP requests, query parameters parsing, schema input model validations, and authorization guards.
* Directly wraps returned payload responses using standard `APIResponse[T]` Pydantic models.

### 2. Service Layer (`app/services/`)
* The **sole holder of business logic**. Ensures credits caps, positive integers verification, status lifecycle transactions, and ownership balance math rules.
* Invokes audit log writing, cache pattern purging, and asynchronous background tasks queue pushes.

### 3. Repository Layer (`app/repositories/`)
* Communicates directly with SQLAlchemy models. Inherits CRUD patterns from a generic `BaseRepository` class.
* Resolves query performance issues by implementing eager relation loading (`joinedload` and `selectinload`) to eliminate N+1 latency behaviors.

### 4. Database Layer (`app/models/`)
* Implements the relational schema on PostgreSQL with custom composite primary keys, cascade rules, indexing, and soft-delete states tracking.

---

## 📁 Folder Structure

```text
carbon-ledger-hub-main/
│
├── app/
│   ├── api/                  # API routers (V1 endpoints group)
│   ├── core/                 # App config, database connectivity, exceptions handlers, and logger rules
│   ├── middleware/           # Security headers, compression, request sizing limits, and rate limits
│   ├── models/               # SQLAlchemy DB Models (entities)
│   ├── repositories/         # Database access repository pattern classes
│   ├── schemas/              # Pydantic serialization & request/response validation schemas
│   ├── services/             # Domain business services, caching, exports, and blockchain interfaces
│   ├── utils/                # Security validators and helpers
│   └── main.py               # FastAPI App definition and middleware stack registration
│
├── tests/                    # 100% passing unit tests suite
├── migrations/               # Alembic database migration scripts
├── requirements.txt          # Python dependencies manifest
├── Dockerfile                # Production multi-stage Docker build config
├── docker-compose.yml        # Development Docker service manifest
├── alembic.ini               # Alembic database migration runner config
└── README.md                 # Technical platform documentation
```

---

## 💻 Technology Stack

* **Language**: Python 3.12+
* **Framework**: FastAPI (Asynchronous Web Framework)
* **ORM Engine**: SQLAlchemy 2.0 (Modern mapped attributes)
* **Migrations**: Alembic
* **Cache DB**: Redis (with standard dict fallback for tests)
* **Reports Engines**: `openpyxl` (styled Excel sheets) & `reportlab` (dynamic PDF tables)

---

## ⚙️ Local Development & Installation

### 1. Prerequisite Setup
Ensure Python 3.12+ is installed on your local computer.

```bash
# Clone the repository
cd carbon-ledger-hub-main

# Create Python Virtual Environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Project Dependencies
pip install -r requirements.txt
```

### 2. Configuration & Environment Variables (`.env`)
Create a `.env` file in the root directory:

```env
ENVIRONMENT=development
PORT=8000
SECRET_KEY=your-jwt-auth-secret-key-must-be-very-secure-and-long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database Connection
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/carbonledger

# Cache Server
REDIS_URL=redis://localhost:6379/0

# Security limit configurations
MAX_CONTENT_LENGTH=10485760
```

### 3. Run Platform Locally
Start the local hot-reloader dev server:

```bash
uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --reload
```

---

## 🐳 Docker Orchestration

You can build and spin up the complete API backend along with PostgreSQL and Redis cache servers instantly using Docker:

```bash
# Build and run the docker containers
docker-compose up --build -d

# Check service logs
docker-compose logs -f app
```

---

## 🔄 Alembic DB Migrations

Manage database structural updates using Alembic migration commands:

```bash
# Generate a new auto-detected migration script
alembic revision --autogenerate -m "describe_migration_changes"

# Apply all pending schema migrations to target PostgreSQL DB
alembic upgrade head

# Rollback last applied migration
alembic downgrade -1
```

---

## 🧪 Automated Testing

We enforce rigorous test validation covering 100% of functional endpoints, repository CRUD, authorization RBAC rules, transaction safety rollbacks, caching services, and health metrics.

Run the test suite inside your virtual environment:

```bash
# Run pytest with warning suppression and details
.venv\Scripts\python -m pytest -p no:warnings -v
```

---

## 🔌 API Endpoints Reference

Once running, interactive documentation schemas are accessible at:
* **Swagger UI Docs**: `http://localhost:8000/docs`
* **Redoc View**: `http://localhost:8000/redoc`

### Standard JSON Response Envelope
Success payload returns:
```json
{
  "success": true,
  "message": "Resource retrieved successfully",
  "data": { ... }
}
```
Failure response payload returns:
```json
{
  "success": false,
  "message": "Clarifying validation or permission error warning text",
  "errors": [ ... ]
}
```

---

## 🚀 Production Deployment to Render

Deploy **CarbonLedger** backend to [Render.com](https://render.com) using native services:

### 1. Setup Database & Cache
1. Create a **Neon PostgreSQL** database cluster and copy the connection string.
2. Spin up a **Render Redis** instance and copy the Redis URL.

### 2. Create Render Web Service
1. Connect this GitHub repository.
2. Select **Runtime: Python** and specify the Start Command:
   ```bash
   uvicorn app.main:create_app --factory --host 0.0.0.0 --port $PORT
   ```
3. Set the following environment variables:
   * `ENVIRONMENT`: `production`
   * `DATABASE_URL`: `your-neon-postgres-connection-string?sslmode=require`
   * `REDIS_URL`: `your-render-redis-connection-string`
   * `SECRET_KEY`: `cryptographically-secure-random-string`
4. Set Up Health Checks: `/api/v1/health`

---

## 🔗 Future Blockchain Integration Hook

Interfaces defined in [blockchain.py](file:///d:/CarbonLedger/carbon-ledger-hub-main/app/services/blockchain.py) allow subsequent smart contract modules to plug in easily:

1. **Ownership Minting**: Trigger `register_ownership()` inside `BatchService.create_batch()`.
2. **Atomic Trade Verification**: Execute `transfer_ownership()` on-chain inside `OrderService.create_order()` database transaction boundary.
3. **Retirement Burning**: Record the permanent credit lock on-chain inside `RetirementService.retire_credits()` via `record_retirement()`.
4. **Log Anchorage**: Anchors cryptographic audit log checksums to the chain using `record_audit_log()` inside `AuditService`.
