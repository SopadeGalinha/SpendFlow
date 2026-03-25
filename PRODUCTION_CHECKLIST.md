# Production Readiness Checklist

## Overview
This document outlines the requirements and best practices for deploying SpendFlow to production on Kubernetes.

---

## 1. Environment Configuration ✅

### Required Environment Variables
All of the following MUST be set in Kubernetes secrets:

```bash
# Application Configuration
ENV=production                          # Must be "production"
CORS_ORIGINS=https://yourdomain.com   # Comma-separated list of allowed origins
SECRET_KEY=<secure-random-key>         # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"

# Database (PostgreSQL recommended for production)
DATABASE_URL=postgresql+asyncpg://user:password@postgres-host:5432/spendlyflow

# Authentication
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Security Requirements

- **NEVER commit .env files or secrets to version control**
- Use Kubernetes Secrets for credential management
- Rotate `SECRET_KEY` periodically
- Use strong database credentials (minimum 32 characters)
- Always use HTTPS in production

---

## 2. Database Setup ✅

### PostgreSQL (Recommended)

1. Create database:
```sql
CREATE DATABASE spendlyflow;
```

2. Run migrations:
```bash
docker run --rm \
  -e DATABASE_URL="postgresql+asyncpg://user:password@host:5432/spendlyflow" \
  ghcr.io/yourorg/spendlyflow:latest \
  alembic upgrade head
```

3. Verify migrations are applied:
```bash
poetry run alembic current
```

### SQLite (NOT recommended for production)
- Use only for development/testing
- File-based SQLite has concurrency issues in distributed systems
- PostgreSQL/MySQL strongly recommended

---

## 3. Security Hardening ✅

### CORS Configuration
```
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```
⚠️ **Never use `*` in production** - explicitly whitelist your domains

### Security Headers (Automatic)
The application includes these security headers:
- `X-Content-Type-Options: nosniff` - Prevent MIME-type sniffing
- `X-Frame-Options: DENY` - Prevent clickjacking
- `X-XSS-Protection: 1; mode=block` - Enable XSS protection
- `Strict-Transport-Security: max-age=63072000` - Enforce HTTPS

### Rate Limiting
- **Current**: In-memory rate limiting (100 requests per 60 seconds per IP)
- **For distributed systems**: Consider Redis-based rate limiting
- Configure rate limits in `src/core/middleware.py` as needed

### Authentication
- JWT tokens expire after 30 minutes (configurable)
- Passwords: minimum 8, maximum 72 characters
- All passwords hashed with bcrypt (industry standard)
- No plaintext passwords stored

---

## 4. Kubernetes Deployment ✅

### Required ConfigMaps
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: spendlyflow-config
  namespace: default
data:
  ENV: "production"
  CORS_ORIGINS: "https://yourdomain.com,https://app.yourdomain.com"
  ACCESS_TOKEN_EXPIRE_MINUTES: "30"
  ALGORITHM: "HS256"
```

### Required Secrets
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: spendlyflow-secrets
  namespace: default
type: Opaque
stringData:
  SECRET_KEY: "<generate-secure-key>"
  DATABASE_URL: "postgresql+asyncpg://user:password@postgres:5432/spendlyflow"
```

### Deployment Manifest (Example)
See `k8s/deployment.yaml` - includes:
- ✅ Health checks (liveness & readiness probes)
- ✅ Resource limits
- ✅ Image pull policy
- ✅ Environment variable injection
- ✅ Port configuration (8080)

### Health Checks
Two endpoints are configured for K8s:
- `GET /health` - Database connectivity check
- `GET /` - Application status check

Configure probes:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
```

---

## 5. Database Migrations ✅

### Before Deployment
Run migrations to set up schema:
```bash
poetry run alembic upgrade head
```

### Existing Migrations
Located in `alembic/versions/`:
- `35cd94722e4c_initial_migration.py` - Initial schema
- `822a442fa8b5_change_numeric_columns_to_decimal.py` - Decimal type fix
- `d62f86d08d40_add_missing_user_columns.py` - User column updates

### Testing Migrations
Migrations are tested automatically as part of the test suite.

---

## 6. Logging & Monitoring ✅

### Structured Logging
The application uses JSON logging for K8s log aggregation:
- All logs include: timestamp, level, message, context
- Sensitive data is sanitized
- Request/response logging via httpx library

### Key Log Points
- User registration/login (info level)
- Authentication failures (warning level)
- Unhandled exceptions (error level with traceback)
- Database operations (debug level)

### Log Aggregation
Configure your log aggregation platform to:
1. Parse JSON log format
2. Index by user_id for audit trails
3. Alert on error rates > 5%

### Metrics
Recommended metrics to monitor:
- `/health` endpoint response time (database latency)
- HTTP request rate by endpoint
- Error rate by status code
- Authentication failure rate
- Rate limit violations

---

## 7. Performance Considerations ✅

- FastAPI runs async code efficiently
- SQLAlchemy AsyncSession properly manages connections
- Database connection pooling configured in SQLAlchemy
- No N+1 query issues identified
- All queries use parameterized statements (no SQL injection risk)

### Scaling
- **Stateless**: Application stores no in-memory state (except rate limiting)
- **Horizontal scaling**: Safe to run multiple replicas
- **Rate limiting caveat**: Per-instance limits, not global (each instance has its own limit)

---

## 8. Testing & Validation ✅

### Test Coverage
All 79 tests pass:
- ✅ Authentication & authorization
- ✅ Account CRUD operations
- ✅ Soft delete & restore
- ✅ Calendar projections
- ✅ Input validation
- ✅ Error handling
- ✅ Security headers
- ✅ CORS configuration

### Before Production Deployment
```bash
# Run complete test suite
poetry run pytest tests/ -v

# Build and scan Docker image
docker build -t spendlyflow:latest .
trivy image spendlyflow:latest
```

---

## 9. Cloud Storage & Backups ✅

### Database Backups
- **Frequency**: Daily automated backups recommended
- **Retention**: Minimum 30 days
- **Testing**: Monthly restore test

### Example (PostgreSQL with Kubernetes)
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-backup
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:latest
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: password
            command:
            - /bin/sh
            - -c
            - |
              pg_dump -h postgres -U spendlyflow spendlyflow | \
              aws s3 cp - s3://backup-bucket/spendlyflow-$(date +%Y%m%d).sql
```

---

## 10. Deployment Steps ✅

### Pre-Deployment
1. [ ] Environment variables configured in K8s secrets
2. [ ] Database created and migrations applied
3. [ ] SSL/TLS certificates configured for ingress
4. [ ] Backup system configured
5. [ ] Monitoring/logging setup complete
6. [ ] All tests passing locally

### Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/ingress.yaml

# Verify deployment
kubectl get pods -l app=spendlyflow
kubectl logs -l app=spendlyflow --tail=50

# Check health
kubectl exec -it <pod-name> -- curl http://localhost:8080/health
```

### Post-Deployment
1. [ ] Verify `/health` endpoint returns `200 OK`
2. [ ] Test login/authentication flow
3. [ ] Create a test account and verify CRUD
4. [ ] Check logs for errors
5. [ ] Monitor error rate for 1 hour

---

## 11. Incident Response ✅

### Common Issues & Solutions

**Problem**: Cannot connect to database
- Check DATABASE_URL in secrets
- Verify database credentials
- Ensure database is running: `kubectl exec postgres-pod -- pg_isready`

**Problem**: High error rate / 500 errors
- Check application logs: `kubectl logs -l app=spendlyflow`
- Check database: `kubectl logs postgres`
- Verify memory limits not exceeded: `kubectl top pods`

**Problem**: Users locked out / authentication failing
- Check JWT token expiry: `ACCESS_TOKEN_EXPIRE_MINUTES` in config
- Verify SECRET_KEY hasn't changed (would invalidate all tokens)
- Check user credentials are correct

**Problem**: Rate limiting too strict / 429 errors
- Increase `REQUESTS_RATE_LIMIT` in `src/core/middleware.py`
- For distributed systems, migrate to Redis rate limiting

---

## 12. Compliance & Security ✅

### Data Protection
- All passwords hashed with bcrypt
- No plaintext credentials in code
- HTTPS only in production
- CORS restricted to allowed domains

### Audit Trail
The application logs:
- User registration (timestamp, email, user_id)
- Authentication attempts (success/failure, email)
- All errors with context

### GDPR Compliance
Implementation notes:
- Soft delete implemented for accounts (data retention)
- User ID tracking in all operations
- Error messages don't expose sensitive data
- No third-party tracking

---

## Contact & Support
For deployment issues, check:
1. `PRODUCTION_CHECKLIST.md` (this file)
2. Application logs
3. K8s event logs: `kubectl describe pod <pod-name>`
4. Database logs: `kubectl logs <postgres-pod>`
