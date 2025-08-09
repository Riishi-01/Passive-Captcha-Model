# Passive CAPTCHA Admin Dashboard

A modern, responsive admin dashboard for managing the Passive CAPTCHA system built with React, Vite, and Tailwind CSS.

## Features

- 🔐 **Password-only Authentication** - Simple admin login
- 📊 **Real-time Analytics** - System performance metrics and charts
- 🌐 **Website Management** - Add, edit, and monitor protected websites
- 🧠 **ML Monitoring** - Track model performance and accuracy
- 🚨 **Alert System** - Real-time notifications and alerts
- 📝 **System Logs** - Comprehensive activity logging
- ⚙️ **Settings Management** - Configure system parameters
- 🌙 **Dark/Light Theme** - User preference theme switching
- 📱 **Responsive Design** - Mobile-friendly interface

## Tech Stack

- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Routing**: React Router DOM
- **Charts**: Recharts
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **Build Tool**: Vite

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn
- Backend API running on port 8000

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file:
```bash
cp .env.example .env
```

4. Configure environment variables:
```env
VITE_API_BASE_URL=http://localhost:8000
```

5. Start development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Project Structure

```
src/
├── components/          # Reusable UI components
├── layouts/            # Page layouts (Auth, Dashboard)
├── views/              # Page components
├── stores/             # Zustand state stores
├── services/           # API service layer
├── hooks/              # Custom React hooks
├── router/             # Route configuration
├── App.jsx             # Main application component
└── main.jsx            # Application entry point
```

## API Integration

The frontend communicates with the backend through a RESTful API. Key endpoints:

- `POST /admin/login` - Authentication
- `GET /admin/analytics/stats` - Dashboard statistics
- `GET /admin/websites` - Website management
- `GET /admin/ml/health` - ML model monitoring
- `GET /admin/alerts/recent` - System alerts
- `GET /admin/logs` - System logs

## Authentication

The application uses JWT tokens for authentication:
- Admin login with password only
- Token stored in localStorage
- Automatic token verification
- Auto-redirect on token expiration

## State Management

Uses Zustand for state management with persistent storage:

- `authStore` - Authentication state
- `appStore` - Global app state (theme, notifications)
- `dashboardStore` - Dashboard data and metrics
- `websitesStore` - Website management state

## Components

### Layout Components
- `AuthLayout` - Minimal layout for login
- `DashboardLayout` - Main dashboard layout with sidebar

### UI Components
- `KPICard` - Metric display cards
- `SystemStatusIndicator` - System health indicator
- `LiveActivityFeed` - Real-time activity display
- `ModelAccuracyChart` - ML performance visualization

### Form Components
- `LoginForm` - Admin authentication form
- `WebsiteModal` - Add/edit website modal

## Theming

Supports dark and light themes:
- Theme preference stored in localStorage
- Automatic system theme detection
- Tailwind CSS dark mode classes
- Theme toggle in header

## Development

### Code Style
- ESLint for code linting
- Prettier for code formatting
- Consistent component structure
- TypeScript-style prop validation

### Performance
- Lazy loading for routes
- Optimized bundle splitting
- Efficient re-renders with Zustand
- Image optimization

## Deployment

### Docker

Build Docker image:
```bash
docker build -t passive-captcha-frontend .
```

Run container:
```bash
docker run -p 5173:5173 passive-captcha-frontend
```

### Static Hosting

The built application can be deployed to any static hosting service:
- Netlify
- Vercel
- AWS S3 + CloudFront
- GitHub Pages

## Configuration

### Environment Variables

- `VITE_API_BASE_URL` - Backend API URL
- `VITE_APP_NAME` - Application name
- `VITE_APP_VERSION` - Application version

### Build Configuration

Vite configuration in `vite.config.js`:
- Proxy setup for development
- Build optimizations
- Asset handling

## Contributing

1. Follow the existing code structure
2. Use TypeScript-style JSDoc comments
3. Test all components thoroughly
4. Ensure responsive design
5. Follow accessibility guidelines

## License

[License information here]
