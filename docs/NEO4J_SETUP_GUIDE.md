# Neo4j Setup Guide for Finnish Political Analysis System

## 🎯 **Setup Options Overview**

| Option | Cost | Signup Required | Best For | Setup Time |
|--------|------|----------------|----------|------------|
| **Local Installation** | Free | ❌ No | Development, Testing | 5 minutes |
| **Docker** | Free | ❌ No | Development, Easy cleanup | 2 minutes |
| **Neo4j AuraDB** | Free tier available | ✅ Yes | Production, Cloud deployment | 10 minutes |

---

## 🏠 **Option 1: Local Neo4j Installation (Recommended)**

### **Step 1: Download Neo4j Desktop**
1. Go to [neo4j.com/download](https://neo4j.com/download/)
2. Click "Download Neo4j Desktop" (no signup required)
3. Choose your operating system (macOS/Windows/Linux)
4. Install the downloaded application

### **Step 2: Create Local Database**
1. Open Neo4j Desktop
2. Click "New" → "Create Project"
3. Name: "Finnish Political Analysis"
4. Click "Add" → "Local DBMS"
5. Name: "fpas-db"
6. Password: Choose a secure password
7. Version: Latest (5.x recommended)
8. Click "Create"

### **Step 3: Start Database**
1. Click the "Start" button on your database
2. Wait for status to show "Active"
3. Note the connection details:
   - **URI**: `bolt://localhost:7687`
   - **Username**: `neo4j`
   - **Password**: Your chosen password

### **Step 4: Configure Environment**
Create/update your `.env` file:
```bash
# Neo4j Local Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_chosen_password
NEO4J_DATABASE=neo4j
```

---

## 🐳 **Option 2: Docker Setup (Fastest)**

### **Step 1: Run Neo4j Container**
```bash
# Create data directories
mkdir -p $HOME/neo4j/{data,logs,import,plugins}

# Run Neo4j container
docker run \
    --name neo4j-fpas \
    -p7474:7474 -p7687:7687 \
    -d \
    -v $HOME/neo4j/data:/data \
    -v $HOME/neo4j/logs:/logs \
    -v $HOME/neo4j/import:/var/lib/neo4j/import \
    -v $HOME/neo4j/plugins:/plugins \
    --env NEO4J_AUTH=neo4j/fpas_password \
    neo4j:5.15
```

### **Step 2: Verify Container**
```bash
# Check if running
docker ps | grep neo4j-fpas

# View logs
docker logs neo4j-fpas
```

### **Step 3: Configure Environment**
```bash
# Neo4j Docker Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=fpas_password
NEO4J_DATABASE=neo4j
```

### **Docker Management Commands**
```bash
# Start container
docker start neo4j-fpas

# Stop container
docker stop neo4j-fpas

# Remove container (keeps data)
docker rm neo4j-fpas

# Remove container and data
docker rm neo4j-fpas
rm -rf $HOME/neo4j
```

---

## ☁️ **Option 3: Neo4j AuraDB (Production)**

### **Step 1: Sign Up for Neo4j Aura**
1. Go to [neo4j.com/cloud/aura](https://neo4j.com/cloud/aura/)
2. Click "Start Free"
3. Create account with email
4. Verify email address

### **Step 2: Create Free Instance**
1. Click "Create Instance"
2. Choose "AuraDB Free"
3. Instance name: "fpas-production"
4. Region: Choose closest to your location
5. Click "Create Instance"

### **Step 3: Get Connection Details**
1. Wait for instance to be ready (~2-3 minutes)
2. Click "Connect" button
3. Copy connection details:
   - **URI**: `neo4j+s://xxxxx.databases.neo4j.io`
   - **Username**: `neo4j`
   - **Password**: Generated password (save this!)

### **Step 4: Configure Environment**
```bash
# Neo4j AuraDB Configuration
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=generated_password_from_aura
NEO4J_DATABASE=neo4j
```

### **AuraDB Free Tier Limits**
- **Nodes**: 200,000
- **Relationships**: 400,000
- **Storage**: 1GB
- **Memory**: 8GB
- **Perfect for FPAS development and testing**

---

## 🧪 **Testing Your Setup**

### **Step 1: Install Python Dependencies**
```bash
cd /path/to/fpas
pip install neo4j python-dotenv
```

### **Step 2: Test Connection**
```python
# test_neo4j_connection.py
import asyncio
from database import health_check

async def test_connection():
    try:
        status = await health_check()
        print(f"✅ Neo4j Connection: {status['status']}")
        print(f"📊 Performance: {status.get('performance_metrics', {})}")
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_connection())
```

### **Step 3: Run Test**
```bash
python test_neo4j_connection.py
```

### **Expected Output**
```
✅ Neo4j Connection: healthy
📊 Performance: {'total_queries': 1, 'successful_queries': 1, 'avg_query_time': 0.045}
```

---

## 🚀 **Initialize FPAS Schema**

### **Step 1: Run Schema Setup**
```bash
cd /path/to/fpas
python -c "
import asyncio
from database import setup_neo4j_schema

async def setup():
    result = await setup_neo4j_schema()
    print(f'Schema setup: {result}')

asyncio.run(setup())
"
```

### **Step 2: Verify Schema**
```bash
python -c "
import asyncio
from database import verify_neo4j_schema

async def verify():
    result = await verify_neo4j_schema()
    print(f'Constraints: {len(result[\"constraints\"])}')
    print(f'Indexes: {len(result[\"indexes\"])}')

asyncio.run(verify())
"
```

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Connection Refused**
```
neo4j.exceptions.ServiceUnavailable: Could not connect to bolt://localhost:7687
```
**Solution**: 
- Ensure Neo4j is running
- Check if port 7687 is available
- Verify credentials in `.env`

#### **Authentication Failed**
```
neo4j.exceptions.AuthError: The client is unauthorized due to authentication failure.
```
**Solution**:
- Check username/password in `.env`
- For local: default is `neo4j/neo4j`, then change on first login
- For Docker: use the password you set in `NEO4J_AUTH`

#### **Database Not Found**
```
neo4j.exceptions.DatabaseError: Unable to get a routing table for database 'fpas'
```
**Solution**:
- Use `NEO4J_DATABASE=neo4j` (default database)
- Or create custom database in Neo4j Desktop

### **Performance Tips**
- **Local**: Allocate more memory in Neo4j Desktop settings
- **Docker**: Increase container memory with `--memory=4g`
- **AuraDB**: Free tier has fixed resources

---

## 📊 **Recommended Setup by Use Case**

### **Development & Testing**
- **Best Choice**: Local Neo4j Desktop
- **Alternative**: Docker
- **Pros**: Full control, no internet required, easy debugging
- **Cons**: Manual setup required

### **Production Deployment**
- **Best Choice**: Neo4j AuraDB
- **Alternative**: Self-hosted Neo4j cluster
- **Pros**: Managed service, automatic backups, scaling
- **Cons**: Requires signup, internet dependency

### **CI/CD & Automated Testing**
- **Best Choice**: Docker
- **Alternative**: Neo4j test containers
- **Pros**: Reproducible, easy cleanup, fast setup
- **Cons**: Requires Docker knowledge

---

## 🎯 **Next Steps After Setup**

1. **✅ Test connection** with health check
2. **✅ Initialize schema** with setup script  
3. **✅ Run data ingestion** with collector bridge
4. **✅ Test analytics queries** with Neo4j integration
5. **✅ Connect to FastAPI backend**
6. **✅ Integrate with Streamlit frontend**

---

**Choose the option that best fits your development workflow. For most developers, I recommend starting with Local Neo4j Desktop for development and upgrading to AuraDB for production deployment.**
