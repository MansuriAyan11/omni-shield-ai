# OmniShield Frontend - React + TypeScript

Modern, minimalist black & white UI for AI-powered content moderation platform.

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool & dev server
- **React Router** - Client-side routing
- **Axios** - HTTP client with JWT interceptors
- **TanStack Query** - Server state management
- **Recharts** - Data visualization
- **Tailwind CSS** - Utility-first styling
- **Lucide React** - Icon library

## Features

- ✅ JWT Authentication with auto-refresh
- ✅ Protected routes
- ✅ Image upload & moderation
- ✅ Real-time analytics dashboards
- ✅ API key management
- ✅ Black & white minimalist design
- ✅ Responsive layout
- ✅ TypeScript for type safety

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running on http://localhost:8000

### Installation

```bash
cd frontend-react
npm install
```

### Environment Setup

Create `.env` file:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

### Development

```bash
npm run dev
```

Open http://localhost:3000

### Build for Production

```bash
npm run build
npm run preview  # Test production build
```

## Project Structure

```
src/
├── components/       # Reusable components
│   └── Layout.tsx   # Main layout with nav
├── pages/           # Route pages
│   ├── Login.tsx
│   ├── Register.tsx
│   ├── Dashboard.tsx
│   ├── Moderate.tsx
│   ├── Analytics.tsx
│   └── APIKeys.tsx
├── lib/             # Utilities
│   ├── axios.ts     # Axios instance with interceptors
│   └── api.ts       # API functions
├── App.tsx          # Router & auth logic
├── main.tsx         # App entry point
└── index.css        # Global styles
```

## API Integration

All API calls are centralized in `src/lib/api.ts`:

```typescript
import api from '@/lib/api'

// Authentication
api.auth.login(email, password)
api.auth.register(email, password)

// Moderation
api.moderation.moderateImage(formData)
api.moderation.moderateMultiModel(formData)

// API Keys
api.keys.createKey(name)
api.keys.listKeys()

// Analytics
api.analytics.getStats()
api.analytics.getTimeSeries(days)
```

## Authentication Flow

1. User logs in → JWT token stored in localStorage
2. Axios interceptor auto-adds token to all requests
3. On 401 response → Clear token & redirect to login
4. Protected routes check authentication state

## Deployment

### Vercel (Recommended)

```bash
npm install -g vercel
vercel
```

### Docker

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Design System

### Colors
- **Black**: #000000 (primary)
- **White**: #ffffff (text on dark bg)
- **Gray shades**: For borders & secondary elements

### Typography
- System font stack for optimal performance
- Font weights: 400 (normal), 500 (medium), 700 (bold)

### Components
- Consistent 8px spacing grid
- Rounded corners (4px, 8px)
- Subtle shadows on white surfaces
- High contrast for accessibility
