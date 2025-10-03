# Finnish Politician Analysis System (FPAS)

A comprehensive system for analyzing Finnish politicians, their relationships, and news coverage using advanced AI techniques and graph database technology.

![FPAS Dashboard](docs/images/fpas-dashboard.png)

## 🚀 Features

- **Interactive Map**: Visualize Finnish provinces with politician distribution
- **Politician Profiles**: Detailed information about Finnish politicians
- **News Analysis**: Real-time news collection and analysis from major Finnish sources
- **AI-Powered Insights**: Advanced analysis using LangChain multi-agent system
- **Graph Database**: Neo4j-powered relationship mapping and querying

## 📋 System Components

- **Data Collection**: Collects data from official Finnish sources and news outlets
- **AI Pipeline**: Processes and analyzes data using LangChain agents
- **API**: FastAPI backend providing structured data access
- **Frontend**: Streamlit dashboard with interactive visualizations
- **Database**: Neo4j graph database storing politicians, news, and relationships

## 🛠️ Installation & Setup

### Required Environment Variables

Before running the system, you need to set up the following environment variables:

```
NEO4J_URI=bolt://localhost:7687 (or bolt://neo4j:7687 for Docker)
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password
NEO4J_DATABASE=neo4j
OPENAI_API_KEY=your_openai_api_key
```

You can copy the example file and modify it:

```bash
cp .env.example .env
```

## 🖥️ Running Locally

### Prerequisites

- Python 3.9+ installed
- Neo4j database (local installation or remote access)
- OpenAI API key

### Setup Steps

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/fpas.git
cd fpas
```

2. **Create and activate a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

Create a `.env` file in the project root with the necessary environment variables (see above).

5. **Start the Neo4j database** (if running locally)

Follow the [Neo4j installation instructions](https://neo4j.com/docs/operations-manual/current/installation/) for your platform.

6. **Initialize the database**

```bash
python scripts/init_database.py
```

7. **Start the API server**

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

8. **Start the frontend**

Open a new terminal, activate the virtual environment, and run:

```bash
streamlit run frontend/app.py
```

9. **Access the system**

- Frontend Dashboard: http://localhost:8501
- API Documentation: http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474 (if running locally)

## 🐳 Running with Docker

### Prerequisites

- [Docker](https://www.docker.com/get-started) and Docker Compose installed
- Git installed
- OpenAI API key (for AI analysis features)

### Quick Start (Single Command)

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/fpas.git
cd fpas
```

2. **Set up environment variables**

```bash
cp .env.example .env
```

Edit the `.env` file and update at minimum these required variables:

```
NEO4J_PASSWORD=your_secure_password
NEO4J_AUTH=neo4j/your_secure_password
OPENAI_API_KEY=your_openai_api_key
```

3. **Start the entire system with a single command**

This command will start all services and initialize the database:

```bash
docker-compose up -d && docker-compose logs -f welcome
```

```
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║  🚀 Finnish Politician Analysis System (FPAS) is now running!         ║
║                                                                       ║
║  📊 Frontend Dashboard: http://localhost:8501                         ║
║  🔍 API Documentation:  http://localhost:8000/docs                    ║
║  🗄️ Neo4j Browser:      http://localhost:7474                         ║
║                                                                       ║
║  Login credentials for Neo4j:                                         ║
║  Username: neo4j                                                      ║
║  Password: 12345678 (or your custom password)                         ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

4. **Access the system**

Simply click on the links displayed in your terminal:

- Frontend Dashboard: http://localhost:8501
- API Documentation: http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474 (username: neo4j, password: your_secure_password)

### Alternative: Step-by-Step Startup

If you prefer to start the system step by step:

1. **Start the containers**

#For safely start first stop the docker if any 

# Stop all containers
```bash
docker-compose down
```

# Start the docker
```bash
docker-compose up -d
```

2. **Initialize the database** (first time only)

```bash
docker-compose exec scripts python /app/init_database.py
```

### Container Architecture

The system consists of the following Docker containers:

- **neo4j**: Graph database storing all politician and news data
- **api**: FastAPI backend providing data access endpoints
- **ai_pipeline**: LangChain-based AI analysis system
- **data_collection**: Data collection services for Finnish political data
- **frontend**: Streamlit dashboard for visualization and interaction
- **scripts**: Utility container for database initialization and maintenance

## 🔧 Troubleshooting

### Common Issues

1. **Neo4j connection issues**
   - Ensure Neo4j container is healthy: `docker-compose ps`
   - Check Neo4j logs: `docker-compose logs neo4j`
   - Verify credentials in `.env` file match what's used in the containers

2. **Frontend can't connect to API**
   - Ensure API container is running: `docker-compose ps api`
   - Check API logs: `docker-compose logs api`
   - Verify API_BASE_URL is set correctly in the frontend container

3. **Missing politician data**
   - Run the initialization script: `docker-compose exec scripts python /app/init_province_data.py`
   - Check data collection logs: `docker-compose logs data_collection`

4. **OpenAI API errors**
   - Verify your OpenAI API key is valid and has sufficient credits
   - Check AI pipeline logs: `docker-compose logs ai_pipeline`

### Rebuilding Containers

If you need to rebuild containers after code changes:

```bash
docker-compose build [service_name]
docker-compose up -d [service_name]
```

For example, to rebuild just the frontend:

```bash
docker-compose build frontend
docker-compose up -d frontend
```

## 📊 Data Sources

- **Eduskunta API**: Official Finnish Parliament data
- **Statistics Finland**: Population and administrative data
- **News Sources**: YLE, Helsingin Sanomat, Iltalehti, MTV Uutiset, Kauppalehti

## 🛠️ Development

### Project Structure

```
fpas/
├── ai_pipeline/        # AI analysis components
├── api/                # FastAPI backend
├── data_collection/    # Data collection services
├── database/           # Database scripts and models
├── docs/               # Documentation
├── frontend/           # Streamlit dashboard
├── scripts/            # Utility scripts
├── .env.example        # Example environment variables
├── docker-compose.yml  # Docker Compose configuration
└── README.md           # This file
```

### Local Development

For local development without Docker:

1. Set up a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Run the API:
```bash
uvicorn api.main:app --reload
```

3. Run the frontend:
```bash
streamlit run frontend/app.py
```

## 📄 License

This project is licensed under the [Creative Commons Attribution 4.0 International License (CC BY 4.0)](LICENSE).

When using or referencing this work, please cite as follows:
```
"Finnish Politician Analysis System (FPAS)" by Md Sadidur Rahman, GPT-Lab, Tampere University.
```

## 🎓 Academic Context

This project was developed as part of a Master's thesis at the Tampere University, under the supervision of [José Cerqueira](https://www.linkedin.com/in/jascerqueira/).

### About GPT-Lab

GPT-Lab is a collective of dreamers, thinkers, and innovators united by a common purpose: to revolutionize how the world communicates with AI. We are dedicated to exploring the limitless potential of Generative AI and large language models. Our goal is to create experiences that are both enlightening and enriching–pushing the boundaries of what is possible.

At GPT-Lab, our work blends empirical research with real-world application to develop practical, AI-driven solutions that address complex societal and industrial challenges. As a growing research group rooted in multidisciplinary collaboration, we explore intersections with ethics, quantum computing, scientific discovery, and startup innovation.

GPT-Lab was founded by [Professor Pekka Abrahamsson](https://www.linkedin.com/in/profabrahamsson/) at the Tampere University.

## 🔬 Open Science Framework

This project follows Open Science Framework best practices to ensure the work is:

- **Reproducible**: All code, data sources, and methodologies are documented
- **Replicable**: Clear instructions are provided for setting up and running the system
- **Transparent**: All components and data sources are clearly described
- **Accessible**: Licensed under CC BY 4.0 to allow academic and research use

## 🙏 Acknowledgements

- Finnish Parliament (Eduskunta) for providing open data
- Statistics Finland for demographic data
- OpenAI for AI capabilities
- Neo4j for graph database technology
- GPT-Lab and Tampere University for academic support
