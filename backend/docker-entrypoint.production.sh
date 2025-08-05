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
    # Try to connect to database directly without Flask context
    from sqlalchemy import create_engine, text
    database_url = os.getenv('DATABASE_URL', 'sqlite:///passive_captcha_production.db')
    
    # Handle Railway PostgreSQL URL format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    engine = create_engine(database_url)
    with engine.connect() as connection:
        connection.execute(text('SELECT 1'))
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
import os
sys.path.insert(0, '/app')
try:
    from app.database import init_db
    database_url = os.getenv('DATABASE_URL', 'sqlite:///passive_captcha_production.db')
    success = init_db(database_url)
    if success:
        print('✅ Database initialized successfully')
    else:
        print('⚠️ Database initialization had issues but continuing...')
except Exception as e:
    print(f'⚠️ Database initialization failed: {e}')
    print('📝 Application will attempt to initialize on startup')
"

# Load ML model
echo "🤖 Loading ML model..."
python -c "
import sys
import os
sys.path.insert(0, '/app')
try:
    # Check if model files exist
    model_path = '/app/models/passive_captcha_rf.pkl'
    scaler_path = '/app/models/passive_captcha_rf_scaler.pkl'
    
    if os.path.exists(model_path) and os.path.exists(scaler_path):
        print('✅ ML model files found')
        print(f'   Model: {model_path}')
        print(f'   Scaler: {scaler_path}')
    else:
        print('⚠️  ML model files not found')
        print('📝 Application will load models on first request')
except Exception as e:
    print(f'⚠️  ML model check failed: {e}')
    print('📝 Application will attempt to load models on startup')
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
    exec python main.py --host 0.0.0.0 --gunicorn
else
    echo "🌟 Starting application with: $@"
    exec "$@"
fi