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
├── alembic/            # Database migration history and environment
├── docs/               # Documentation (you are here)
├── src/
│   ├── api/            # Route handlers (FastAPI Endpoints)
│   ├── core/           # Configuration, Security, and Global constants
│   ├── models/         # SQLModel database definitions
│   ├── repositories/   # Data access layer (Direct DB queries)
│   ├── schemas/        # Pydantic-only models for API data exchange
│   ├── services/       # Business logic (e.g., Calendar Projection Engine)
│   └── database.py     # Database engine and session setup
├── alembic.ini         # Alembic configuration
├── docker-compose.yaml # Local infrastructure setup
└── pyproject.toml      # Project dependencies (Poetry)