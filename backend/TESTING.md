# Testing the MikroTik Controller Backend

This guide explains how to test the backend API to ensure everything is working correctly.

## Prerequisites

Before testing, ensure you have:

1. ✅ Completed the setup (see [QUICKSTART.md](QUICKSTART.md))
2. ✅ PostgreSQL running
3. ✅ Redis running
4. ✅ Database migrations applied
5. ✅ API server running

## Quick Test

Run the automated test script:

```bash
python test_api.py
```

This will verify:
- Health check endpoints
- Database connectivity
- Redis connectivity
- API documentation accessibility
- CORS configuration

## Manual Testing with API Docs

The easiest way to test the API manually is using the interactive API documentation:

1. **Start the server** (if not already running):
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Open the API docs** in your browser:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

3. **Seed the database** with test data:
   ```bash
   python seed_database.py
   ```

## Testing Authentication

### 1. Login

**Endpoint:** `POST /api/v1/auth/login`

**Request:**
```json
{
  "email": "admin@test.com",
  "password": "admin123"
}
```

**Expected Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "email": "admin@test.com",
    "tenant_id": "uuid",
    "role": {
      "name": "TenantAdmin",
      "description": "Full access within tenant"
    }
  }
}
```

**Using curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"admin123"}'
```

### 2. Use Access Token

Copy the `access_token` from the login response and use it in subsequent requests:

**Using curl:**
```bash
# Save token to variable
TOKEN="your_access_token_here"

# Make authenticated request
curl -X GET "http://localhost:8000/api/v1/devices" \
  -H "Authorization: Bearer $TOKEN"
```

**Using API Docs:**
1. Click the "Authorize" button (🔒) at the top right
2. Enter: `Bearer your_access_token_here`
3. Click "Authorize"
4. Now all requests will include the token

### 3. Refresh Token

**Endpoint:** `POST /api/v1/auth/refresh`

**Request:**
```json
{
  "refresh_token": "your_refresh_token_here"
}
```

**Expected Response (200 OK):**
```json
{
  "access_token": "new_access_token",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 4. Logout

**Endpoint:** `POST /api/v1/auth/logout`

**Headers:**
```
Authorization: Bearer your_access_token_here
```

**Expected Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

## Testing with Different User Roles

The seeded database includes users with different roles:

| Email | Password | Role | Permissions |
|-------|----------|------|-------------|
| admin@test.com | admin123 | TenantAdmin | Full access within tenant |
| manager@test.com | manager123 | SiteManager | Manage devices in sites |
| operator@test.com | operator123 | Operator | Execute operations |
| viewer@test.com | viewer123 | Viewer | Read-only access |

Test each role to verify permission enforcement:

1. Login as each user
2. Try to access different endpoints
3. Verify that restricted actions return 403 Forbidden

## Testing Health Endpoints

### Basic Health Check

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-03-11T..."
}
```

### Readiness Check

```bash
curl http://localhost:8000/health/ready
```

**Expected Response:**
```json
{
  "status": "ready",
  "dependencies": {
    "database": "healthy",
    "redis": "not_implemented"
  },
  "timestamp": "2026-03-11T..."
}
```

### Liveness Check

```bash
curl http://localhost:8000/health/live
```

**Expected Response:**
```json
{
  "status": "alive",
  "timestamp": "2026-03-11T..."
}
```

## Running Unit Tests

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_services/test_device_service.py

# Run with verbose output
pytest -v

# Run tests matching a pattern
pytest -k "test_authentication"
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Testing Error Handling

### Invalid Credentials

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"wrong_password"}'
```

**Expected Response (401 Unauthorized):**
```json
{
  "detail": "Invalid email or password"
}
```

### Missing Authentication

```bash
curl -X GET "http://localhost:8000/api/v1/devices"
```

**Expected Response (401 Unauthorized):**
```json
{
  "detail": "Could not validate credentials"
}
```

### Invalid Token

```bash
curl -X GET "http://localhost:8000/api/v1/devices" \
  -H "Authorization: Bearer invalid_token"
```

**Expected Response (401 Unauthorized):**
```json
{
  "detail": "Could not validate credentials"
}
```

## Testing Audit Logging

All actions are logged to the audit log. To verify:

1. Perform some actions (login, create device, etc.)
2. Check the `audit_logs` table in the database:

```sql
SELECT 
  action,
  resource_type,
  result,
  timestamp,
  user_id
FROM audit_logs
ORDER BY timestamp DESC
LIMIT 10;
```

Or query via API (once audit endpoints are implemented):
```bash
curl -X GET "http://localhost:8000/api/v1/audit-logs" \
  -H "Authorization: Bearer $TOKEN"
```

## Testing Multi-Tenant Isolation

1. Create two tenants with different users
2. Login as user from Tenant A
3. Try to access resources from Tenant B
4. Verify that access is denied (404 or 403)

## Performance Testing

### Simple Load Test with curl

```bash
# Test health endpoint
for i in {1..100}; do
  curl -s http://localhost:8000/health > /dev/null &
done
wait
```

### Load Testing with Locust

Create a `locustfile.py`:

```python
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login and get token
        response = self.client.post("/api/v1/auth/login", json={
            "email": "admin@test.com",
            "password": "admin123"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task
    def health_check(self):
        self.client.get("/health")
    
    @task(3)
    def list_devices(self):
        self.client.get("/api/v1/devices", headers=self.headers)
```

Run load test:
```bash
locust -f locustfile.py --host=http://localhost:8000
```

Then open http://localhost:8089 to configure and run the test.

## Debugging Tips

### Enable Debug Logging

In `.env`:
```
APP_DEBUG=true
APP_LOG_LEVEL=DEBUG
```

### Check Logs

The server logs will show detailed information about each request:
- Request method and path
- Authentication status
- Database queries (if DB_ECHO=true)
- Errors and stack traces

### Use Database Client

Connect to the database to inspect data:

```bash
psql -U postgres -d mikrotik_controller
```

Useful queries:
```sql
-- Check users
SELECT id, email, is_active FROM users;

-- Check devices
SELECT id, hostname, ip_address, status FROM devices;

-- Check audit logs
SELECT action, result, timestamp FROM audit_logs ORDER BY timestamp DESC LIMIT 10;

-- Check roles and permissions
SELECT r.name, p.resource, p.action 
FROM roles r 
JOIN permissions p ON r.id = p.role_id 
ORDER BY r.name, p.resource, p.action;
```

## Common Issues

### "Database connection failed"
- Check PostgreSQL is running: `pg_isready`
- Check credentials in `.env`
- Check database exists: `psql -U postgres -l`

### "Redis connection failed"
- Check Redis is running: `redis-cli ping`
- Should return `PONG`

### "Token expired"
- Tokens expire after 30 minutes by default
- Use the refresh token to get a new access token
- Or login again

### "Permission denied"
- Check user role has required permissions
- Check audit logs to see what permission was required
- SuperAdmin bypasses all permission checks

## Next Steps

Once basic testing is complete:

1. ✅ Test all authentication flows
2. ✅ Test with different user roles
3. ✅ Verify audit logging
4. ✅ Test error handling
5. ⏭️ Implement device management endpoints
6. ⏭️ Implement template management
7. ⏭️ Implement job queue
8. ⏭️ Add integration tests

## Automated Testing Checklist

- [ ] Health checks pass
- [ ] Database connectivity works
- [ ] Redis connectivity works
- [ ] User authentication works
- [ ] Token refresh works
- [ ] Logout works
- [ ] Permission enforcement works
- [ ] Multi-tenant isolation works
- [ ] Audit logging works
- [ ] Error handling works
- [ ] API documentation accessible
- [ ] All unit tests pass
- [ ] Code coverage > 80%
