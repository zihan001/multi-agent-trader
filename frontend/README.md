# AI Multi-Agent Trading Simulator - Frontend

This is the frontend application for the AI Multi-Agent Crypto Trading Simulator, built with Next.js 14, TypeScript, and TailwindCSS.

## Features

- **Dashboard**: View real-time market data, technical indicators, and trigger AI analysis
- **Analysis View**: See detailed agent outputs (Technical, Sentiment, Tokenomics, Researcher, Trader, Risk Manager)
- **Portfolio View**: Track open positions, PnL, and trade history
- **Backtest View**: Run backtests on historical data with visualizations

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **TailwindCSS** - Utility-first CSS framework
- **Recharts** - Data visualization
- **Axios** - HTTP client
- **Lucide React** - Icon library
- **date-fns** - Date formatting

## Getting Started

### Prerequisites

- Node.js 20+ and npm
- Backend API running (see main README)

### Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Update API URL in .env.local if needed
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Development

```bash
# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

### Build for Production

```bash
# Build the application
npm run build

# Start production server
npm start
```

## Docker Deployment

### Using Docker Compose

```bash
# Production build
docker-compose up -d frontend

# Development with hot reload
docker-compose -f docker-compose.dev.yml up frontend
```

## Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── page.tsx           # Dashboard (home)
│   ├── analysis/          # Analysis results page
│   ├── portfolio/         # Portfolio page
│   ├── backtest/          # Backtest page
│   ├── layout.tsx         # Root layout with navigation
│   └── globals.css        # Global styles
├── components/            # Reusable React components
│   └── Navigation.tsx     # Navigation bar
├── lib/                   # Utilities and API client
│   └── api.ts            # Backend API client
├── types/                 # TypeScript type definitions
│   └── api.ts            # API response types
├── public/               # Static assets
├── Dockerfile            # Production Docker image
├── next.config.ts        # Next.js configuration
├── tailwind.config.ts    # TailwindCSS configuration
└── package.json          # Dependencies and scripts
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000` |

## Deployment Options

### Option 1: Vercel (Recommended)

1. Push code to GitHub
2. Import project in Vercel
3. Set environment variable: `NEXT_PUBLIC_API_URL`
4. Deploy

### Option 2: Docker on AWS ECS/EC2

Use the provided Dockerfile and deploy the container to AWS infrastructure.

## Troubleshooting

### API Connection Errors

- Ensure backend is running
- Check `NEXT_PUBLIC_API_URL` is correct
- Verify CORS is enabled on backend

### Build Errors

```bash
# Clear cache and rebuild
rm -rf .next node_modules
npm install
npm run build
```

## License

MIT License - See main repository README for details

