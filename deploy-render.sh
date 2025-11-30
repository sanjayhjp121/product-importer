#!/bin/bash

# Render Deployment Script
# This script helps deploy your application to Render using the render.yaml Blueprint

set -e

echo "🚀 Render Deployment Helper"
echo "=========================="
echo ""

# Check if code is pushed
echo "📦 Checking Git status..."
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  You have uncommitted changes. Committing them..."
    git add -A
    git commit -m "Prepare for Render deployment" || echo "No changes to commit"
fi

echo "📤 Pushing to GitHub..."
git push origin main

echo ""
echo "✅ Code pushed to GitHub successfully!"
echo ""
echo "📋 Next Steps:"
echo "=============="
echo ""
echo "1. Go to Render Dashboard: https://dashboard.render.com"
echo ""
echo "2. Click 'New +' → 'Blueprint'"
echo ""
echo "3. Connect your GitHub repository: https://github.com/sanjayhjp121/product-importer"
echo ""
echo "4. Render will automatically detect render.yaml and create:"
echo "   - PostgreSQL Database (product-importer-db)"
echo "   - Web Service (product-importer-web)"
echo "   - Worker Service (product-importer-worker)"
echo ""
echo "5. After Blueprint creates the services, you need to:"
echo "   a. Create a Redis instance manually:"
echo "      - Go to 'New +' → 'Redis'"
echo "      - Name: product-importer-redis"
echo "      - Copy the Internal Redis URL"
echo ""
echo "   b. Add Redis URLs to both web and worker services:"
echo "      - Go to each service → Environment"
echo "      - Set REDIS_URL = (your Redis Internal URL)"
echo "      - Set CELERY_BROKER_URL = (same as REDIS_URL)"
echo "      - Set CELERY_RESULT_BACKEND = (same as REDIS_URL)"
echo ""
echo "6. The database will be automatically linked and initialized!"
echo ""
echo "🌐 Your app will be available at: https://product-importer-web.onrender.com"
echo ""
echo "📝 For detailed instructions, see RENDER_DEPLOYMENT.md"
echo ""

