#!/bin/bash
# -*- coding: utf-8 -*-
# Vercel Deployment Script

echo "=== PASSIVE CAPTCHA DEPLOYMENT ==="
echo

# Check if we're ready for deployment
echo "Running pre-deployment validation..."
python3 scripts/testing/final_deployment_validation.py

if [ $? -ne 0 ]; then
    echo "[ERROR] Pre-deployment validation failed!"
    exit 1
fi

echo
echo "Pre-deployment validation passed!"
echo

# Show what will be deployed
echo "Deployment Configuration:"
echo "  - Backend: Flask + Python 3.9"
echo "  - Frontend: Vue.js + Vite"
echo "  - Database: PostgreSQL (external)"
echo "  - Cache: Redis (external)"
echo

# Check Vercel CLI
if ! command -v vercel &> /dev/null; then
    echo "[ERROR] Vercel CLI not found. Install with: npm i -g vercel"
    exit 1
fi

echo "Vercel CLI found. Starting deployment..."
echo

# Deploy to Vercel
vercel --prod

echo
echo "Deployment completed!"
echo
echo "Next steps:"
echo "1. Configure environment variables in Vercel dashboard"
echo "2. Set up external PostgreSQL database"
echo "3. Configure Redis cache"
echo "4. Test the deployment"
