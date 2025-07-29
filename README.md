# Passive CAPTCHA System with ML Model & Admin Panel

A production-ready passive CAPTCHA system that uses machine learning to distinguish humans from bots through behavioral biometrics and device fingerprinting, with comprehensive admin monitoring and easy deployment capabilities.

## Project Overview

- **Frontend**: JavaScript widget for universal website integration
- **Backend**: ML inference API with admin dashboard  
- **Database**: Verification logs and analytics storage
- **Deployment**: Cloud-native architecture (Railway/Vercel/Heroku)
- **Admin Panel**: Real-time monitoring, analytics, and system management

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client Sites  │────│  CDN (Vercel)    │────│  API (Railway)  │
│  (Any Website)  │    │  - JS Widget     │    │  - ML Model     │
│                 │    │  - Static Files  │    │  - Admin Panel  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                ┌─────────────────┐
                                                │   Database      │
                                                │  - SQLite/PG    │
                                                │  - Logs & Stats │
                                                └─────────────────┘
```

## Project Structure

```
passive-captcha/
├── frontend/                 # JavaScript widget & demo site
│   ├── src/
│   │   ├── passive-captcha.js    # Main widget script
│   │   ├── feature-extractor.js  # Behavioral analysis
│   │   └── device-fingerprint.js # Hardware fingerprinting
│   ├── demo/                     # Integration examples
│   └── dist/                     # Built files for CDN
├── backend/                  # ML API & admin dashboard
│   ├── app/
│   │   ├── api/                  # REST API endpoints
│   │   ├── ml/                   # Machine learning model
│   │   ├── admin/                # Admin dashboard
│   │   └── database/             # Database models
│   ├── models/                   # Trained ML models
│   └── requirements.txt          # Python dependencies
├── dataset/                  # Training data management
│   ├── raw/                      # Original datasets
│   ├── processed/                # Feature-engineered data
│   └── scripts/                  # Data processing pipeline
└── docs/                     # Documentation
    ├── api.md                    # API documentation
    ├── integration.md            # Integration guide
    └── deployment.md             # Deployment instructions
```

## ML Model Specifications

- **Algorithm**: Random Forest Classifier
- **Features**: 11-dimensional vector (behavioral + device fingerprinting)
- **Target Accuracy**: 85-92%
- **Inference Time**: <100ms per request
- **Framework**: scikit-learn

### Feature Vector

1. **Behavioral Features (70% weight)**:
   - Mouse movement count and velocity
   - Keystroke dynamics and timing
   - Session duration and scroll patterns

2. **Device Fingerprint Features (30% weight)**:
   - WebGL support and capabilities
   - Canvas fingerprinting
   - Hardware legitimacy scores

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 14+
- Git

### Development Setup

1. **Clone Repository**
```bash
git clone https://github.com/your-org/passive-captcha.git
cd passive-captcha
```

2. **Backend Setup**
```bash
cd backend
pip install -r requirements.txt
python app.py
```

3. **Frontend Setup**
```bash
cd frontend
npm install
npm run build
npm run serve
```

4. **Database Setup**
```bash
cd backend
python -c "from app.database import init_db; init_db()"
```

### Integration Example

```html
<script src="https://passive-captcha.vercel.app/passive-captcha.js"></script>
<script>
PassiveCaptcha.init({
    element: '#protected-button',
    onVerified: (result) => {
        if (result.isHuman && result.confidence > 0.7) {
            // Allow action
            document.getElementById('protected-content').style.display = 'block';
        } else {
            // Show fallback or challenge
            alert('Verification required. Please try again.');
        }
    }
});
</script>
```

## API Endpoints

### Verification API
```http
POST /api/verify
Content-Type: application/json

{
  "sessionId": "string",
  "mouseMovements": [...],
  "keystrokes": [...],
  "fingerprint": {...},
  "sessionDuration": 15000,
  "origin": "https://example.com"
}
```

### Admin Analytics API
```http
GET /admin/analytics?hours=24
Authorization: Bearer <admin_token>
```

## Deployment

### Frontend (Vercel)
```bash
cd frontend
vercel --prod
```

### Backend (Railway)
```bash
cd backend
railway up
```

### Environment Variables
```bash
# Backend
MODEL_PATH=models/passive_captcha_rf.pkl
DATABASE_URL=sqlite:///passive_captcha.db
ADMIN_SECRET=your-secret-key
CONFIDENCE_THRESHOLD=0.6

# Frontend
REACT_APP_API_URL=https://your-api.railway.app
```

## Performance Requirements

- **ML Inference**: <100ms per request
- **API Response**: <150ms total
- **Script Loading**: <50ms from CDN
- **Concurrent Users**: 1,000+ simultaneous verifications
- **Daily Requests**: 100,000+ verifications

## Security Features

- HTTPS-only communication
- Rate limiting (100 requests/hour per IP)
- Input validation and sanitization
- No PII storage (privacy-compliant)
- CORS configuration for cross-origin requests

## Monitoring & Analytics

The admin dashboard provides:
- Real-time verification statistics
- Human vs bot detection rates
- API performance metrics
- Feature importance analysis
- Geographic distribution maps

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation in `/docs`
- Review integration examples in `/frontend/demo` 