# 🏗️ SpendlyFlow Architecture

This document describes the technical stack and the structural design of the SpendlyFlow API.

## 🚀 Tech Stack

| Library | Purpose | Why this choice? |
| :--- | :--- | :--- |
| **FastAPI** | Web Framework | Modern, extremely fast, and built-in support for asynchronous programming (`async/await`). |
| **SQLModel** | ORM & Schema | A "marriage" between **SQLAlchemy** and **Pydantic**. It allows us to use the same class for the database table and the API response/request. |
| **Alembic** | DB Migrations | Essential for SaaS. It tracks every change in the database schema (adding columns, tables) like a Git for data. |
| **PostgreSQL** | Database | The industry standard for relational data. Reliable and supports complex financial queries. |
| **asyncpg** | Async Driver | Used by the API to talk to Postgres without "blocking" other requests. |
| **psycopg2** | Sync Driver | Required by Alembic because migration scripts are traditionally synchronous. |
| **Poetry** | Package Manager | Handles dependencies and virtual environments in a deterministic way (replaces `pip`). |

## 📁 Project Directory Structure

```text
.
├── [[alembic/]]              # Database migration history and env.py setup
│   └── versions/         # Individual migration scripts (v1, v2...)
├── docs/                 # Project documentation and architectural RFCs
├── src/
│   ├── api/              # Route handlers (FastAPI Endpoints)
│   │   └── v1/           # Versioned API routes (auth, calendar, etc.)
│   ├── [[core/]]             # Global engine: Config, Security, and Constants
│   ├── models/           # SQLModel database definitions (User, Account)
│   ├── repositories/     # Data access layer (Direct DB queries)
│   ├── schemas/          # Pydantic models for request/response validation
│   ├── services/         # Business logic (e.g., Projection Engine)
│   ├── [[database.py]]       # Async engine and session local setup
│   └── [[main.py]]           # API entry point and lifespan management
├── alembic.ini           # Alembic configuration file
├── docker-compose.yaml   # Local infrastructure (App + Postgres)
├── [[Dockerfile]]            # Multi-stage production-ready build
├── pyproject.toml        # Poetry dependencies and metadata
└── .env                  # Local secrets

```