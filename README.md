# Finnish Politician Analysis System (FPAS)

An enterprise-grade system for analyzing Finnish politicians using AI-powered sentiment analysis, topic modeling, and influence tracking.

## 🚀 Features

- **Real-time Analysis**: Monitor political discourse in real-time
- **Comprehensive Data**: Aggregated from multiple official Finnish sources
- **Advanced AI**: Powered by LangChain for sophisticated analysis
- **Interactive Dashboard**: Streamlit-based frontend with rich visualizations
- **Scalable Architecture**: Microservices-based design for enterprise use

## 🏗️ Project Structure

```
fpas/
├── .github/           # GitHub Actions workflows
├── infrastructure/    # Infrastructure as Code
├── services/          # Microservices
├── databases/         # Database configurations
├── monitoring/        # Monitoring stack
├── tests/             # Test suites
├── docs/              # Documentation
└── scripts/           # Utility scripts
```

## 🛠️ Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and configure environment variables
3. Run `docker-compose up -d` to start all services

## 📚 Documentation

- [API Documentation](/docs/api/README.md)
- [Architecture Overview](/docs/architecture/overview.md)
- [Deployment Guide](/docs/deployment/README.md)
- [User Guide](/docs/user_guide/README.md)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
