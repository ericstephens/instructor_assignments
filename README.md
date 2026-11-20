# Instructor Reservation System

A web application for managing instructor allocations to events and classes. Instructors self-allocate to available event dates; administrators manage the full catalog, assignments, and reporting.

**Stack:** FastAPI · SQLAlchemy · PostgreSQL · React/Vite · AWS (ECS Fargate, RDS, S3, CloudFront, SES) · OpenTofu · AWS Emulator

---

## AWS Architecture

```mermaid
%%{init: {'theme': 'dark'}}%%
graph TD
    subgraph Client["Client"]
        Browser([Browser])
    end

    subgraph Emulator["AWS — emulator @ 127.0.0.1:9297"]

        subgraph CDN["CDN"]
            CF["CloudFront\ndistribution"]
        end

        subgraph Storage["Storage"]
            S3["S3\nfrontend assets"]
        end

        subgraph VPC["VPC  10.0.0.0/16"]
            IGW["Internet Gateway"]
            ALB["Application Load Balancer\n:80"]
            SG_ALB["SG: alb_sg"]
            SG_API["SG: api_sg"]
            SG_RDS["SG: rds_sg"]

            subgraph Fargate["ECS Fargate  us-east-1a / 1b"]
                API["FastAPI\n:8000"]
            end

            RDS["RDS PostgreSQL 16\nAPI-level emulation only†"]
        end

        subgraph Support["Supporting services"]
            ECR["ECR\ninstructor-api image"]
            SES["SES\nemail notifications"]
            CW["CloudWatch\n/ecs/instructor-api"]
            IAM_EXEC["IAM — exec role\nECSTaskExecutionRolePolicy\n+ CloudWatch logs"]
            IAM_TASK["IAM — task role\nSES SendEmail"]
        end
    end

    subgraph Sidecar["Local sidecar  dev/test"]
        PG[("postgres:16\n127.0.0.1:5433")]
    end

    Browser -- "HTTPS" --> CF
    CF --> S3
    Browser -- "HTTP :80" --> ALB
    ALB -- ":8000" --> API

    SG_ALB -. "controls" .-> ALB
    SG_API -. "controls" .-> API
    SG_RDS -. "controls" .-> RDS

    IGW --> ALB

    ECR -- "image pull" --> API
    API -- "data" --> PG
    API -- "send email" --> SES
    API -- "structured logs" --> CW
    IAM_EXEC -. "permissions" .-> API
    IAM_TASK -. "permissions" .-> API
    RDS -. "† models prod config;\n  no wire endpoint\n  in emulator" .-> PG
```

> **†** The AWS Emulator provides RDS API emulation (create/describe/delete instance) but does not expose a PostgreSQL wire endpoint. A `postgres:16` sidecar container (`127.0.0.1:5433`) serves as the actual data layer locally. In a real AWS environment, replace the sidecar with the RDS endpoint.

---

## Prerequisites

| Tool | Version |
|------|---------|
| podman | ≥ 4.x |
| podman machine | running (macOS) |
| conda / mamba | any |
| OpenTofu | ≥ 1.6 (`tofu`) |
| AWS CLI v2 | ≥ 2.40 |
| Node.js | ≥ 18 |

---

## Quick start

### 1 — Build the emulator image (once)

```bash
./manage.sh emulator:build
```

### 2 — Start the stack

```bash
# Start postgres sidecar + AWS emulator containers
./manage.sh emulator:start

# Activate emulator credentials
source localENV
aws login          # writes creds/CA to ~/.aws/emulator/9297/

# Provision all 31 AWS resources
./manage.sh infra:init
./manage.sh infra:up

# Bootstrap databases and run migrations
./manage.sh db:init
./manage.sh db:migrate
```

### 3 — Run the application locally

```bash
./manage.sh api:start      # FastAPI on :8000
./manage.sh fe:start       # Vite dev server on :5173
```

Or start everything at once:

```bash
source localENV && aws login
./manage.sh start
```

### 4 — Run tests

```bash
./manage.sh test            # db + api + frontend
```

### 5 — Tear down

```bash
./manage.sh stop            # api + fe + infra:down + containers
```

---

## manage.sh reference

### Emulator
| Command | Description |
|---------|-------------|
| `emulator:build` | Build the `aws-emulator` container image |
| `emulator:start` | Start postgres sidecar (`:5433`) + AWS emulator (`:9297`) |
| `emulator:stop` | Stop and remove both containers |
| `emulator:status` | Show running container status |
| `emulator:login` | Run `aws login` against the emulator |

### Infrastructure (OpenTofu)
| Command | Description |
|---------|-------------|
| `infra:init` | `tofu init` |
| `infra:up` | `tofu apply -auto-approve` — provisions 31 resources |
| `infra:down` | `tofu destroy -auto-approve` |
| `infra:status` | `tofu show` |
| `infra:output` | Print all outputs (ALB URL, CloudFront, ECR, etc.) |

### Database
| Command | Description |
|---------|-------------|
| `db:init` | Create `instructor_test_db` on the postgres sidecar |
| `db:migrate` | Run Alembic migrations (`001` initial schema → `003` users) |

### API
| Command | Description |
|---------|-------------|
| `api:build` | Build `instructor-api:latest` Docker image |
| `api:push` | Push image to ECR (requires `infra:up`) |
| `api:start` | Start FastAPI dev server on `:8000` (background) |
| `api:stop` | Stop the dev server |
| `api:restart` | Restart the dev server |
| `api:logs` | Tail API log |
| `api:test` | Run pytest suite (77 tests) |

### Frontend
| Command | Description |
|---------|-------------|
| `fe:start` | Start Vite dev server on `:5173` (background) |
| `fe:stop` | Stop the dev server |
| `fe:build` | Production build to `src/frontend/dist/` |
| `fe:deploy` | Build + `aws s3 sync` + CloudFront invalidation |
| `fe:test` | Run Vitest suite |

### Stack shortcuts
| Command | Description |
|---------|-------------|
| `start` | Full stack: emulator → infra → migrate → api → frontend |
| `stop` | Reverse teardown |
| `status` | Status of all components |
| `test` | All test suites |

---

## Environment variables

Defaults live in `localENV` and `src/api/requirements.txt`. Override via `TF_VAR_*` for Terraform or env vars for the API:

| Variable | Default | Used by |
|----------|---------|---------|
| `DATABASE_URL` | `postgresql+psycopg2://postgres:instructor_pass_local@127.0.0.1:5433/instructor_db` | API, Alembic |
| `TEST_DATABASE_URL` | same host, `instructor_test_db` | pytest |
| `JWT_SECRET_KEY` | `dev-jwt-secret-change-in-prod` | API auth |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | FastAPI CORS |
| `NOTIFY_BACKEND` | `log` | notifications (`log` \| `smtp` \| `ses`) |
| `NOTIFY_FROM_EMAIL` | `noreply@instructor-system.local` | SES / SMTP |
| `AWS_ENDPOINT_URL` | `https://127.0.0.1:9297` | AWS SDK + OpenTofu |

---

## Architectural decisions

### API framework — FastAPI
**Chosen:** FastAPI  
**Why:** Native async support, automatic OpenAPI/Swagger docs, first-class Pydantic v2 integration, and dependency injection (used for auth and DB session injection in every route). Performance is significantly better than synchronous frameworks under load.  
**Alternatives:**
- **Flask** — simpler but no async, no built-in validation; would require Marshmallow or similar
- **Django REST Framework** — batteries-included but heavy; ORM coupling makes it awkward alongside SQLAlchemy
- **Litestar** — comparable feature set to FastAPI; less ecosystem adoption at the time of writing

---

### ORM + migrations — SQLAlchemy 2.x + Alembic
**Chosen:** SQLAlchemy Core/ORM with Alembic  
**Why:** SQLAlchemy 2.x gives full control over queries while remaining database-agnostic. Alembic generates versioned, reviewable migration scripts that map 1:1 to schema changes. The two are designed to work together.  
**Alternatives:**
- **Django ORM** — tightly coupled to Django; not usable standalone without significant friction
- **Tortoise ORM** — async-native, but smaller ecosystem and less tooling for migrations
- **Prisma (Python)** — schema-first approach; still maturing in the Python ecosystem

---

### Auth — JWT (stateless) + bcrypt
**Chosen:** `python-jose` for JWT, `passlib[bcrypt]` for password hashing  
**Why:** JWTs are stateless — no session store needed, tokens carry role claims, and they work naturally with SPAs that store tokens in memory. bcrypt is the industry standard for password hashing: intentionally slow, well-audited, and widely supported.  
**Note:** bcrypt pinned to `<4.0.0` — passlib 1.7.4 is incompatible with bcrypt 4.x API changes.  
**Alternatives:**
- **OAuth 2.0 / OIDC (Auth0, Cognito)** — appropriate for production SSO but adds external service dependency; overkill for a closed-user-base system
- **Session cookies** — simpler for server-rendered apps; poor fit for SPA + API separation
- **argon2** — newer and stronger than bcrypt; passlib supports it, but bcrypt remains the more common choice

---

### Compute — ECS Fargate
**Chosen:** ECS Fargate  
**Why:** Serverless containers — no EC2 instances to patch or size, IAM roles attach directly to task definitions, and scaling is handled by the ECS service scheduler. The container boundary keeps dev/prod parity tight (same image runs locally and in AWS).  
**Alternatives:**
- **EC2 (ECS or standalone)** — full control over instance type/OS; operational overhead of patching and right-sizing; appropriate when GPU or specific hardware is needed
- **AWS Lambda** — sub-second billing and zero idle cost; cold starts and 15-minute timeout make it a poor fit for a long-lived FastAPI server with DB connection pooling
- **App Runner** — simpler than Fargate (no VPC, ALB, or task definitions); less control over networking and scaling policies
- **Kubernetes (EKS)** — production-grade orchestration; significant operational complexity for a single-service deployment

---

### Frontend hosting — S3 + CloudFront
**Chosen:** S3 static website + CloudFront CDN  
**Why:** A React/Vite build produces pure static assets — no server-side rendering needed. S3+CloudFront is the lowest-cost, highest-durability option: global edge caching, automatic HTTPS, and zero compute to manage.  
**Alternatives:**
- **Amplify Hosting** — managed CI/CD + hosting in one; less control, vendor lock-in on the build pipeline
- **EC2 / Nginx** — unnecessary compute cost and operational overhead for static files
- **Vercel / Netlify** — excellent DX but outside the AWS ecosystem; incompatible with the emulator-based local workflow

---

### Container registry — ECR
**Chosen:** Amazon ECR  
**Why:** Native IAM integration — ECS task execution roles pull images without managing Docker Hub credentials. Image scanning, lifecycle policies, and no egress charges within the same AWS region.  
**Alternatives:**
- **Docker Hub** — wider tooling support; requires credential management; rate-limited on free tier
- **GitHub Container Registry** — good for open-source projects; adds a cross-cloud dependency

---

### Load balancer — ALB
**Chosen:** Application Load Balancer  
**Why:** Layer 7 HTTP/HTTPS routing, path-based rules, native integration with ECS Fargate (IP-based target groups), and health checks. Required for the ECS service to register and deregister tasks automatically.  
**Alternatives:**
- **API Gateway (HTTP API)** — better fit for Lambda; adds request/response transformation overhead not needed here
- **NLB (Network Load Balancer)** — Layer 4; lower latency but no HTTP-level features (host/path routing, health check response codes)
- **Direct container exposure** — no load balancer; works for dev, loses HA and zero-downtime deploys

---

### Database — RDS PostgreSQL
**Chosen:** RDS PostgreSQL 16  
**Why:** The data model is inherently relational (events → event_dates → allocations with FK constraints and uniqueness rules). PostgreSQL's `UniqueConstraint` enforces double-booking prevention at the DB level, and SQLAlchemy's ORM maps cleanly to it.  
**Alternatives:**
- **Aurora PostgreSQL** — wire-compatible with PostgreSQL; higher cost; better fit for high-availability multi-region deployments (see detailed comparison below)
- **DynamoDB** — no joins, no transactions across items; would require significant denormalization for the allocation model
- **SQLite** — zero-config for local dev; not production-grade; abandoned early in favour of real PostgreSQL for all environments (see testing decision below)

#### RDS PostgreSQL vs Aurora PostgreSQL — detailed comparison

**Cost** (`db.t3.micro`, 20 GB storage, us-east-1 on-demand)

| | RDS PostgreSQL | Aurora PostgreSQL |
|-|---------------|------------------|
| Compute | `db.t3.micro` ~$0.018/hr (~$13/mo) | Minimum `db.t3.medium` ~$0.073/hr (~$53/mo) — no Micro option |
| Storage | $0.115/GB-month (gp2) | $0.10/GB-month |
| I/O | Included | **$0.20 per million requests** — adds up on write-heavy workloads |
| Multi-AZ | 2× instance cost (opt-in) | Built-in 6-way replication across 3 AZs |
| Estimated total | **~$15/mo** | **~$55–80/mo** |

Aurora costs roughly 4–6× more at small scale. The per-I/O charge makes it particularly punishing for workloads with many small writes (e.g., frequent allocation events).

**Where Aurora wins**
- **Availability**: Automatic failover in ~30 seconds vs. 1–2 minutes for RDS Multi-AZ; six-way replication by default
- **Read replicas**: Up to 15 with single-digit millisecond replication lag vs. 5 for RDS with higher lag
- **Aurora Serverless v2**: Scales in 0.5 ACU increments toward near-zero when idle — better cost profile for intermittent traffic than a fixed instance
- **Global Database**: Cross-region active-active replication with <1 s RPO/RTO; no RDS equivalent
- **Zero-downtime minor upgrades** via blue/green deployment

**Where RDS PostgreSQL wins**
- **Engine fidelity**: 100% stock PostgreSQL — no Aurora-specific vacuum behavior, sequence caching differences, or extension restrictions
- **Extension support**: Full `pg_extension` ecosystem; Aurora patches or restricts some extensions
- **Operational simplicity**: No cluster vs. reader endpoint distinction, no ACU tuning
- **Emulator compatibility**: The AWS Emulator models `aws_db_instance`; Aurora clusters (`aws_rds_cluster`) would require reworking both the Terraform and emulator behavior
- **Minimum viable instance**: `db.t3.micro` is sufficient; Aurora has no micro-class option

**Verdict**: RDS PostgreSQL is the right call for this workload. User counts are bounded, write volume is low, and the availability requirements don't justify Aurora's cost floor. Aurora Serverless v2 would be worth revisiting if the system grew to hundreds of concurrent users or required cross-region failover.

---

### Infrastructure as code — OpenTofu
**Chosen:** OpenTofu (`tofu`)  
**Why:** Drop-in open-source fork of Terraform under the Linux Foundation. Full HCL compatibility with the HashiCorp AWS provider; avoids the BSL licensing concerns introduced in Terraform 1.6+.  
**Alternatives:**
- **Terraform** — identical HCL syntax; BSL license restricts competitive use cases
- **AWS CDK** — TypeScript/Python-native; better for teams already in those languages; generates CloudFormation, which adds an abstraction layer
- **Pulumi** — general-purpose IaC in real programming languages; steeper learning curve; not yet as mature an ecosystem as HCL for AWS

---

### Notification backend — pluggable (log / SMTP / SES)
**Chosen:** Strategy-pattern backend selected via `NOTIFY_BACKEND` env var  
**Why:** Keeps the test suite fast and self-contained (`log` backend writes to the Python logger, captured by `caplog`). Switching to `ses` in production requires only an env var change — no code path changes.  
**Alternatives:**
- **Hardcoded SES** — simpler but forces SES credentials in every environment including CI
- **Celery + Redis task queue** — appropriate for high-volume/retry-heavy email; unnecessary complexity for the current scale
- **Firebase Cloud Messaging** — suitable for push notifications to mobile; not applicable here

---

### Test isolation — real PostgreSQL, per-function rollback
**Chosen:** Real `postgres:16` for all test environments; connection-level transaction rolled back after each test  
**Why:** Mocked databases let subtle bugs through — a migration or constraint that works in SQLite may fail in PostgreSQL. The rollback-per-test pattern gives full isolation without the cost of recreating the schema for every test function.  
**Alternatives:**
- **SQLite in-memory** — fast to spin up; silently ignores constraints PostgreSQL enforces; rejected after prior incidents
- **Separate DB per test** — perfect isolation; prohibitively slow for 77 tests
- **Testcontainers** — spins up a real Docker PostgreSQL per test run; equivalent outcome, more complex setup

---

## Project structure

```
├── src/
│   ├── api/                  FastAPI application
│   │   ├── main.py           App entry point, CORS, router wiring
│   │   ├── auth.py           JWT, bcrypt, RBAC dependencies
│   │   ├── notifications.py  Pluggable email (log / SMTP / SES)
│   │   ├── routers/          events, event_dates, allocations,
│   │   │                     instructors, reports, auth
│   │   ├── schemas.py        Pydantic v2 request/response models
│   │   ├── Dockerfile        Python 3.13-slim API container
│   │   └── tests/            77 pytest integration tests
│   ├── db/
│   │   ├── models.py         SQLAlchemy ORM models
│   │   ├── config.py         Engine + Base + get_db
│   │   ├── alembic.ini       Alembic config
│   │   ├── migrations/       001 schema · 002 is_cancelled · 003 users
│   │   └── tests/            DB-layer tests
│   └── frontend/             React + Vite + FullCalendar
│       ├── src/
│       │   ├── pages/        AdminDashboard, InstructorView
│       │   ├── components/   Calendar, ImportForm, ReportsPanel
│       │   └── api/          axios wrappers
│       └── __tests__/        Vitest + React Testing Library
├── *.tf                      OpenTofu — VPC, RDS, ECR, ECS, ALB,
│                             S3, CloudFront, SES, IAM
├── Dockerfile                AWS Emulator container
├── localENV                  Source this before tofu / aws CLI
├── manage.sh                 All lifecycle commands
└── start                     Raw podman run for the emulator
```
