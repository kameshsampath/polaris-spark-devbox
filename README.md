# Polaris Spark DevBox

[![Build Apache Polaris](https://github.com/kameshsampath/polaris-spark-devbox/actions/workflows/polaris.yml/badge.svg)](https://github.com/kameshsampath/polaris-spark-devbox/actions/workflows/polaris.yml)
[![Build Apache Spark with Jupyter Notebook](https://github.com/kameshsampath/polaris-spark-devbox/actions/workflows/pysparknotebook.yml/badge.svg)](https://github.com/kameshsampath/polaris-spark-devbox/actions/workflows/pysparknotebook.yml)

A development environment for experimenting with [Apache Polaris](https://github.com/apache/arrow-datafusion), [Apache Spark](https://spark.apache.org/), and [Apache Iceberg](https://iceberg.apache.org/) integration. This project provides a Docker-based setup for quick prototyping and learning.

> [!IMPORTANT]  
> This environment is intended for development and testing purposes only. Not suitable for production use.

## Overview

Polaris Spark DevBox offers a pre-configured environment that combines:

- [Apache Polaris](https://github.com/apache/arrow-datafusion) - A Rust-based query engine built on Apache Arrow DataFusion
- [Apache Spark](https://spark.apache.org/) (v3.5.4) - Unified analytics engine for large-scale data processing
- [Apache Iceberg](https://iceberg.apache.org/) - Open table format for huge analytic datasets

The environment includes:

- Polaris Server (Java 21)
- Apache Spark 3.5.4 with Hadoop 3
- Jupyter Notebook with PySpark integration
- Pre-configured networking and volume management
- Sample datasets and Iceberg table examples

## Core Features

- 🚀 Zero-configuration setup with Apache Polaris and Spark
- 📓 Integrated Jupyter environment with PySpark
- 🗂 Apache Iceberg table format support
- 🐳 Containerized development
- 🔄 Automated initialization
- 📚 Example notebooks demonstrating Polaris, Spark, and Iceberg integration
- 🛠️ Development utilities

## Prerequisites

> [!NOTE]
> Make sure you have all prerequisites installed before proceeding with the setup.

- Python 3.11+
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
  - Windows/macOS: Use Docker Desktop
  - Linux: Docker Desktop for Linux or Docker Engine with Docker Compose
- Sufficient disk space for containers and volumes

## Environment Configuration

> [!CAUTION]
> Keep your environment variables secure and never commit the `.env` file to version control.

Required variables in `.env`:

```ini
COMPOSE_PROJECT_NAME=polaris_spark_dev
POLARIS_CATALOG_NAME=my_catalog
POLARIS_DEFAULT_BASE_LOCATION=file:///data/polaris
POLARIS_PRINCIPAL_NAME=polarisuser
POLARIS_PRINCIPAL_ROLE_NAME=polarisuser_role
POLARIS_CATALOG_ROLE_NAME=my_catalog_role
POLARIS_API_HOST=localhost
POLARIS_API_PORT=8181
```

## Getting Started

> [!TIP]
> Ensure Docker is running before starting the containers.

1. Start the environment:
   ```bash
   docker-compose up -d
   ```

2. Verify container status:
   ```bash
   docker-compose ps
   ```

3. Setup Apache Polaris:
   ```bash
   ./setup
   ```

   > [!NOTE]
   > This will configure Polaris with 
   > - a catalog 
   > - a principal and principal role
   > - a catalog role 
   > - assign the catalog role to the principal role
   > - grant privileges
   > - generate a simple Jupyter Notebook verify the setup

## Access Points

> [!NOTE]
> All services are configured to run on localhost by default.

- Jupyter Notebook: [http://localhost:8888](http://localhost:8888)
- Polaris API: [http://localhost:10081](http://localhost:10081)
- Polaris Admin: [http://localhost:10082](http://localhost:10082)

## Integrations

### Apache Spark Integration
- Uses [Apache Spark 3.5.4](https://spark.apache.org/docs/3.5.4/)
- PySpark for Python interface
- Spark SQL for data querying
- Built-in Spark History Server

### Apache Iceberg Integration
- [Apache Iceberg](https://iceberg.apache.org/docs/latest/) table format support
- Schema evolution
- Time travel queries
- Partition evolution
- Hidden partitioning

### Apache Polaris Features
- REST Catalog
- SQL query support
- Distributed query execution
- Integration with Iceberg tables

## Project Structure

```
polaris-spark-devbox/
├── connection_config.py     # Configuration utility
├── requirements.txt        # Python dependencies
├── docker-compose.yml     # Container orchestration
├── conf/                  # Configuration files
├── templates/             # Template files
├── notebooks/            # Jupyter notebooks
└── http/                # HTTP test files
```

## Documentation

> [!NOTE]
> All examples and documentation are automatically generated during setup.

The setup generates two types of documentation:

1. **Jupyter Notebooks** (`notebooks/polaris_setup_verify.ipynb`)
   - Setup verification
   - API usage examples
   - Iceberg table operations
   - Spark SQL queries

2. **HTTP Files** (`http/polaris.http`)
   - REST API documentation
   - Testing endpoints

## Building Locally

> [!TIP]
> For the best experience, run all commands from the project root directory.

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd polaris-spark-devbox
   ```

2. Create Python virtual environment and install dependencies:

   > [!NOTE]
   > Create and activate a Python virtual environment to isolate project dependencies

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Unix/macOS
   # Or on Windows
   # .venv\Scripts\activate
   pip install -r requirements.txt
   ```

   > [!TIP]
   > If you use [direnv](https://direnv.net/), you can automate virtual environment activation by adding this to your `.envrc`:
   > ```bash
   > layout python python3.11
   > ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

## Dependencies

- [Docker SDK for Python](https://docker-py.readthedocs.io/)
- [Python-dotenv](https://github.com/theskumar/python-dotenv)
- [Requests](https://docs.python-requests.org/)
- [Jinja2](https://jinja.palletsprojects.com/)

## Related Resources

- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [Apache Iceberg Documentation](https://iceberg.apache.org/docs/latest/)
- [Apache Arrow DataFusion](https://arrow.apache.org/datafusion/)
- [PySpark Documentation](https://spark.apache.org/docs/latest/api/python/)

## Contributing

> [!TIP]
> Before submitting a PR, make sure to test your changes thoroughly.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.

## Support

For questions and support:
- Open an issue in the GitHub repository
- Connect on [LinkedIn](https://linkedin.com/in/kameshsampath)

---
Built with ❤️ by [Kamesh Sampath](https://github.com/kameshsampath)