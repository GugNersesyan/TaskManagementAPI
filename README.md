# Task Management API

A FastAPI-based REST API for managing tasks with authentication, caching, and real-time WebSocket support.

## Features

- **User Authentication**: JWT-based auth with access/refresh tokens
- **Task Management**: CRUD operations for tasks
- **Role-based Access Control**: Admin and regular user roles
- **Caching**: Redis integration for task caching
- **WebSocket**: Real-time task updates
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic database migrations

## Tech Stack

- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- Redis
- JWT (python-jose)
- Pydantic v2
- pytest

## Project Structure

```
app/
├── api/              # API routes
├── core/             # Security, cache, connection manager
├── db/              # Database config, sessions
├── models/          # SQLAlchemy models
├── schemas/         # Pydantic schemas
├── services/        # Business logic
├── tests/           # Test suite
└── main.py          # App entry point
```

## Setup

1. Install dependencies:
```bash
uv pip install -e ".[test]"
```

2. Configure environment variables in `.env`:
```env
DATABASE_URL=postgresql://user:pass@localhost/taskdb
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
REDIS_URL=redis://localhost:6379
```

3. Run migrations:
```bash
alembic upgrade head
```

4. Start the server:
```bash
uvicorn app.main:app --reload
```

## Testing

Run all tests:
```bash
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_api_auth.py -v
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login (get tokens)
- `POST /auth/refresh` - Refresh access token

### Tasks
- `POST /api/tasks/` - Create task
- `GET /api/tasks/` - List tasks
- `GET /api/tasks/{id}` - Get task
- `PUT /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task

### Users
- `GET /api/users/me` - Get current user
- `GET /api/users/` - List users (admin only)

### WebSocket
- `WS /api/tasks/ws/tasks?token=<access_token>` - Real-time updates

## Test Coverage

- Unit tests (security, services)
- Integration tests (API endpoints)
- Authentication flow tests
- WebSocket connection tests

Total: 103 tests

## License

MIT
