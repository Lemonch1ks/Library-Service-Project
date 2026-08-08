# Library Service API

A REST API for managing a library's books, users, and book borrowings. The
project is built with Django REST Framework and uses JWT authentication. It is
intended to replace manual tracking of book inventory and borrowing records.

The current implementation covers the selected FLEX tasks for the Books,
Users, Borrowings, and Telegram notification services. Stripe payments and
scheduled overdue checks are not implemented.

## Features

- Book inventory management with create, read, update, and delete operations
- Email-based user registration and authentication
- JWT access and refresh tokens
- Custom `Authorize` request header for JWT authentication
- Borrowing creation with automatic inventory decrement
- Borrowing return with automatic inventory increment
- Borrowing date validation
- Active and returned borrowing filters
- User-specific borrowing access with staff-level access to all records
- Telegram notifications when a new borrowing is created
- Environment-based storage for Telegram credentials
- OpenAPI schema, Swagger UI, and ReDoc documentation
- Automated tests for the Books, Users, and Borrowings services
- Test coverage reporting with `coverage`

## Technology Stack

- Python 3.12
- Django 5.2
- Django REST Framework
- Simple JWT
- drf-spectacular
- python-dotenv
- Telegram Bot API
- coverage
- SQLite
- Docker and Docker Compose

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Lemonch1ks/Library-Service-Project.git
cd Library-Service-Project

```

### 2. Create and activate a virtual environment

Linux and macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Telegram notifications

Copy the environment variable template:

Linux and macOS:

```bash
cp .env.sample .env
```

Windows PowerShell:

```powershell
Copy-Item .env.sample .env
```

Set the credentials in `.env`:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

The `.env` file is ignored by Git and must never be committed. If Telegram
credentials are not configured, borrowings can still be created, but the
notification is skipped and a warning is written to the application log.

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Create an administrator account

```bash
python manage.py createsuperuser
```

### 7. Start the development server

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`.

## Running with Docker

Create `.env` from the provided template and replace its placeholder values.
Then build and start the application:

```bash
docker compose up --build
```

Docker Compose applies migrations automatically and starts the API at
`http://127.0.0.1:8000/`. The SQLite database is stored in the named
`sqlite_data` volume, so it is preserved when the application container is
recreated.

Stop the application with:

```bash
docker compose down
```

## Authentication

The project uses JWT authentication with email and password. Register a user,
obtain an access token, and send it in the custom `Authorize` header.

### Register a user

```http
POST /users/
Content-Type: application/json
```

```json
{
  "email": "reader@example.com",
  "first_name": "Alex",
  "last_name": "Reader",
  "password": "strong-password"
}
```

### Obtain JWT tokens

```http
POST /users/token/
Content-Type: application/json
```

```json
{
  "email": "reader@example.com",
  "password": "strong-password"
}
```

The response contains `access` and `refresh` tokens.

### Authenticate a request

Use `Authorize`, not the standard `Authorization` header:

```http
Authorize: Bearer <access-token>
```

Example with curl:

```bash
curl http://127.0.0.1:8000/borrowings/ \
  -H "Authorize: Bearer YOUR_ACCESS_TOKEN"
```

### Refresh an access token

```http
POST /users/token/refresh/
Content-Type: application/json
```

```json
{
  "refresh": "your-refresh-token"
}
```

## API Endpoints

### Books Service

| Method | Endpoint | Description | Access |
| --- | --- | --- | --- |
| `GET` | `/books/` | List all books | Public |
| `POST` | `/books/` | Create a book | Staff only |
| `GET` | `/books/{id}/` | Retrieve a book | Public |
| `PUT` | `/books/{id}/` | Replace a book | Staff only |
| `PATCH` | `/books/{id}/` | Partially update a book | Staff only |
| `DELETE` | `/books/{id}/` | Delete a book | Staff only |

Book creation example:

```json
{
  "title": "Clean Code",
  "author": "Robert C. Martin",
  "cover": "hard",
  "inventory": 5,
  "daily_fee": "2.50"
}
```

The supported `cover` values are `hard` and `soft`. Inventory and daily fee
cannot be negative.

### Users Service

| Method | Endpoint | Description | Access |
| --- | --- | --- | --- |
| `POST` | `/users/` | Register a user | Public |
| `POST` | `/users/token/` | Obtain JWT tokens | Public |
| `POST` | `/users/token/refresh/` | Refresh an access token | Public |
| `GET` | `/users/me/` | Retrieve the current profile | Authenticated |
| `PUT` | `/users/me/` | Replace the current profile | Authenticated |
| `PATCH` | `/users/me/` | Partially update the current profile | Authenticated |

### Borrowings Service

| Method | Endpoint | Description | Access |
| --- | --- | --- | --- |
| `GET` | `/borrowings/` | List borrowings | Authenticated |
| `POST` | `/borrowings/` | Create a borrowing | Authenticated |
| `GET` | `/borrowings/{id}/` | Retrieve a borrowing | Owner or staff |
| `POST` | `/borrowings/{id}/return/` | Return a borrowed book | Owner or staff |

Non-staff users can access only their own borrowings. Staff users can access
all borrowings.

#### Create a borrowing

```http
POST /borrowings/
Authorize: Bearer <access-token>
Content-Type: application/json
```

```json
{
  "borrow_date": "2026-08-08",
  "expected_return_date": "2026-08-15",
  "book": 1
}
```

The authenticated user is attached automatically. The selected book must have
available inventory. After successful creation, its inventory is decreased by
one. If `borrow_date` is omitted, it defaults to the current date. A borrow date
in the past is rejected, and `expected_return_date` must be later than
`borrow_date`.

After the database transaction is committed, the service attempts to send a
Telegram message containing the user email, book title, borrow date, and
expected return date. A Telegram API failure does not roll back the borrowing.

#### Filter borrowings

List active borrowings:

```http
GET /borrowings/?is_active=true
```

List returned borrowings:

```http
GET /borrowings/?is_active=false
```

Staff users can filter borrowings by user ID:

```http
GET /borrowings/?user_id=3
```

Filters can be combined:

```http
GET /borrowings/?user_id=3&is_active=true
```

`is_active=true` means that `actual_return_date` is empty. Non-staff users
remain restricted to their own records even if they provide `user_id`.

#### Return a borrowing

```http
POST /borrowings/1/return/
Authorize: Bearer <access-token>
```

No request body is required. The endpoint sets `actual_return_date` to the
current date and increases the book inventory by one. A borrowing cannot be
returned twice.

## API Documentation

After starting the server, the documentation is available at:

- Swagger UI: `http://127.0.0.1:8000/api/schema/swagger-ui/`
- ReDoc: `http://127.0.0.1:8000/api/schema/redoc/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`

For authenticated requests, remember that this project expects the custom
`Authorize` header.

## Running Tests

Run the Django test suite:

```bash
python manage.py test
```

To measure test coverage, install `coverage` and run:

```bash
pip install coverage
coverage run --source=books_service,users_service,borrowing_service,permissions \
  manage.py test
coverage report
```

## Project Structure

```text
Library-Service-Project/
- books_service/       # Book model, serializer, views, and routes
- borrowing_service/   # Borrowing logic, filters, returns, and tests
- borrowing_service/telegram.py  # Telegram notification helper
- users_service/       # Custom user model, registration, and profile API
- permissions/         # Shared REST framework permissions
- library_conf/        # Django settings and root URL configuration
- Dockerfile
- docker-compose.yml
- manage.py
- requirements.txt
- README.md
```

## Implemented FLEX Coding Tasks

The project currently implements the following selected tasks:

1. Books Service CRUD
2. Books Service permissions
3. Users Service CRUD and JWT authentication
4. Borrowing list and detail endpoints
5. Borrowing creation with inventory management
6. Borrowing filtering and user access restrictions
7. Borrowing return functionality
8. Telegram notification on borrowing creation

## Planned Functionality

The full Library Service specification also includes functionality that is not
part of the current implementation:

- Stripe payments and overdue fines
- Scheduled overdue borrowing checks
