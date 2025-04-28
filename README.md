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

1. Build and run using Docker Compose:
```bash
docker-compose up --build
```

2. To run in detached mode:
```bash
docker-compose up -d
```

3. To stop the containers:
```bash
docker-compose down
```

The server will start and you can access:
- API documentation at http://localhost:8000/docs
- ReDoc documentation at http://localhost:8000/redoc
- Health check endpoint at http://localhost:8000/health
- Root endpoint at http://localhost:8000/

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

```

