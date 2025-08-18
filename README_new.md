# HUST Solar Car Dashboard

Real-time telemetry dashboard for solar car racing. Vue.js frontend with a Flask backend, developed for the Halmstad University Solar Team.

## Overview

Displays live battery, motor, solar, and vehicle metrics with racing-focused alerts and simple energy-balance guidance. Designed for BWSC conditions and on-vehicle operation.

## What’s inside

- `backend/` – Flask API and database utilities
- `hust-frontend/` – Vue 3 dashboard UI
- `requirements.txt` – Python dependencies
- `setup.sh` / `setup.bat` – Install scripts
- `preview.html` – VS Code preview helper

## Highlights

- Real-time telemetry (battery, motor, solar, vehicle)
- BWSC-aligned alerts (voltage, temperature, speed)
- Energy balance with basic speed suggestions
- Data continuity during brief disconnects
- Automated cleanup with latest-records protection
- Modern stack (Vue 3, Flask, Vite, Pinia)

## Quick start

Prerequisites: Python 3.8+, Node.js 16+, MySQL

```bash
# Clone
git clone https://github.com/Lobbeb/Hust-SolarCar-Dashboard.git
cd Hust-SolarCar-Dashboard

# Install
./setup.sh    # Linux/Mac/WSL
setup.bat     # Windows

# Configure
cp .env.template .env
# Edit .env with your database credentials
```

Manual setup:
```bash
# Backend
pip install -r requirements.txt
python backend/app.py

# Frontend
cd hust-frontend
npm install
npm run dev
```

## Configure

Adjust thresholds and UI behavior in:
- `hust-frontend/src/ui/TelemDashboard.vue`

Keep car-specific values (voltages, temperatures, limits) aligned with your hardware and race rules.

## Notes

- This repository excludes proprietary data sources and private race configs.
- Intended as a student project showcase and internal team tool.

## Contributor

- William Olsson (wilols20@student.hh.se)

## License

MIT – see `LICENSE`.
