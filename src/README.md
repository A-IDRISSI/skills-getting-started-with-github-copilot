# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- See signed-up participants in each activity card, updated after signup
- Sign up for activities
- Unregister a participant using the delete icon next to their email

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## Backend Tests

From the repository root, install the dependencies in your virtual environment:

```bash
python3 -m pip install -r requirements.txt
```

Run the backend tests with pytest:

```bash
python3 -m pytest tests/test_app.py -v
```

These tests use FastAPI's TestClient in-process, so no running server or browser
is needed. Fixtures restore the in-memory activity data after each test.
Structure new backend tests using explicit **Arrange**, **Act**, and **Assert**
blocks: prepare inputs and expected state, make requests, then check responses
and state changes.

To also run the existing browser integration test:

```bash
python3 -m pytest tests -v
```

The browser test is skipped when Google Chrome is unavailable.

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a participant from an activity                        |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
