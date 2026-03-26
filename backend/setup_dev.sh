#!/bin/bash
# Development setup script for MikroTik Controller Backend

set -e

echo "🚀 Setting up MikroTik Controller Backend Development Environment"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    
    # Generate random secrets
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Update .env with generated secrets
    sed -i.bak "s/your_secret_key_at_least_32_characters_long_here/$SECRET_KEY/" .env
    sed -i.bak "s/your_encryption_key_at_least_32_characters_long_here/$ENCRYPTION_KEY/" .env
    rm .env.bak
    
    echo "✅ .env file created with generated secrets"
else
    echo "✅ .env file already exists"
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
echo "✅ Dependencies installed"

# Check if PostgreSQL is running
echo ""
echo "🔍 Checking PostgreSQL connection..."
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "✅ PostgreSQL is running"
else
    echo "⚠️  PostgreSQL is not running. Please start PostgreSQL:"
    echo "   macOS: brew services start postgresql"
    echo "   Linux: sudo systemctl start postgresql"
    echo ""
    echo "   Or use Docker:"
    echo "   docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15"
    exit 1
fi

# Check if Redis is running
echo ""
echo "🔍 Checking Redis connection..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "⚠️  Redis is not running. Please start Redis:"
    echo "   macOS: brew services start redis"
    echo "   Linux: sudo systemctl start redis"
    echo ""
    echo "   Or use Docker:"
    echo "   docker run -d --name redis -p 6379:6379 redis:7"
    exit 1
fi

# Create database if it doesn't exist
echo ""
echo "🗄️  Setting up database..."
DB_NAME=$(grep DB_NAME .env | cut -d '=' -f2)
DB_USER=$(grep DB_USER .env | cut -d '=' -f2)

if psql -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo "✅ Database '$DB_NAME' already exists"
else
    echo "📝 Creating database '$DB_NAME'..."
    createdb -U $DB_USER $DB_NAME
    echo "✅ Database created"
fi

# Run migrations
echo ""
echo "🔄 Running database migrations..."
alembic upgrade head
echo "✅ Migrations complete"

# Validate configuration
echo ""
echo "🔍 Validating configuration..."
python validate_config.py
echo "✅ Configuration valid"

echo ""
echo "✨ Development environment setup complete!"
echo ""
echo "To start the development server:"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "API will be available at: http://localhost:8000"
echo "API docs will be available at: http://localhost:8000/docs"
echo ""
