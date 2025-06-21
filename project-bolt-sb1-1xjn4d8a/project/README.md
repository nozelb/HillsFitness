# 🏋️ Gym AI Coach - Personalized Training & Nutrition Web App

An AI-powered fitness application that analyzes your physique from uploaded images and generates personalized workout and nutrition plans based on evidence-based fitness principles.

## 🎯 Features

- **AI Physique Analysis**: Upload photos for automated body measurement estimation using MediaPipe and OpenCV
- **Smart Plan Generation**: Evidence-based workout plans following ACSM guidelines
- **Personalized Nutrition**: Custom meal plans with macro calculations using Harris-Benedict equation
- **User Authentication**: Secure JWT-based authentication system
- **Progress Tracking**: Store and view previous plans and analyses
- **PDF Export**: Download your complete fitness plan as a PDF
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## 🚀 Tech Stack

### Backend
- **Python 3.11** with FastAPI framework
- **MediaPipe + OpenCV** for image analysis and pose detection
- **TinyDB** for lightweight JSON-based data storage
- **Pydantic** for data validation and serialization
- **JWT Authentication** for secure user sessions

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for responsive styling
- **Lucide React** for beautiful icons

### DevOps
- **Docker** containerization with multi-service setup
- **Docker Compose** for orchestration
- **Hot reload** development environment

## 📋 Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

## 🔧 Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd gym-ai-coach
   ```

2. **Start the application**
   ```bash
   docker compose up --build
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Local Development Setup

#### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
npm install
npm run dev
```

## 📖 API Documentation

The FastAPI backend automatically generates interactive API documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

- `POST /api/register` - User registration
- `POST /api/login` - User authentication
- `POST /api/upload-image` - Upload and analyze physique photos
- `POST /api/user-data` - Store user physical data
- `POST /api/generate-plan` - Generate personalized workout and nutrition plan
- `GET /api/plans` - Retrieve user's previous plans

### Example API Usage

```bash
# Register a new user
curl -X POST "http://localhost:8000/api/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "John Doe"
  }'

# Upload and analyze image
curl -X POST "http://localhost:8000/api/upload-image" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@/path/to/your/photo.jpg"
```

## 🏗️ Project Structure

```
gym-ai-coach/
├── backend/
│   ├── main.py              # FastAPI application entry point
│   ├── models.py            # Pydantic data models
│   ├── plan_engine.py       # Workout plan generation logic
│   ├── nutrition_engine.py  # Nutrition plan calculation
│   ├── image_utils.py       # Image analysis with MediaPipe
│   ├── database.py          # TinyDB database operations
│   └── requirements.txt     # Python dependencies
├── src/
│   ├── components/          # React components
│   ├── api.js              # API client utilities
│   └── App.tsx             # Main React application
├── docker-compose.yaml      # Multi-service Docker setup
├── Dockerfile-backend       # Backend container configuration
├── Dockerfile-frontend      # Frontend container configuration
└── README.md               # You are here! 📍
```

## 🧪 Development Workflow

1. **Make your changes** to the backend or frontend code
2. **Backend changes**: The FastAPI server will auto-reload
3. **Frontend changes**: Vite will hot-reload the React app
4. **Test your changes** using the interactive frontend or API docs
5. **Build for production** using Docker Compose

## 🔒 Security Features

- JWT-based authentication with secure token handling
- Password hashing using bcrypt
- Input validation and sanitization
- CORS protection for cross-origin requests
- File type validation for image uploads

## 🎨 User Experience

The application provides a guided, multi-step process:

1. **Account Creation**: Simple registration with email and password
2. **Photo Upload**: Intuitive drag-and-drop interface with real-time analysis
3. **Data Entry**: Clean forms for physical measurements and smart scale data
4. **Goal Setting**: Visual goal selection with clear descriptions
5. **Plan Generation**: Instant plan creation with loading indicators
6. **Plan Review**: Comprehensive plan display with download options

## 🔬 AI Analysis Details

### Image Processing
- **Pose Detection**: Uses MediaPipe's pose estimation model
- **Body Measurements**: Calculates shoulder, waist, and hip measurements
- **Body Fat Estimation**: US Navy method with confidence scoring
- **Fallback Handling**: Graceful degradation when analysis fails

### Plan Generation
- **Workout Plans**: ACSM-compliant exercise selection and programming
- **Nutrition Calculations**: Harris-Benedict BMR with activity multipliers
- **Macro Distribution**: Goal-specific protein, carb, and fat ratios
- **Meal Suggestions**: Sample meals with ingredient lists

## 🤔 Why did the gym AI coach break up with the treadmill? Because it wasn't working out! 

*(Had to get the dad joke in there somewhere... back to serious documentation!)* 

## 🚀 Deployment

For production deployment:

1. **Environment Variables**: Set up proper environment variables for security
2. **Database**: Consider migrating from TinyDB to PostgreSQL for production scale
3. **File Storage**: Implement cloud storage for uploaded images
4. **SSL/HTTPS**: Enable secure connections
5. **Monitoring**: Add application monitoring and logging

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Support

For support, email support@gymaicoach.com or create an issue in the GitHub repository.

---

**Built with ❤️ for fitness enthusiasts who love technology**