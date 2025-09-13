# E-Truck Logistics Optimizer

## Background
Traditional logistics relies on diesel trucks with:
- Long range (1,500 km)
- Abundant fueling infrastructure
- Fast refueling (5 min)
- Stable, predictable pricing

## Problem
Trucks generate >25% of EU road transport CO2 emissions. The shift to electric trucks introduces new challenges:
- Limited range (max 500 km)
- Scarce charging infrastructure (~60 stations in Germany)
- Slow charging (45 min for 30% to 80%)
- Volatile electricity pricing with significant variations:
  - Public charging: More expensive, varies by operator, location, payment method
  - Private charging: More economical, varies by time, tariff, and on-site generation

## Our Solution: AI Dispatcher
Our system optimizes e-truck routes by balancing feasibility, timing, and cost through:

**Inputs:**
- Delivery stops (locations/times)
- Internal variables: Depot locations, charging availability, driver shifts
- External variables: Traffic, charging station availability, dynamic pricing

**Output:**
An intelligent routing system that creates optimized, cost-effective drive and charge schedules for e-truck fleets.


### Backend Setup
```bash
cd backend
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

### Env file setup
- Create a file called .env
- Ask ashish for credentials

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```