# nd-aiaplatform-be

A FastAPI-based backend service for the AI Travel Agent Platform.

## Project Structure

```
.
├── app/                    # Main application package
│   ├── __init__.py
│   ├── main.py            # FastAPI application instance and main configurations
│   ├── api/               # API route definitions
│   │   ├── __init__.py
│   │   └── v1/           # API version 1
│   │       ├── __init__.py
│   │       └── endpoints/ # Route handlers for different features
│   ├── core/             # Core application components
│   │   ├── __init__.py
│   │   ├── config.py     # Configuration settings
│   │   └── database.py   # Database connection and session management
│   ├── models/           # Database models and Pydantic schemas
│   │   ├── __init__.py
│   │   ├── database.py   # SQLAlchemy models
│   │   └── schemas.py    # Pydantic models for request/response validation
│   └── services/         # Business logic and service layer
│       └── __init__.py
├── tests/                # Test suite
│   ├── __init__.py
│   ├── conftest.py      # Test configurations and fixtures
│   └── api/             # API tests
│       └── v1/
│           └── endpoints/
├── alembic/             # Database migration scripts
│   ├── versions/        # Migration version files
│   └── env.py          # Migration environment configuration
├── requirements.txt     # Production dependencies
├── requirements-test.txt # Test dependencies
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Development Docker Compose configuration
├── docker-compose.prod.yml # Production Docker Compose configuration
└── README.md           # Project documentation
```

## Development Setup

### Prerequisites
- Python 3.11 or higher
- PostgreSQL (for development and production)
- Docker and Docker Compose (optional, for containerized development)

### Local Development Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-test.txt  # For development and testing
```

3. Create environment files:
   - Create `.env.dev` for development
   - Create `.env.prod` for production
   - Create `.env.test` for testing. Testing env do not need to have any DB info as in-momory sqllite is used for testing.
   - Example `.env.dev`:
   ```env
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_NAME=your_db_name
   DB_PORT=5432
   DB_HOST=localhost
   DB_SCHEMA=aiaplatform
   ```

4. Run the development server:
Do following before running the API server.
a) Ensure that Postgres DB is running
b) Migration script is executed (refer to the how to run migration section)
c) right env file is used (.env.dev or .env.prod, use appropiate docker command)

```bash
docker compose up api
```

## Docker Setup

### Development Environment
1. Build and run using Docker Compose:
```bash
docker compose up --build
```

### Production Environment
1. Build and run using production Docker Compose:
```bash
docker compose -f docker-compose.prod.yml up --build
```

## Database Configuration

The application uses two different databases:

1. **PostgreSQL** (Production/Development):
   - Main database for the API
   - Configured through environment variables
   - Uses schema-based isolation
   - Connection pooling with health checks
   - Connection recycling after 1 hour

2. **SQLite** (Testing):
   - In-memory database for testing
   - Automatically configured in test environment
   - No schema support (schema is stripped for testing)
   - Each test gets a fresh database instance

## Database Migrations

### Using Docker (Recommended)

1. **Development Environment**:
```bash
# Run migrations and remove the container after completion
docker compose up migration --remove-orphans

# Or if you want to keep the container for debugging
docker compose up migration
```

2. **Production Environment**:
```bash
# Run migrations and remove the container after completion
docker compose -f docker-compose.prod.yml up migration --remove-orphans
```

3. **Cleanup Orphaned Containers**:
If you see a message about orphaned containers, you can clean them up with:
```bash
# Remove orphaned containers
docker compose down --remove-orphans

# Or when running migrations
docker compose up migration --remove-orphans
```

Note: The migration service is designed to run once and exit. Using `--remove-orphans` flag ensures that the container is removed after the migration is complete.

### Manual Migration (Alternative)

These commands are useful for:
- Development without Docker
- Debugging migration issues
- CI/CD pipelines
- Manual database management

#### Prerequisites Installation

1. **Install PostgreSQL Client Tools**:
   - On macOS:
   ```bash
   brew install postgresql
   ```
   - On Ubuntu/Debian:
   ```bash
   sudo apt-get install postgresql-client
   ```
   - On Windows:
   - Install PostgreSQL from https://www.postgresql.org/download/windows/
   - Add PostgreSQL bin directory to PATH

2. **Install Alembic**:
```bash
pip install alembic
```

#### Migration Commands

1. **First-time Setup**:

Using Docker (Recommended):
```bash
# Create database using PostgreSQL container
docker compose exec db createdb your_db_name

# Run migrations using API container
docker compose exec api alembic upgrade head
```

Using Local Installation:
```bash
# Create database (if not using Docker)
createdb your_db_name

# Run migrations manually
alembic upgrade head
```

2. **Managing Migrations**:

Using Docker:
```bash
# Create new migration
docker compose exec api alembic revision --autogenerate -m "description of changes"

# Apply migrations
docker compose exec api alembic upgrade head

# Downgrade migrations
docker compose exec api alembic downgrade -1  # Go back one migration
# or
docker compose exec api alembic downgrade <revision_id>  # Go to specific revision

# View migration history
docker compose exec api alembic history
```

Using Local Installation:
```bash
# Create new migration
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head

# Downgrade migrations
alembic downgrade -1  # Go back one migration
# or
alembic downgrade <revision_id>  # Go to specific revision

# View migration history
alembic history
```

### Important Notes
- Always review auto-generated migrations before applying
- Never modify existing migration files
- Create new migrations for schema changes
- Test migrations in development before applying to production
- For containerized environments, prefer using `docker compose up migration`
- Manual commands are mainly for development and debugging purposes
- When using Docker commands, ensure containers are running before executing migration commands

## Testing

### Running Tests

1. Run all tests:
```bash
pytest
```

2. Run tests with verbose output:
```bash
pytest -v
```

3. Run tests with coverage report:
```bash
pytest --cov=app tests/
```

4. Run specific test file:
```bash
pytest tests/api/v1/endpoints/test_agents.py
```

### Test Structure
- `tests/`: Root test directory
  - `conftest.py`: Contains shared pytest fixtures
  - `api/`: API tests
    - `v1/`: Version 1 API tests
      - `endpoints/`: Tests for specific endpoints

### Writing Tests
1. Test files should be named `test_*.py`
2. Test functions should be named `test_*`
3. Use fixtures from `conftest.py` for common setup
4. Follow the Arrange-Act-Assert pattern
5. Test both success and error cases

## API Documentation

Once the server is running, you can access:
- Swagger UI documentation: http://localhost:8000/docs
- ReDoc documentation: http://localhost:8000/redoc
- Health check endpoint: http://localhost:8000/health

## Docker Registry Management

### GitHub Container Registry (ghcr.io)

1. Login to GitHub Container Registry:
```bash
echo $GHCR_TOKEN | docker login ghcr.io -u azman-nd --password-stdin
```

2. Tag local image:
```bash
docker tag <ImageID> ghcr.io/azman-nd/nd-aiaplatform-be-api:latest
```

3. Push to registry:
```bash
docker push ghcr.io/azman-nd/nd-aiaplatform-be-api:latest
```

4. Pull from registry:
```bash
docker pull ghcr.io/azman-nd/nd-aiaplatform-be-api:latest
```

## Development Guidelines

1. All new endpoints should be added in the appropriate module under `app/api/v1/endpoints/`
2. Use Pydantic models for request/response validation
3. Keep business logic in the services layer
4. Update requirements.txt when adding new dependencies
5. Write tests for new features
6. Follow PEP 8 style guide
7. Use type hints for better code maintainability

## Troubleshooting

### Common Issues

1. Database Connection Issues:
   - Verify PostgreSQL is running
   - Check environment variables
   - Ensure database exists
   - Check network connectivity

2. Migration Issues:
   - Ensure database exists
   - Check migration history
   - Verify schema exists
   - Check user permissions

3. Docker Issues:
   - Check Docker daemon is running
   - Verify network configuration
   - Check container logs
   - Ensure ports are available

