#!/bin/bash
set -e

echo "🚀 Research Orchestrator Setup"
echo "================================"

# Step 1: Create Python virtual environment
echo "📦 Creating Python virtual environment..."
python -m venv .venv

# Activate venv based on OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

# Step 2: Install dependencies
echo "📚 Installing dependencies..."
pip install -e .

# Step 3: Start Supabase and capture service key
echo "🗄️  Starting Supabase..."
npx supabase start

# Wait a moment for Supabase to be ready
sleep 2

# Extract service key from supabase status JSON
echo "📋 Extracting Supabase credentials..."
SERVICE_KEY=$(npx supabase status | grep -o '"SERVICE_ROLE_KEY":"[^"]*' | cut -d'"' -f4)

if [ -z "$SERVICE_KEY" ]; then
    echo "⚠️  Could not extract service key. Please enter manually:"
    npx supabase status
    read -p "Enter SERVICE_ROLE_KEY from above: " SERVICE_KEY
fi

# Step 4: Create .env file
echo "⚙️  Creating .env file..."
cat > .env << EOF
# Supabase (local CLI defaults from \`supabase start\`)
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_SERVICE_KEY=$SERVICE_KEY

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_CHAT_MODEL=llama3.1

# Web search providers
SEARCH_PROVIDERS=brave
BRAVE_API_KEY=${BRAVE_API_KEY:-replace-with-brave-search-api-key}

# SEC EDGAR
SEC_USER_AGENT=MyCompanyResearch ujculbe@gmail.com

# Reddit (optional - comment out to skip)
# REDDIT_CLIENT_ID=
# REDDIT_CLIENT_SECRET=
# REDDIT_USER_AGENT=research-orchestrator/0.1
EOF

echo "✅ .env created with SUPABASE_SERVICE_KEY"

# Step 5: Reset database (apply migrations)
echo "🔄 Resetting Supabase database..."
npx supabase db reset

# Step 6: Seed Workday entities
echo "🌱 Seeding Workday entities..."
python scripts/seed_workday_entities.py

# Step 7: First run
echo "▶️  Running first orchestration..."
research-orchestrator run

echo ""
echo "✨ Setup complete! Your first run is done."
echo ""
echo "Next steps:"
echo "  - View data in Supabase Studio: http://127.0.0.1:54323"
echo "  - Add more sources: research-orchestrator add-source --help"
echo "  - Schedule runs via Docker + n8n: docker compose up -d --build"
echo ""
