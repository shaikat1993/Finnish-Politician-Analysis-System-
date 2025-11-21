# 🚀 Docker Quick Start Guide

## For New Users Cloning This Repository

This guide helps you run the Finnish Politician Analysis System (FPAS) using Docker in under 5 minutes.

---

## ⚡ Quick Start (3 Steps)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd fpas
```

### Step 2: Create Your Environment File

Copy the example file and add your credentials:

```bash
cp .env.example .env
```

**Now edit the `.env` file:**

```bash
nano .env  # or use any text editor
```

**Required changes:**

```env
# Change these values:
NEO4J_PASSWORD=your_secure_password_here
NEO4J_AUTH=neo4j/your_secure_password_here

# Add your OpenAI API key:
OPENAI_API_KEY=sk-your-actual-openai-key-here
```

**Optional but recommended:**
```env
# Generate a secure API secret:
API_SECRET_KEY=<run: python -c "import secrets; print(secrets.token_urlsafe(32))">
```

### Step 3: Start Docker

```bash
docker-compose up -d
```

**Wait 2-3 minutes** for all services to start (Neo4j takes time to initialize).

---

## ✅ Verify It's Running

Check service status:
```bash
docker-compose ps
```

All services should show "healthy" or "running".

### Access the Application

- **Frontend (Main App)**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474
  - Username: `neo4j`
  - Password: (whatever you set in `.env`)

---

## 🔑 Getting Your OpenAI API Key

If you don't have an OpenAI API key:

1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)
5. Paste it in your `.env` file

**Note**: OpenAI API requires payment. You need credits to run this system.

---

## 🛠️ Common Issues & Solutions

### Issue: "Neo4j connection refused"

**Solution**: Wait longer. Neo4j takes 2-3 minutes to fully start.

```bash
# Check Neo4j logs
docker-compose logs neo4j

# Wait for: "Bolt enabled on 0.0.0.0:7687"
```

### Issue: "Invalid OpenAI API key"

**Solution**: Check your API key in `.env`:
- Should start with `sk-`
- No spaces or quotes around it
- Must be active and have credits

### Issue: "Permission denied" errors

**Solution**: Fix volume permissions:
```bash
sudo chown -R 1000:1000 ./neo4j ./cache ./logs
```

### Issue: Maps not showing in frontend

**Solution**: Already fixed! Just restart frontend:
```bash
docker-compose restart frontend
```

---

## 🔒 Security Notes

### ⚠️ IMPORTANT: Never Commit Your `.env` File!

Your `.env` file contains:
- ❌ Your OpenAI API key (costs you money if stolen)
- ❌ Your database password
- ❌ Other sensitive credentials

The `.env` file is already in `.gitignore`, but double-check:

```bash
# Should output: .env
git check-ignore .env
```

### For Public GitHub Repos

If your repo is public:
1. ✅ Commit `.env.example` (safe template)
2. ❌ Never commit `.env` (real credentials)
3. ✅ Commit `docker-compose.yml` (uses environment variables)
4. ✅ Commit documentation (this guide!)

---

## 📦 What's Running?

After `docker-compose up`, you'll have:

| Service | Purpose | Port |
|---------|---------|------|
| **neo4j** | Graph database storing politician data | 7474, 7687 |
| **ai_pipeline** | AI agents for analysis | Internal only |
| **api** | Backend API (FastAPI) | 8000 |
| **frontend** | User interface (Streamlit) | 8501 |
| **data_collection** | Data scraper (manual start) | Internal only |

---

## 🧪 Testing It Works

### Test 1: Check API Health

```bash
curl http://localhost:8000/api/v1/health
```

Should return: `{"status":"healthy"}`

### Test 2: Open Frontend

Open http://localhost:8501 in your browser.

You should see the FPAS dashboard with navigation on the left.

### Test 3: Try the AI Chat

1. Go to "Politician Chat" tab
2. Ask: "Who is the president of Finland?"
3. You should get an AI-generated response

**If chat works, everything is set up correctly!** 🎉

---

## 🗂️ Project Structure

```
fpas/
├── .env                    # YOUR credentials (never commit!)
├── .env.example            # Template (safe to commit)
├── docker-compose.yml      # Docker configuration
├── frontend/
│   ├── .streamlit/         # Streamlit config (fixes map rendering)
│   └── Dockerfile          # Production-grade container
├── api/                    # FastAPI backend
├── ai_pipeline/            # AI agents with OWASP security
├── data_collection/        # Data scrapers
└── neo4j/                  # Neo4j initialization scripts
```

---

## 🛑 Stopping the Application

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes data!)
docker-compose down -v
```

---

## 🔄 Updating the Application

```bash
# Pull latest code
git pull

# Rebuild containers
docker-compose build --no-cache

# Restart services
docker-compose up -d
```

---

## 💡 Tips for Development

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f frontend
docker-compose logs -f api
```

### Restart a Single Service

```bash
docker-compose restart frontend
```

### Access Container Shell

```bash
docker exec -it fpas-frontend /bin/bash
docker exec -it fpas-api /bin/bash
```

### Run Data Collection Manually

```bash
docker exec -it fpas-data-collection python -m data_collection.main
```

---

## 📚 Additional Documentation

- **Full Setup Guide**: [DOCKER_SETUP.md](DOCKER_SETUP.md)
- **Security Implementation**: [DOCKER_SECURITY_IMPLEMENTATION.md](DOCKER_SECURITY_IMPLEMENTATION.md)
- **OWASP Security Details**: [docs/OWASP_LLM06_IMPLEMENTATION.md](docs/OWASP_LLM06_IMPLEMENTATION.md)

---

## 🆘 Getting Help

### Still Having Issues?

1. Check logs: `docker-compose logs -f`
2. Verify `.env` file has all required variables
3. Ensure Docker has enough resources (4GB+ RAM)
4. Check firewall isn't blocking ports 8000, 8501, 7474, 7687

### For Contributors

If you're contributing to this project:
1. Never commit your `.env` file
2. Test with `docker-compose up` before pushing
3. Update this guide if you change the setup process

---

## ⭐ Success!

If you can:
- ✅ Access http://localhost:8501
- ✅ See the FPAS dashboard
- ✅ Get AI responses in Politician Chat

**Congratulations! You're all set up!** 🎉

Now explore the features:
- 📊 Main Dashboard - Visualize politician networks
- 💬 Politician Chat - Ask questions about Finnish politics
- 🔐 Security Dashboard - See OWASP security in action
- 🧪 Research Tools - Experiment with prompts

---

**Made with ❤️ for academic research on AI security**
