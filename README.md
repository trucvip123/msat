# MSAT Manager

A full-stack application with a backend service and MySQL database.

## Prerequisites

- Docker
- Docker Compose
- Git

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Backend Configuration
BACKEND_PORT=8000
DATABASE_URL=mysql://user:password@db:3306/database_name
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=development

# MySQL Configuration
MYSQL_DATABASE=your_database_name
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_ROOT_PASSWORD=your_root_password
MYSQL_PORT=3306
```

## Project Structure

```
.
├── backend/           # Backend application code
├── mysql-init/       # MySQL initialization scripts
├── mysql/           # MySQL configuration files
├── docker-compose.yml
└── .env             # Environment variables (create this file)
```

## Getting Started

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd msat_manager
   ```

2. Create and configure the `.env` file as shown above.

3. Start the services:
   ```bash
   docker-compose up -d
   ```

4. The application will be available at:
   - Backend API: http://localhost:8000
   - MySQL Database: localhost:3306

## API Documentation

### Authentication

#### Register
Create a new user account and receive an access token.

**Endpoint:** `POST /auth/register`

**Request Body:**
```json
{
    "username": "your_username",
    "email": "your.email@example.com",
    "password": "your_password"
}
```

**Response:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
}
```

**Error Responses:**
```json
{
    "detail": "Username already registered"
}
```
or
```json
{
    "detail": "Password must be at least 8 characters long and contain uppercase, lowercase, and numbers"
}
```

#### Login
Authenticate a user and receive an access token.

**Endpoint:** `POST /auth/login`

**Request Body:**
```json
{
    "username": "your_username",
    "password": "your_password"
}
```

**Response:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
}
```

**Error Response:**
```json
{
    "detail": "Invalid credentials"
}
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number

## Services

### Backend Service
- Built from the Dockerfile in the `backend` directory
- Exposes port 8000 (configurable via BACKEND_PORT)
- Connected to MySQL database
- Hot-reload enabled for development

### MySQL Database
- MySQL 8.0
- Persistent data storage
- Custom configuration through `mysql/my.cnf`
- Initialization scripts in `mysql-init/`

## Development

The backend service is configured with a volume mount, allowing for live code changes during development. Any changes made to the backend code will be reflected immediately.

## Database Management

The MySQL database is configured with:
- Persistent volume storage
- Health checks
- Custom configuration
- Initialization scripts

## Stopping the Services

To stop all services:
```bash
docker-compose down
```

To stop and remove all data (including the database volume):
```bash
docker-compose down -v
```

## Network

The services are connected through a custom bridge network named `msat-network`.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

[Add your license information here] 