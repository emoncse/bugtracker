# 🐛 Bug Tracker API

A modern Django REST Framework application with real-time WebSocket support for bug tracking and project management.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Redis server
- Virtual environment

### Installation

1. **Clone and setup**
```bash
git clone <repository-url>
cd bugtracker
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements/common.txt
pip install -r requirements/development.txt
```

3. **Setup database**
```bash
python manage.py migrate
python manage.py createsuperuser
```

4. **Seed test data (optional)**
```bash
python manage.py seed_data
```

5. **Start Redis server**
```bash
redis-server
```

6. **Run the application**
```bash
# Development server (HTTP only)
python manage.py runserver

# Production server with WebSocket support
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

## 🔗 Access Points

- **API Documentation**: http://localhost:8000/api/docs/
- **Admin Interface**: http://localhost:8000/admin/
- **Landing Page**: http://localhost:8000/

## 🔐 Authentication

Use JWT tokens for API authentication:

```bash
# Get token
curl -X POST http://localhost:8000/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Use token
curl -H "Authorization: Bearer <your-token>" \
  http://localhost:8000/api/projects/
```

## 📡 WebSocket Testing

### Connect to WebSocket
```javascript
// General tracker WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/tracker/');

// Project-specific WebSocket
const projectWs = new WebSocket('ws://localhost:8000/ws/tracker/1/');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

### Test Messages
```javascript
// Send ping
ws.send(JSON.stringify({type: 'ping'}));

// Send typing indicator
ws.send(JSON.stringify({type: 'typing_start'}));
```

## 🏗️ Project Structure

```
bugtracker/
├── apps/tracker/           # Main application
│   ├── api/v1/            # API version 1
│   ├── services.py        # Business logic
│   └── models.py          # Database models
├── config/                # Django settings
├── requirements/          # Dependencies
├── deployments/          # Docker files
└── docs/                # Documentation
```

## 📋 API Endpoints

### Projects
- `GET /api/projects/` - List projects
- `POST /api/projects/` - Create project
- `GET /api/projects/{id}/` - Get project details
- `PUT /api/projects/{id}/` - Update project
- `DELETE /api/projects/{id}/` - Delete project

### Bugs
- `GET /api/bugs/` - List bugs
- `POST /api/bugs/` - Create bug
- `GET /api/bugs/{id}/` - Get bug details
- `PUT /api/bugs/{id}/` - Update bug
- `DELETE /api/bugs/{id}/` - Delete bug
- `GET /api/bugs/assigned_to_me/` - Bugs assigned to user
- `GET /api/bugs/created_by_me/` - Bugs created by user

### Comments
- `GET /api/comments/` - List comments
- `POST /api/comments/` - Create comment
- `GET /api/comments/{id}/` - Get comment details
- `PUT /api/comments/{id}/` - Update comment
- `DELETE /api/comments/{id}/` - Delete comment

### Activities
- `GET /api/activities/` - List activity logs

## 🔧 Development

### Running Tests
```bash
python manage.py test
```

### Code Quality
```bash
# Format code
black apps/ config/

# Check imports
isort apps/ config/

# Lint code
flake8 apps/ config/
```

### Database Management
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database
python manage.py flush
```

## 🐳 Docker Deployment

### Using Docker Compose
```bash
# Build and start services
docker-compose -f deployments/docker-compose.yml up -d

# View logs
docker-compose -f deployments/docker-compose.yml logs -f

# Stop services
docker-compose -f deployments/docker-compose.yml down
```

### Manual Docker Build
```bash
# Build image
docker build -f deployments/Dockerfile -t bugtracker .

# Run container
docker run -p 8000:8000 bugtracker
```

## 📊 Features

### Core Features
- ✅ **Project Management**: Create, update, and manage projects
- ✅ **Bug Tracking**: Full CRUD operations for bugs
- ✅ **Comment System**: Add comments to bugs
- ✅ **User Assignment**: Assign bugs to team members
- ✅ **Status Tracking**: Track bug status (Open, In Progress, Resolved)
- ✅ **Priority Levels**: Set bug priorities (Low, Medium, High, Critical)

### Real-time Features
- ✅ **Live Updates**: WebSocket notifications for bug changes
- ✅ **Typing Indicators**: Real-time typing indicators in comments
- ✅ **Activity Logs**: Stream activity updates via WebSocket
- ✅ **Project Rooms**: Separate WebSocket rooms per project

### API Features
- ✅ **RESTful API**: Full CRUD operations
- ✅ **JWT Authentication**: Secure token-based authentication
- ✅ **Filtering & Search**: Filter bugs by status, project, assignee
- ✅ **API Documentation**: Auto-generated Swagger/OpenAPI docs
- ✅ **Pagination**: Page-based results
- ✅ **Ordering**: Sort results by various fields

## 🔒 Security

- JWT token authentication
- CORS configuration
- Input validation
- SQL injection protection
- XSS protection

## 📝 Environment Variables

Create a `.env` file:
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support, please open an issue in the repository or contact the development team.

