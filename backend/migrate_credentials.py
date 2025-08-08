#!/usr/bin/env python3
"""
Secure Credential Migration Script
Migrates from hardcoded credentials to secure environment-based configuration
"""

import os
import bcrypt
import secrets
import string
from pathlib import Path

def generate_secure_password(length=32):
    """Generate cryptographically secure password"""
    alphabet = string.ascii_letters + string.digits + '@#$%&*'
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_jwt_secret(length=64):
    """Generate secure JWT secret"""
    return secrets.token_urlsafe(length)

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_secure_env():
    """Create secure environment configuration"""
    
    # Generate secure credentials
    jwt_secret = generate_jwt_secret()
    admin_password = generate_secure_password()
    admin_password_hash = hash_password(admin_password)
    
    env_content = f"""# Secure Environment Configuration
# Generated on {os.popen('date').read().strip()}

# JWT Configuration
JWT_SECRET_KEY={jwt_secret}
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Admin Authentication
ADMIN_EMAIL=admin@passivecaptcha.com
ADMIN_SECRET={admin_password}
ADMIN_PASSWORD_HASH={admin_password_hash}
ADMIN_NAME=System Administrator

# Database Configuration
DATABASE_URL=sqlite:///passive_captcha_production.db

# Redis Configuration  
REDIS_URL=redis://localhost:6379/0

# Security Settings
CONFIDENCE_THRESHOLD=0.6
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=3600

# Application Settings
FLASK_ENV=production
DEBUG=False
TESTING=False
"""

    # Write to .env.secure
    env_path = Path(__file__).parent / '.env.secure'
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print("✅ Secure environment configuration created!")
    print(f"📁 File: {env_path}")
    print("\n🔐 IMPORTANT - Save these credentials securely:")
    print(f"Admin Email: admin@passivecaptcha.com")
    print(f"Admin Password: {admin_password}")
    print(f"JWT Secret: {jwt_secret[:20]}...")
    
    return {
        'admin_password': admin_password,
        'admin_password_hash': admin_password_hash,
        'jwt_secret': jwt_secret
    }

def update_main_py():
    """Update main.py to remove hardcoded credentials"""
    main_py_path = Path(__file__).parent / 'main.py'
    
    if not main_py_path.exists():
        print("❌ main.py not found")
        return
    
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    # Remove hardcoded admin secret
    updated_content = content.replace(
        "'ADMIN_SECRET': os.getenv('ADMIN_SECRET', 'Admin123'),",
        "'ADMIN_SECRET': os.getenv('ADMIN_SECRET', None),"
    )
    
    # Add environment validation
    validation_code = '''
    # Validate critical environment variables
    required_vars = ['ADMIN_SECRET', 'JWT_SECRET_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    '''
    
    # Insert after imports
    if 'import os' in updated_content and validation_code not in updated_content:
        updated_content = updated_content.replace(
            'import os',
            f'import os{validation_code}'
        )
    
    with open(main_py_path, 'w') as f:
        f.write(updated_content)
    
    print("✅ main.py updated with secure configuration")

if __name__ == "__main__":
    print("🔒 Starting Secure Credential Migration...\n")
    
    credentials = create_secure_env()
    update_main_py()
    
    print("\n" + "="*60)
    print("🔐 SECURITY UPGRADE COMPLETED")
    print("="*60)
    print("\n📋 Next Steps:")
    print("1. Copy .env.secure to .env.production")
    print("2. Update your password manager with new credentials")
    print("3. Restart the application")
    print("4. Test authentication with new password")
    print("\n⚠️  IMPORTANT: The old password 'Admin123' will no longer work!")