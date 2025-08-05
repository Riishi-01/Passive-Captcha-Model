# Environment Variables for Passive CAPTCHA Model

## Required Environment Variables for Production Deployment

### Core Application Settings
```bash
# Application Environment
ENV=production
FLASK_ENV=production

# Server Configuration
PORT=5003                           # Port for the server (Railway auto-assigns this)
HOST=0.0.0.0                       # Host to bind to
SERVE_FRONTEND=true                # Whether to serve frontend static files

# Security Keys (CRITICAL - must be set in production)
SECRET_KEY=your-secret-key-here                    # Flask secret key for sessions
JWT_SECRET_KEY=your-jwt-secret-key-here            # JWT token signing key
ADMIN_SECRET=Admin123                              # Admin authentication secret

# Admin User Configuration  
DEFAULT_ADMIN_EMAIL=admin@passivecaptcha.com      # Default admin email
DEFAULT_ADMIN_PASSWORD=Admin123                   # Default admin password (uses ADMIN_SECRET if not set)
ADMIN_PASSWORD_HASH=                              # Pre-hashed admin password (optional)
```

### Database Configuration
```bash
# Database (Railway provides DATABASE_URL automatically)
DATABASE_URL=postgresql://user:pass@host:port/db  # PostgreSQL connection string
# or for SQLite:
# DATABASE_URL=sqlite:///passive_captcha_production.db
```

### Redis Configuration (Optional)
```bash
# Redis for caching and rate limiting (fallback to in-memory if not available)
REDIS_URL=redis://host:port/db                    # Redis connection string
```

### ML Model Configuration
```bash
# Machine Learning Model Settings
MODEL_PATH=models/passive_captcha_rf.pkl          # Path to Random Forest model
CONFIDENCE_THRESHOLD=0.6                          # ML confidence threshold (0.0-1.0)
```

### Rate Limiting
```bash
# Rate Limiting Configuration
RATE_LIMIT_REQUESTS=1000                          # Requests per minute limit
```

### CORS and Domain Configuration
```bash
# API and Frontend URLs (Railway auto-configures these)
API_BASE_URL=https://your-app.up.railway.app      # Base URL for API
WEBSOCKET_URL=wss://your-app.up.railway.app       # WebSocket URL
ALLOWED_ORIGINS=https://your-domain.com,https://another-domain.com  # Comma-separated allowed origins
```

### Logging Configuration
```bash
# Logging Settings
LOG_LEVEL=INFO                                    # Log level (DEBUG, INFO, WARNING, ERROR)
LOG_FILE=logs/app.log                            # Log file path
LOG_MAX_SIZE=10485760                            # Max log file size (10MB)
LOG_BACKUP_COUNT=10                              # Number of log backups to keep
```

### Platform-Specific Variables (Auto-provided by Railway)
```bash
# Railway automatically provides these:
RAILWAY_PUBLIC_DOMAIN=your-app.up.railway.app    # Public domain
RENDER_EXTERNAL_URL=https://your-app.up.railway.app  # External URL (legacy support)
```

## Minimal Required Variables for Railway Deployment

For a basic Railway deployment, you MUST set these:

```bash
# Critical Security Variables
JWT_SECRET_KEY=your-super-secret-jwt-key-minimum-32-characters
ADMIN_SECRET=YourSecureAdminPassword123

# Optional but Recommended
SECRET_KEY=your-flask-secret-key-for-sessions
DATABASE_URL=                                    # Railway PostgreSQL addon auto-provides this
REDIS_URL=                                       # Railway Redis addon auto-provides this
```

## Setting Environment Variables in Railway

1. **Via Railway Dashboard:**
   - Go to your project → Variables tab
   - Add each variable individually

2. **Via Railway CLI:**
   ```bash
   railway variables set JWT_SECRET_KEY=your-secret-key
   railway variables set ADMIN_SECRET=your-admin-password
   ```

3. **Via `railway.toml` (already configured):**
   ```toml
   [services.variables]
   ENV = "production"
   FLASK_ENV = "production"
   JWT_SECRET = "${{JWT_SECRET}}"
   ADMIN_SECRET = "${{ADMIN_SECRET}}"
   ```

## Default Values (Fallbacks)

If environment variables are not set, the application uses these defaults:

| Variable | Default Value | Safe for Production? |
|----------|---------------|---------------------|
| `PORT` | 5003 | ✅ (Railway overrides) |
| `SECRET_KEY` | "passive-captcha-production-secret" | ❌ Must change |
| `JWT_SECRET_KEY` | Auto-generated | ✅ |
| `ADMIN_SECRET` | "Admin123" | ❌ Must change |
| `DATABASE_URL` | SQLite local file | ⚠️ Use PostgreSQL |
| `REDIS_URL` | "redis://localhost:6379/0" | ⚠️ Falls back to in-memory |
| `CONFIDENCE_THRESHOLD` | 0.6 | ✅ |
| `RATE_LIMIT_REQUESTS` | 1000 | ✅ |

## Security Notes

- **Never commit sensitive values to git**
- **Always set custom values for JWT_SECRET_KEY and ADMIN_SECRET in production**
- **Use Railway's PostgreSQL addon for DATABASE_URL**
- **Use Railway's Redis addon for REDIS_URL (optional but recommended)**