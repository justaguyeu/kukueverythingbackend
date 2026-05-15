#!/bin/bash
# ─────────────────────────────────────────────────────
#  KUKU EVERYTHING — Backend Setup Script
# ─────────────────────────────────────────────────────
set -e

echo ""
echo "🐓 ==========================================="
echo "   KUKU EVERYTHING — Backend Setup"
echo "=============================================="
echo ""

# Python check
if ! command -v python3 &>/dev/null; then
  echo "❌ Python 3 not found. Install it first."
  exit 1
fi

# Virtual environment
if [ ! -d "venv" ]; then
  echo "📦 Creating virtual environment..."
  python3 -m venv venv
fi
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt -q

# .env setup
if [ ! -f .env ]; then
  cp .env.example .env
  echo ""
  echo "⚠️  .env created from .env.example."
  echo "    Open .env and configure your Email and SMS settings."
  echo "    For development, the defaults (console mode) work with zero setup."
  echo ""
fi

# Migrations
echo "🗄️  Running migrations..."
python manage.py makemigrations accounts businesses orders reviews notifications
python manage.py migrate

# Superuser
echo ""
echo "👤 Create your admin account:"
python manage.py createsuperuser

# Static files
echo ""
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput -v 0

echo ""
echo "✅ ============================================"
echo "   Setup complete!"
echo "   Run: source venv/bin/activate"
echo "        python manage.py runserver"
echo "   Admin: http://localhost:8000/admin/"
echo "=============================================="
