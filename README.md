# Catalog Project
This web application was designed as a generic website for catalogs. The program demonstrates frontend and backend (including databases and api calls) skills.
Once set up on the users computer it can be used to store category and item information.

## Requirements
You need Docker and Docker Compose installed on your system to run this application. You can download them from:
- Docker: https://docs.docker.com/get-docker/
- Docker Compose: https://docs.docker.com/compose/install/

## Deployment
To run the program, execute the following from within the Catalog Project directory in the shell:

```bash
# Build and start the containers
docker-compose up --build

# To run in detached mode (in the background)
docker-compose up -d --build
```

The application will be available at http://localhost:8000

To stop the application:
```bash
docker-compose down
```

To stop the application and remove all data (including the database):
```bash
docker-compose down -v
```

## Development
The application uses:
- Python 3.9
- PostgreSQL 13
- Redis 6

The application code is mounted as a volume, so any changes to the code will be reflected immediately without rebuilding the container.

### Features
- Automatic health checks for database and Redis
- Wait-for-it script ensures database is ready before starting the application
- Non-root user for improved security
- Automatic container restart on failure
- Named volumes and networks for better management
- Development mode enabled by default

## Credit
Some of the code from gconnect() function was copied from notes I had taken in the Udacity classroom. Credit goes to the owner.

## License
This project is public domain.
