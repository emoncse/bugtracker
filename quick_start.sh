#!/bin/bash

# Bug Tracker Quick Start Script

echo "Bug Tracker - Quick Start"
echo "============================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Check if superuser exists
echo "Checking for superuser..."
if ! python manage.py shell -c "from django.contrib.auth.models import User; print('Superuser exists' if User.objects.filter(is_superuser=True).exists() else 'No superuser')" 2>/dev/null | grep -q "Superuser exists"; then
    echo "Creating superuser..."
    echo "Username: admin"
    echo "Email: admin@example.com"
    echo "Password: admin123"
    python manage.py createsuperuser --username admin --email admin@example.com --noinput
    python manage.py shell -c "from django.contrib.auth.models import User; u = User.objects.get(username='admin'); u.set_password('admin123'); u.save()"
fi

# Seed test data
echo "Seeding test data..."
python manage.py seed_data

# Check if Redis is running
echo "Checking Redis server..."
if ! redis-cli ping >/dev/null 2>&1; then
    echo "Redis server is not running!"
    echo "Please start Redis server:"
    echo "  macOS: brew services start redis"
    echo "  Ubuntu: sudo systemctl start redis-server"
    echo "  Or run: redis-server"
    echo ""
    echo "Starting development server without WebSocket support..."
    echo "Starting development server at http://localhost:8000"
    python manage.py runserver
else
    echo "Redis server is running"
    echo ""
    echo "Choose your server:"
    echo "1. Development server (HTTP only)"
    echo "2. Production server with WebSocket support"
    echo ""
    read -p "Enter your choice (1 or 2): " choice
    
    case $choice in
        1)
            echo "Starting development server at http://localhost:8000"
            python manage.py runserver
            ;;
        2)
            echo "Starting production server with WebSocket support at http://localhost:8000"
            daphne -b 0.0.0.0 -p 8000 config.asgi:application
            ;;
        *)
            echo "Invalid choice. Starting development server..."
            python manage.py runserver
            ;;
    esac
fi 