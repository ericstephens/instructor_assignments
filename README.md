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
