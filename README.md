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
│   │   └── config.py     # Configuration settings
│   ├── models/           # Database models and Pydantic schemas
│   │   └── __init__.py
│   └── services/         # Business logic and service layer
│       └── __init__.py
├── requirements.txt       # Project dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
└── README.md             # Project documentation
```

## Setup and Installation

### Local Development Setup

1. Ensure you have Conda installed and create the environment:
```bash
conda activate aia-platform-be
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the development server:
```bash
uvicorn app.main:app --reload
```

### Docker Setup

1. Using the right docker compose yaml file.

For development env use `docker-compose.yaml` file. It (a) usees `env.dev` env file, (b) connects to same network that is created by DB docker and (c) uses DB Hostname as mentioned that is reachable from DB service. 


For production env use `docker-compose.prod.yaml` file. IT (a) uses `env.prod` env file, (b) creats its own network and (c) connects to DB server using a publicly reachable IP. 

2. Build and run using Docker Compose:
```bash
docker compose -f < filename > up --build
```

3. To run in detached mode:
```bash
docker compose -f < filename > up -d
```

4. To stop the containers:
```bash
docker compose down
```

The server will start and you can access:
- API documentation at http://localhost:8000/docs
- ReDoc documentation at http://localhost:8000/redoc
- Health check endpoint at http://localhost:8000/health
- Root endpoint at http://localhost:8000/

## Database Connection

### Database Configuration

The application uses PostgreSQL with the following features:
- Connection pooling with health checks
- Connection recycling after 1 hour
- Schema-based isolation
- Environment-specific host configuration:
  - Development: Uses Docker service name 'postgres'
  - Production: Uses actual database machine IP

The database connection is configured through individual environment variables:
```env
DB_USER=<your_db_user>
DB_PASSWORD=<your_db_password>
DB_NAME=<your_db_name>
DB_PORT=5432
DB_HOST=<your_db_host>
DB_SCHEMA=aiaplatform
```

The `DATABASE_URL` is automatically computed from these settings.

### Finding Database Docker IP Address

PostgreSQL docker is configured to accept remote connection. Therefore, in production env, update the `DB_HOST` in your environment file with the IP address of the machine where DB docker is running.

### Verifying Database Connection

You can verify the database connection and schema using the health check endpoint:
```bash
curl http://localhost:8000/health
```

The response will include:
- Connection status
- PostgreSQL version
- Current schema name

## API Documentation

Once the server is running, you can access:
- Swagger UI documentation: http://localhost:8000/docs
- ReDoc documentation: http://localhost:8000/redoc
- Health check endpoint: http://localhost:8000/health
- Root endpoint: http://localhost:8000/

## Project Components

- **api/**: Contains all the route definitions organized by version
- **core/**: Houses core functionality and configurations
- **models/**: Contains database models and Pydantic schemas for data validation
- **services/**: Implements business logic and external service integrations

## Development Guidelines

1. All new endpoints should be added in the appropriate module under `app/api/v1/endpoints/`
2. Use Pydantic models for request/response validation
3. Keep business logic in the services layer
4. Update requirements.txt when adding new dependencies

### Github Login and Docker push/pull:

1. Login to Github Container Registry service (ghcr.io)
```bash 
echo $GHCR_TOKEN| docker login ghcr.io -u azman-nd --password-stdin
```
2. Tag local image for ghcr.io
```bash
docker tag <ImageID> ghcr.io/azman-nd/nd-aiaplatform-be-api:latest
```
3. Push docker image to ghcr.io
```bash
docker push ghcr.io/azman-nd/nd-aiaplatform-be-api:latest
```
4. Pull docker image in EC2
```bash
docker pull ghcr.io/azman-nd/nd-aiaplatform-be-api:latest
```
5. Run docker in EC2
```bash
docker run -d -p 8000:8000 ghcr.io/azman-nd/nd-aiaplatform-be-api:latest
```

## Environment Setup

The application uses environment-specific configuration files. Create the following files in the `app` directory:

### Development Environment (.env.dev)
```env

# Database Configuration
DB_USER=<your_db_user>
DB_PASSWORD=<your_db_password>
DB_NAME=<your_db_name>
DB_PORT=5432
DB_HOST=postgres
DB_SCHEMA=aiaplatform

```

### Production Environment (.env.prod)
```env
# Database Configuration
DB_USER=<your_db_user>
DB_PASSWORD=<your_db_password>
DB_NAME=<your_db_name>
DB_PORT=5432
DB_HOST=<your-db-machine-ip>
DB_SCHEMA=aiaplatform
```

## Running the Application



### Development
```bash
# Default (uses .env.dev)
docker compose up

# Or explicitly specify environment
docker compose -f docker-compose.yaml up
```

### Production
```bash
docker compose -f docker-compose.prod.yaml up
```

## Database Configuration

The application uses PostgreSQL with the following features:
- Connection pooling with health checks
- Connection recycling after 1 hour
- Schema-based isolation
- Environment-specific host configuration:
  - Development: Uses Docker service name 'postgres'
  - Production: Uses actual database machine IP

## API Documentation

Once the application is running, you can access:
- API documentation at: http://localhost:8000/docs
- Alternative API documentation at: http://localhost:8000/redoc

## Health Check

The application provides a health check endpoint at `/health` that verifies:
- Database connectivity
- PostgreSQL version
- Current schema
- Basic database operations

