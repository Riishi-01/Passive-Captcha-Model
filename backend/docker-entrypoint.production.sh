#!/bin/bash
set -e

echo "🚀 Starting Passive CAPTCHA Production Server..."

# Wait for database
echo "⏳ Waiting for database connection..."
until python -c "
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
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
"; do
    echo "⏳ Database not ready, waiting 5 seconds..."
    sleep 5
done

# Wait for Redis
echo "⏳ Waiting for Redis connection..."
until python -c "
import redis
import os
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
try:
    client = redis.Redis.from_url(redis_url)
    client.ping()
    print('✅ Redis connected successfully')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    sys.exit(1)
"; do
    echo "⏳ Redis not ready, waiting 5 seconds..."
    sleep 5
done

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
echo "🌟 Starting application with: $@"

# Execute the main command
exec "$@"