# 🗄️ Database & Migrations (Alembic)

We use **Alembic** to manage schema changes. Since we are running inside Docker, all commands must be executed within the container context.

## 🌍 Timezone Policy
We use `TIMESTAMPTZ` (Timestamp with Timezone) for all temporal data.
- **Rule:** The database stores everything in UTC. 
- **Application:** The Python layer interprets this data and can convert it to the user's specific timezone (e.g., `Europe/Lisbon`) on the frontend.

## 🛠️ The Migration Workflow

Every time you change a model in `src/models/`, follow these steps:

1. **Modify the Model:** Update your Python class in `src/models/`.
2. **Generate a Revision:**
   ```bash
   docker-compose exec app alembic revision --autogenerate -m "describe your change"
   ```
3. **Review the Script:** Check the new file generated in `alembic/versions/`.
4. **Apply to Database:**
    ```bash
    docker-compose exec app alembic upgrade head
    ```
## ⚠️ Common Issues
- Driver not found: Ensure psycopg2-binary is installed. Alembic cannot use asyncpg.
- Command not found: Ensure you are running through docker-compose exec app.

---
