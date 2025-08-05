#!/bin/bash
set -e

echo "🚀 Starting Passive CAPTCHA Production Server..."

# Check database connection
echo "⏳ Checking database connection..."
python -c "
import sys
import os
sys.path.insert(0, '/app')
try:
    from app.database import get_db_session
    session = get_db_session()
    session.execute('SELECT 1')
    session.close()
    print('✅ Database connected successfully')
except Exception as e:
    print(f'⚠️  Database connection issue: {e}')
    print('📝 Application will initialize database or use SQLite fallback')
"

# Check Redis connection (optional)
echo "⏳ Checking Redis connection..."
python -c "
import redis
import os
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
try:
    client = redis.Redis.from_url(redis_url)
    client.ping()
    print('✅ Redis connected successfully')
except Exception as e:
    print(f'⚠️  Redis connection failed: {e}')
    print('📝 Application will continue without Redis (using in-memory fallback)')
"

# Initialize database tables
echo "🔧 Initializing database..."
python -c "
import sys
sys.path.insert(0, '/app')
from app.database import init_db
init_db()
print('✅ Database initialized')
"

# Load ML model
echo "🤖 Loading ML model..."
python -c "
import sys
sys.path.insert(0, '/app')
try:
    from app.ml import load_model
    load_model()
    print('✅ ML model loaded successfully')
except Exception as e:
    print(f'⚠️  ML model loading failed: {e}')
    print('📝 Application will continue without ML model')
"

# Create log directory if it doesn't exist
mkdir -p /app/logs

# Set permissions
chmod 755 /app/logs

echo "✅ Production server initialization complete"

# Default command if none provided
if [ $# -eq 0 ]; then
    echo "🌟 Starting with default command: python main.py"
    PORT=${PORT:-5000}
    exec python main.py --host 0.0.0.0 --port $PORT --gunicorn
else
    echo "🌟 Starting application with: $@"
    exec "$@"
fi