# HUST Solar Car Dashboard

Real-time telemetry dashboard for solar car racing, built for the Halmstad University Solar Team competing in BWSC. Vue.js frontend with Flask backend.

![Vue.js](https://img.shields.io/badge/Vue.js-3.4.21-4FC08D) ![Flask](https://img.shields.io/badge/Flask-2.3.3-000000) ![Python](https://img.shields.io/badge/Python-3.8+-3776AB)

## Features

- **Battery monitoring** - Voltage, current, cell temperatures with configurable alerts
- **Motor data** - Temperature and current monitoring with thermal protection
- **Solar tracking** - 3 MPPT controllers plus total power output
- **Vehicle metrics** - Speed, distance, energy consumption
- **BWSC-optimized alerts** - Racing-specific thresholds for Australian conditions
- **Energy management** - Real-time balance calculations with speed recommendations
- **Data persistence** - Automated cleanup with latest records protection
- **Development tools** - VS Code integration, hot reload, comprehensive error handling

## Repository Structure

```
├── backend/                 # Flask API server
│   ├── app.py              # Main application
│   ├── routes.py           # API endpoints
│   ├── socket_events.py    # WebSocket handlers
│   ├── database_cleanup.py # Data management
│   └── helpers.py          # Database utilities
├── hust-frontend/          # Vue.js dashboard
│   ├── src/ui/            # Dashboard components
│   │   ├── TelemDashboard.vue
│   │   ├── LiveChart.vue
│   │   ├── MetricPanel.vue
│   │   └── CleanupPanel.vue
│   ├── store.js           # State management
│   └── App.vue
├── requirements.txt        # Python dependencies
├── setup.sh / setup.bat   # Installation scripts
└── preview.html          # VS Code integration
```

## Core Features

### Real-time Telemetry
- Battery: Voltage, current, individual cell temperatures
- Motor: Current draw, temperature monitoring
- Solar: 3 MPPT controllers + total power output
- Vehicle: Speed, distance, energy consumption

### Racing Alerts (BWSC-optimized)
- Battery: 52V warning → 48V critical
- Temperature: 45°C warning → 55°C critical  
- Speed: 105 km/h highway → 135 km/h NT limit
- Energy balance with speed recommendations
- Data caching during connection drops
- Latest records protection (always keeps 300-500 newest records)

### Development Features
- Automated database cleanup with configurable retention
- Real-time statistics and system health monitoring
- VS Code preview integration
- Connection pooling and error recovery

## Installation

### Requirements
- Python 3.8+ with pip
- Node.js 16+ with npm
- MySQL database

### Quick Setup
```bash
git clone https://github.com/Lobbeb/Hust-SolarCar-Dashboard.git
cd Hust-SolarCar-Dashboard

# Run setup script
./setup.sh    # Linux/Mac/WSL
setup.bat     # Windows

# Configure database
cp .env.template .env
# Edit .env with your MySQL credentials
```

### Manual Installation
```bash
# Install dependencies
pip install -r requirements.txt
cd hust-frontend && npm install

# Start servers
python backend/app.py          # Backend (port 5000)
npm run dev                    # Frontend (port 5173)
```

## Usage

### Database Schema
Your MySQL database needs telemetry tables with these fields:

**Battery Data:**
- `Battery_Volt`, `Battery_Current`
- `Battery_Cell_1_Temp` through `Battery_Cell_N_Temp`

**Motor Data:**
- `Motor_Current`, `Motor_Temp`, `Motor_Controller_Temp`

**Solar Data (MPPT):**
- `MPPT1_Watt`, `MPPT2_Watt`, `MPPT3_Watt`, `MPPT_Total_Watt`

**Vehicle Data:**
- `Velocity`, `Distance_Travelled`

### Access
- Main dashboard: `http://localhost:5173`
- API backend: `http://localhost:5000`
- VS Code preview: Right-click `preview.html` → "Show Preview"

### Configuration

**Racing Thresholds** (edit in `TelemDashboard.vue`):
```javascript
// Battery thresholds (48V LiFePO4 system)
warningVoltage: 52V    // "Plan charging stop"
criticalVoltage: 48V   // "Find charging immediately"

// Temperature limits
warningTemp: 45°C      // Battery warming
criticalTemp: 55°C     // Thermal protection

// Speed limits (Australian roads)
speedWarning: 105 km/h   // Highway limit
speedCritical: 135 km/h  // NT speed limit
```

## Configuration

### Customizing for Your Car
Edit thresholds in `hust-frontend/src/ui/TelemDashboard.vue`:

- Battery voltage limits based on your pack chemistry
- Temperature limits based on your cooling system
- Speed alerts based on race regulations
- Solar power targets based on your array specs

### Database Management
The system includes automated data cleanup:
- Configurable retention periods (14-30 days)
- Always preserves latest 300-500 records
- Automatic table optimization
- Safety limits prevent accidental data loss

### Development
```bash
# Frontend with hot reload
cd hust-frontend && npm run dev

# VS Code integration
code preview.html    # Right-click → "Show Preview"
```

## Technical Details

### Backend
- Flask 2.3.3 with REST API and WebSocket support
- PyMySQL 1.0.3 with connection pooling
- APScheduler for automated database maintenance
- Socket.IO for real-time data updates

### Frontend
- Vue.js 3.4.21 with Composition API
- Pinia for state management and data caching
- Chart.js for real-time data visualization
- Vite development server with hot reload

### Database
- MySQL with optimized telemetry tables
- Timestamp-based indexing for performance
- Automated cleanup with configurable retention
- Multi-layer data protection system

## Contributors

This project was developed for the Halmstad University Solar Team's BWSC competition preparation.

**William Olsson** ([wilols20@student.hh.se](mailto:wilols20@student.hh.se)) - Lead Developer

## License

MIT License - See `LICENSE` file for details.

Open source for other solar car teams to use and improve.
