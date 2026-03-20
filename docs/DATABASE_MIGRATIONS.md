# 🗄️ Database & Migrations (Alembic)

### Core Concept
We use **Alembic** to manage schema evolutions in a controlled manner. Since the application runs inside **Docker**, all migration commands must be executed within the `app` container context.

### 🌍 Timezone Policy
To ensure consistency in a global SaaS, we adopt the `TIMESTAMPTZ` (Timestamp with Timezone) policy.
- **Golden Rule:** The database stores everything in **UTC**.
- **Application Layer:** Python interprets this data, and the Frontend is responsible for converting it to the user's local timezone (e.g., `Europe/Lisbon` or `America/New_York`).

### 🛠️ The Migration Workflow

Every time you change a model in `src/models/`, follow these steps rigorously:

1. **Modify the Model:** Update the Python class (e.g., add a field in `User`).
2. **Generate the Revision:**
   ```bash
   docker-compose exec app alembic revision --autogenerate -m "describe the change"
   ```

3. **Validate the Script:** > SQLModel Import Trap
    > Alembic might forget to import sqlmodel. Open the file in alembic/versions/ and ensure it has import sqlmodel at the top if you see types like AutoString.

4. **Apply to Database:**
    ```
    docker-compose exec app alembic upgrade head
    ```

### 🧹 Environment Reset (Development Only)

**If you need to wipe everything and start from scratch:**
```bash
docker-compose down -v
docker-compose up -d
docker-compose exec app alembic upgrade head
```
