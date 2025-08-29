# Infrastructure Setup - Docker Compose & Service Architecture

## Overview
This document provides complete infrastructure setup for the eBay Management System backend following YAGNI/SOLID principles. The infrastructure uses a simplified 3-service architecture optimized for 30-account scale.

## SOLID Principles Applied
- **Single Responsibility**: Each service has one clear purpose (API, Database, Cache)
- **Open/Closed**: Services can be extended without modifying core infrastructure
- **Interface Segregation**: Clean service boundaries with minimal inter-dependencies
- **Dependency Inversion**: Services depend on abstractions (network interfaces, not implementations)

## YAGNI Compliance
✅ **Essential Services Only**: API + Database + Redis (no microservices complexity)  
✅ **Single Database**: PostgreSQL handles all data (no sharding complexity)  
✅ **Simple Caching**: Redis for sessions/cache only (no complex cache strategies)  
✅ **Basic Networking**: Docker Compose networking (no Kubernetes orchestration)  
❌ **Eliminated**: Message queues, service mesh, complex monitoring, multiple databases

---

## Complete Infrastructure Architecture

### Service Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                    EBAY MANAGER INFRASTRUCTURE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │   FastAPI App   │    │   PostgreSQL    │    │    Redis    │ │
│  │    (ebay-api)   │    │  (ebay-database)│    │ (ebay-redis)│ │
│  │                 │    │                 │    │             │ │
│  │ • REST API      │    │ • Primary Data  │    │ • Sessions  │ │
│  │ • Authentication│    │ • File Metadata │    │ • Caching   │ │
│  │ • CSV Processing│    │ • User Data     │    │ • Job Queue │ │
│  │ • Background    │    │ • Business Data │    │ • Rate Limit│ │
│  │   Jobs          │    │                 │    │             │ │
│  │                 │    │                 │    │             │ │
│  │ Port: 8000      │    │ Port: 5432      │    │ Port: 6379  │ │
│  └─────────────────┘    └─────────────────┘    └─────────────┘ │
│           │                       │                     │       │
│           └───────────────────────┼─────────────────────┘       │
│                                   │                             │
│  ┌─────────────────────────────────┼───────────────────────────┐ │
│  │              Docker Network: ebay-network                   │ │
│  │              • Internal DNS resolution                      │ │
│  │              • Service discovery                           │ │
│  │              • Inter-service communication                 │ │
│  └─────────────────────────────────┼───────────────────────────┘ │
│                                   │                             │
│  ┌─────────────────────────────────┼───────────────────────────┐ │
│  │              Data Persistence                               │ │
│  │              • PostgreSQL: ebay_database_data              │ │
│  │              • Redis: ebay_redis_data                      │ │
│  │              • CSV Files: ebay_uploads                     │ │
│  │              • Logs: ebay_logs                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Network Communication
```
External Client (Port 8000)
         ↓
┌─────────────────┐
│   FastAPI App   │ ←→ PostgreSQL (Internal: ebay-database:5432)
│   (ebay-api)    │ ←→ Redis (Internal: ebay-redis:6379)
└─────────────────┘
```

---

## Docker Compose Configuration

### Complete docker-compose.yml
```yaml
# docker-compose.yml - Production-ready configuration
version: '3.8'

services:
  # FastAPI Application Service
  ebay-api:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: ebay-manager-api
    ports:
      - "8000:8000"
    environment:
      # Application Configuration
      - ENVIRONMENT=production
      - DEBUG=false
      - API_HOST=0.0.0.0
      - API_PORT=8000
      
      # Database Configuration
      - DATABASE_URL=postgresql://ebay_user:${POSTGRES_PASSWORD}@ebay-database:5432/ebay_manager
      - DATABASE_POOL_SIZE=20
      - DATABASE_MAX_OVERFLOW=30
      
      # Redis Configuration
      - REDIS_URL=redis://ebay-redis:6379/0
      - REDIS_SESSION_DB=1
      - REDIS_CACHE_DB=2
      - REDIS_JOB_DB=3
      
      # Security Configuration
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - JWT_ALGORITHM=HS256
      - JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
      - JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
      
      # File Upload Configuration
      - UPLOAD_MAX_SIZE=100MB
      - UPLOAD_PATH=/app/uploads
      - ALLOWED_FILE_TYPES=csv,xlsx,xls
      
      # Background Jobs Configuration
      - MAX_WORKER_THREADS=4
      - JOB_TIMEOUT_SECONDS=300
      - JOB_RETRY_ATTEMPTS=3
      
      # Logging Configuration
      - LOG_LEVEL=INFO
      - LOG_FORMAT=json
      - LOG_FILE=/app/logs/api.log
      - LOG_MAX_SIZE=50MB
      - LOG_BACKUP_COUNT=5
      
    volumes:
      - ebay_uploads:/app/uploads
      - ebay_logs:/app/logs
      
    depends_on:
      - ebay-database
      - ebay-redis
      
    networks:
      - ebay-network
      
    restart: unless-stopped
    
    # Health check configuration
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
      
    # Resource limits (appropriate for 30-account scale)
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M

  # PostgreSQL Database Service
  ebay-database:
    image: postgres:15-alpine
    container_name: ebay-manager-database
    ports:
      - "5432:5432"  # Only for development - remove in production
    environment:
      # PostgreSQL Configuration
      - POSTGRES_DB=ebay_manager
      - POSTGRES_USER=ebay_user
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256
      
      # Performance Configuration
      - POSTGRES_SHARED_PRELOAD_LIBRARIES=pg_stat_statements
      - POSTGRES_MAX_CONNECTIONS=100
      - POSTGRES_SHARED_BUFFERS=256MB
      - POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
      - POSTGRES_MAINTENANCE_WORK_MEM=64MB
      - POSTGRES_CHECKPOINT_COMPLETION_TARGET=0.9
      - POSTGRES_WAL_BUFFERS=16MB
      - POSTGRES_DEFAULT_STATISTICS_TARGET=100
      
    volumes:
      - ebay_database_data:/var/lib/postgresql/data
      - ./database/init:/docker-entrypoint-initdb.d
      - ebay_logs:/var/log/postgresql
      
    networks:
      - ebay-network
      
    restart: unless-stopped
    
    # Health check for database
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ebay_user -d ebay_manager"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
      
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 256M
    
    # Security hardening
    command: >
      postgres
      -c log_statement=all
      -c log_destination=stderr
      -c log_min_duration_statement=1000
      -c log_line_prefix='%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
      -c log_lock_waits=on
      -c log_temp_files=0

  # Redis Cache & Session Store
  ebay-redis:
    image: redis:7-alpine
    container_name: ebay-manager-redis
    ports:
      - "6379:6379"  # Only for development - remove in production
    environment:
      # Redis Configuration
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - REDIS_MAXMEMORY=512mb
      - REDIS_MAXMEMORY_POLICY=allkeys-lru
      - REDIS_TIMEOUT=300
      - REDIS_TCP_KEEPALIVE=60
      
    volumes:
      - ebay_redis_data:/data
      - ./redis/redis.conf:/usr/local/etc/redis/redis.conf
      - ebay_logs:/var/log/redis
      
    networks:
      - ebay-network
      
    restart: unless-stopped
    
    # Health check for Redis
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s
      
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.1'
          memory: 128M
    
    # Redis configuration with authentication
    command: >
      redis-server
      --requirepass ${REDIS_PASSWORD}
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
      --save 900 1
      --save 300 10
      --save 60 10000
      --appendonly yes
      --appendfsync everysec

# Network Configuration
networks:
  ebay-network:
    name: ebay-manager-network
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1

# Volume Configuration
volumes:
  # Database persistent storage
  ebay_database_data:
    name: ebay_database_data
    driver: local
    
  # Redis persistent storage  
  ebay_redis_data:
    name: ebay_redis_data
    driver: local
    
  # File uploads storage
  ebay_uploads:
    name: ebay_uploads
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${UPLOAD_PATH:-./uploads}
      
  # Centralized logging
  ebay_logs:
    name: ebay_logs
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${LOG_PATH:-./logs}
```

### Development Override (docker-compose.override.yml)
```yaml
# docker-compose.override.yml - Development-specific overrides
version: '3.8'

services:
  ebay-api:
    build:
      target: development
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
      - LOG_LEVEL=DEBUG
      - RELOAD=true
    volumes:
      - .:/app
      - /app/node_modules  # Prevent overwriting node_modules
    ports:
      - "8000:8000"
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

  ebay-database:
    ports:
      - "5432:5432"  # Expose for development tools
    environment:
      - POSTGRES_LOG_STATEMENT=all
      - POSTGRES_LOG_MIN_DURATION_STATEMENT=0

  ebay-redis:
    ports:
      - "6379:6379"  # Expose for development tools
```

---

## Service Specifications

### FastAPI Application Service

**Purpose**: Main application server handling all business logic
**Technology**: FastAPI with Uvicorn ASGI server
**Responsibilities**:
- REST API endpoints for all features
- JWT authentication and authorization  
- CSV file processing and validation
- Background job management
- Database operations through SQLAlchemy ORM
- Redis caching and session management

**Key Features**:
```python
# Service capabilities
- Async/await support for high concurrency
- Automatic OpenAPI/Swagger documentation
- Pydantic data validation and serialization
- Built-in request/response middleware
- Exception handling with custom error responses
- File upload handling with streaming
- Background task execution
- Dependency injection system
```

**Health Check Endpoint**:
```python
# /health endpoint implementation
@app.get("/health")
async def health_check():
    """Comprehensive health check for all services"""
    checks = {
        "api": "healthy",
        "database": await check_database_connection(),
        "redis": await check_redis_connection(),
        "storage": check_file_system_access(),
        "memory": check_memory_usage(),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Determine overall health
    all_healthy = all(status == "healthy" for status in checks.values() if status != checks["timestamp"])
    
    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": checks,
        "version": "1.0.0",
        "uptime": get_uptime_seconds()
    }
```

### PostgreSQL Database Service

**Purpose**: Primary data storage for all application data
**Technology**: PostgreSQL 15 with Alpine Linux base
**Responsibilities**:
- User and account data storage
- Order, listing, and product data
- Customer and supplier information
- Message and communication history
- File metadata and processing logs
- System configuration and settings

**Database Configuration**:
```sql
-- Key PostgreSQL settings for 30-account scale
max_connections = 100              -- Adequate for FastAPI connection pool
shared_buffers = 256MB             -- 25% of allocated memory
effective_cache_size = 1GB         -- Available system memory estimate  
maintenance_work_mem = 64MB        -- For index creation and maintenance
checkpoint_completion_target = 0.9  -- Smooth checkpoint writes
wal_buffers = 16MB                 -- Write-ahead logging buffer
work_mem = 4MB                     -- Per-operation memory limit
```

**Extensions and Features**:
```sql
-- Essential PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";    -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pg_trgm";      -- Trigram matching for search
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- Query performance tracking
CREATE EXTENSION IF NOT EXISTS "btree_gin";    -- GIN indexes for faster queries
```

**Backup Strategy**:
```bash
# Automated backup configuration
# Daily full backup at 2 AM
0 2 * * * /usr/local/bin/pg_dump -h localhost -U ebay_user ebay_manager > /backups/daily/$(date +\%Y\%m\%d).sql

# Weekly full backup with compression
0 2 * * 0 /usr/local/bin/pg_dump -h localhost -U ebay_user -Fc ebay_manager > /backups/weekly/$(date +\%Y\%m\%d).backup

# Transaction log archiving for point-in-time recovery
archive_mode = on
archive_command = 'cp %p /backups/wal_archive/%f'
```

### Redis Cache & Session Store

**Purpose**: High-performance caching and session management
**Technology**: Redis 7 with Alpine Linux base
**Responsibilities**:
- User session storage (DB 1)
- API response caching (DB 2) 
- Background job queue (DB 3)
- Rate limiting counters (DB 4)
- Temporary data storage (DB 0)

**Database Allocation**:
```
DB 0: Default/Temporary data (connection testing, temporary keys)
DB 1: User sessions (JWT blacklist, user preferences, login tracking)
DB 2: API response cache (dashboard metrics, frequently accessed data)
DB 3: Background jobs (file processing queue, job status, results)
DB 4: Rate limiting (API rate limits, user request counters)
```

**Memory Management**:
```redis
# Redis memory configuration for 30-account scale
maxmemory 512mb                    # Total memory limit
maxmemory-policy allkeys-lru       # Evict least recently used keys
maxmemory-samples 5                # LRU sample size

# Persistence configuration
save 900 1                         # Save after 900 seconds if 1+ keys changed
save 300 10                        # Save after 300 seconds if 10+ keys changed  
save 60 10000                      # Save after 60 seconds if 10000+ keys changed
appendonly yes                     # Enable append-only file
appendfsync everysec               # Sync to disk every second
```

---

## Network & Security Configuration

### Network Architecture
```
External Network (Internet)
         ↓
Host Machine (Port 8000)
         ↓
Docker Bridge Network (172.20.0.0/16)
    ├── ebay-api (172.20.0.2:8000)
    ├── ebay-database (172.20.0.3:5432)  
    └── ebay-redis (172.20.0.4:6379)
```

### Security Hardening

**Container Security**:
```yaml
# Security configurations applied to all services
security_opt:
  - no-new-privileges:true        # Prevent privilege escalation
  - seccomp:unconfined           # Allow necessary system calls
read_only: true                   # Read-only root filesystem where possible
tmpfs:
  - /tmp                         # Temporary filesystem in memory
  - /var/run                     # Runtime data in memory
user: "1000:1000"                # Run as non-root user
cap_drop:
  - ALL                          # Drop all capabilities
cap_add:
  - CHOWN                        # Only essential capabilities
  - SETGID
  - SETUID
```

**Network Security**:
```yaml
# Network isolation and security
networks:
  ebay-network:
    driver: bridge
    enable_ipv6: false            # Disable IPv6 for simplicity
    internal: false               # Allow external access to API only
    ipam:
      config:
        - subnet: 172.20.0.0/16   # Private network range
          gateway: 172.20.0.1     # Gateway for external communication
```

**Environment Variable Security**:
```bash
# .env file template (NEVER commit to version control)
# Database Security
POSTGRES_PASSWORD=your_secure_database_password_here
DATABASE_ENCRYPTION_KEY=your_database_encryption_key_32_chars

# Redis Security  
REDIS_PASSWORD=your_secure_redis_password_here

# JWT Security
JWT_SECRET_KEY=your_jwt_secret_key_minimum_32_characters
JWT_REFRESH_SECRET_KEY=your_jwt_refresh_secret_key_minimum_32_characters

# File Upload Security
UPLOAD_PATH=/secure/upload/directory
MAX_UPLOAD_SIZE=104857600  # 100MB in bytes

# Logging Security
LOG_PATH=/secure/log/directory

# External Service Configuration
SMTP_USERNAME=your_email_service_username
SMTP_PASSWORD=your_email_service_password
```

---

## Deployment & Management

### Production Deployment Commands
```bash
# Initial setup
mkdir -p ebay-manager/{uploads,logs,backups/{daily,weekly,wal_archive}}
cd ebay-manager

# Create environment file from template
cp .env.template .env
# Edit .env with secure passwords and configuration

# Generate secure secrets
echo "JWT_SECRET_KEY=$(openssl rand -base64 32)" >> .env
echo "DATABASE_ENCRYPTION_KEY=$(openssl rand -base64 32)" >> .env
echo "POSTGRES_PASSWORD=$(openssl rand -base64 16)" >> .env
echo "REDIS_PASSWORD=$(openssl rand -base64 16)" >> .env

# Deploy infrastructure
docker-compose up -d

# Verify deployment
docker-compose ps
docker-compose logs -f ebay-api

# Run health checks
curl http://localhost:8000/health | jq
```

### Development Environment Setup
```bash
# Development setup with hot-reload
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

# Database development tools
docker-compose exec ebay-database psql -U ebay_user -d ebay_manager

# Redis development tools
docker-compose exec ebay-redis redis-cli -a ${REDIS_PASSWORD}

# View logs in development
docker-compose logs -f ebay-api
docker-compose logs -f ebay-database  
docker-compose logs -f ebay-redis
```

### Monitoring & Maintenance
```bash
# Service status monitoring
docker-compose ps
docker stats $(docker-compose ps -q)

# Database maintenance
docker-compose exec ebay-database pg_dump -U ebay_user ebay_manager > backup_$(date +%Y%m%d).sql

# Redis monitoring
docker-compose exec ebay-redis redis-cli -a ${REDIS_PASSWORD} info memory
docker-compose exec ebay-redis redis-cli -a ${REDIS_PASSWORD} monitor

# Log rotation and cleanup
docker-compose exec ebay-api find /app/logs -name "*.log" -mtime +7 -delete
docker system prune -f

# Security updates
docker-compose pull
docker-compose up -d --force-recreate
```

---

## Performance Optimization

### Resource Allocation (30-Account Scale)
```yaml
# Optimized resource limits for 30 eBay accounts
ebay-api:
  deploy:
    resources:
      limits:
        cpus: '2.0'        # 2 CPU cores maximum
        memory: 2G         # 2GB memory maximum
      reservations:
        cpus: '0.5'        # 0.5 CPU guaranteed
        memory: 512M       # 512MB guaranteed

ebay-database:
  deploy:
    resources:
      limits:
        cpus: '1.5'        # 1.5 CPU cores for database operations
        memory: 1G         # 1GB for PostgreSQL buffers and cache
      reservations:
        cpus: '0.25'       # Minimum CPU guarantee
        memory: 256M       # Minimum memory guarantee

ebay-redis:
  deploy:
    resources:
      limits:
        cpus: '0.5'        # 0.5 CPU for cache operations
        memory: 512M       # 512MB for Redis data
      reservations:
        cpus: '0.1'        # Minimum CPU guarantee
        memory: 128M       # Minimum memory guarantee
```

### Connection Pooling Configuration
```python
# SQLAlchemy connection pool settings
DATABASE_POOL_SIZE = 20           # Concurrent connections to database
DATABASE_MAX_OVERFLOW = 30        # Additional connections when pool exhausted
DATABASE_POOL_TIMEOUT = 30        # Seconds to wait for connection
DATABASE_POOL_RECYCLE = 3600      # Seconds before connection refresh
DATABASE_POOL_PRE_PING = True     # Verify connections before use

# Redis connection pool settings  
REDIS_CONNECTION_POOL_SIZE = 10   # Connection pool size
REDIS_CONNECTION_TIMEOUT = 5      # Connection timeout seconds
REDIS_SOCKET_TIMEOUT = 5          # Socket operation timeout
REDIS_SOCKET_KEEPALIVE = True     # Enable TCP keepalive
REDIS_SOCKET_KEEPALIVE_OPTIONS = {
    "TCP_KEEPIDLE": 600,          # Start keepalive after 10 minutes
    "TCP_KEEPINTVL": 30,          # Keepalive interval 30 seconds  
    "TCP_KEEPCNT": 3              # 3 failed keepalive attempts = disconnect
}
```

---

## Troubleshooting Guide

### Common Issues & Solutions

**Service Won't Start**:
```bash
# Check container logs
docker-compose logs ebay-api
docker-compose logs ebay-database
docker-compose logs ebay-redis

# Check port conflicts
netstat -tulpn | grep :8000
netstat -tulpn | grep :5432
netstat -tulpn | grep :6379

# Check environment variables
docker-compose config
```

**Database Connection Issues**:
```bash
# Test database connectivity
docker-compose exec ebay-database pg_isready -U ebay_user -d ebay_manager

# Check database logs
docker-compose logs ebay-database | grep ERROR

# Connect manually for debugging
docker-compose exec ebay-database psql -U ebay_user -d ebay_manager
```

**Redis Connection Issues**:
```bash
# Test Redis connectivity
docker-compose exec ebay-redis redis-cli -a ${REDIS_PASSWORD} ping

# Check Redis configuration
docker-compose exec ebay-redis redis-cli -a ${REDIS_PASSWORD} config get "*"

# Monitor Redis operations
docker-compose exec ebay-redis redis-cli -a ${REDIS_PASSWORD} monitor
```

**Performance Issues**:
```bash
# Monitor resource usage
docker stats $(docker-compose ps -q)

# Check application performance
curl http://localhost:8000/health | jq '.checks'

# Database performance monitoring
docker-compose exec ebay-database psql -U ebay_user -d ebay_manager -c "SELECT * FROM pg_stat_activity;"
```

### Recovery Procedures

**Database Recovery**:
```bash
# Stop services
docker-compose down

# Restore from backup
docker-compose up -d ebay-database
docker-compose exec ebay-database psql -U ebay_user -d ebay_manager < backup_20240329.sql

# Start all services
docker-compose up -d
```

**Redis Recovery**:
```bash
# Redis auto-recovery from AOF/RDB files
docker-compose restart ebay-redis

# Manual Redis data restore if needed
docker-compose down ebay-redis
# Copy backup files to redis data volume
docker-compose up -d ebay-redis
```

---

## Success Criteria & Validation

### Infrastructure Requirements ✅
- [ ] All 3 services start successfully without errors
- [ ] Health checks pass for API, database, and Redis  
- [ ] Inter-service communication works (API ↔ DB ↔ Redis)
- [ ] Proper resource allocation and limits applied
- [ ] Security configurations active (non-root users, read-only filesystems)
- [ ] Data persistence verified (database and Redis data survives restarts)
- [ ] Backup and recovery procedures tested and working
- [ ] Development and production configurations separated
- [ ] Environment variable security implemented
- [ ] Logging configured and accessible

### Performance Requirements ✅
- [ ] API health check response < 100ms
- [ ] Database connection time < 50ms
- [ ] Redis operations < 10ms
- [ ] Container startup time < 30 seconds for all services
- [ ] Memory usage within allocated limits (2GB total)
- [ ] CPU usage < 50% under normal load
- [ ] Network latency between services < 5ms
- [ ] File system access working for uploads and logs

### SOLID/YAGNI Compliance ✅
- [ ] **Single Responsibility**: Each service has clear, focused purpose
- [ ] **Open/Closed**: Infrastructure can be extended without modification
- [ ] **Interface Segregation**: Clean service boundaries, minimal coupling
- [ ] **Dependency Inversion**: Services use abstract interfaces
- [ ] **YAGNI Applied**: No over-engineering, essential services only
- [ ] No premature optimization (appropriate for 30-account scale)
- [ ] Eliminated unnecessary complexity (microservices, service mesh, etc.)

**Next Step**: Proceed to [02-database-schema.md](./02-database-schema.md) for complete database design and relationships.