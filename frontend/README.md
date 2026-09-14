# Finpilot-AI / Frontend Dashboard

Next.js 14+ and TypeScript executive Business Intelligence dashboard providing real-time data visualization, Prophet revenue forecasting, Isolation Forest anomaly auditing, and prescriptive recommendations.

## Features
- **Executive KPI Cards**: Real-time Gross Revenue, Order Volume, AOV, and Active Fraud/Anomaly alerts.
- **Historical Trends Visualizer**: Interactive time-series bar and volume chart with 7D / 30D toggles.
- **Prophet AI Forecast Corridor**: Dynamic spline rendering with 95% Bayesian uncertainty confidence corridor.
- **Merchandising Category & Store Mix**: Category revenue share and store leaderboard.
- **Anomaly Detection Feed**: Isolation Forest flagged transactions with severity tags (`Critical`, `Warning`, `Moderate`) and diagnostic explanations.
- **Prescriptive AI Intelligence**: Actionable business recommendations with estimated ROI impact.

## Development Setup

```bash
# Install dependencies
npm install

# Run local development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Docker
```bash
docker build -t finpilot-frontend .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://localhost:8000 finpilot-frontend
```
