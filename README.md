# HUST Solar Car Dashboard

A real-time telemetry dashboard for monitoring solar car performance during racing. Built with Vue.js frontend and Flask backend, designed for the Halmstad University Solar Team.

## Overview

This dashboard displays live telemetry data from a solar car's onboard systems including battery status, motor performance, solar panel output, and vehicle metrics. Features critical alerts for racing safety and energy management recommendations.

## Repository Contents

- **`backend/`** - Flask API with MySQL database integration and WebSocket support
- **`hust-frontend/`** - Vue.js 3 dashboard with real-time charts and alerts  
- **`requirements.txt`** - Python dependencies
- **`setup.sh/setup.bat`** - Installation scripts
- **`preview.html`** - VS Code integration for development

## Features

**Real-time Monitoring:**
- Battery voltage, current, and cell temperatures
- Motor temperature and current draw
- Solar panel power output (3 individual + total)
- Vehicle speed and distance traveled

**Critical Alerts:**
- Battery voltage warnings (52V warning, 48V critical)
- Temperature monitoring (45°C warning, 55°C critical)
- Speed limit compliance (105 km/h warning, 135 km/h critical)
- Motor overheating protection

**Race Strategy:**
- Real-time energy balance calculation
- Speed recommendations based on energy surplus/deficit
- Solar efficiency monitoring

**Database Management:**
- Automated cleanup every 7 days (configurable)
- Intelligent data retention (14-30 days based on data type)
- Manual cleanup tools and statistics
- Prevents database overflow during long racing sessions

## Installation & Setup

### Prerequisites
- Python 3.8+ with pip
- Node.js 16+ with npm  
- MySQL database with telemetry tables

### Quick Setup
```bash
# Clone repository
git clone https://github.com/Lobbeb/Hust-SolarCar-Dashboard.git
cd Hust-SolarCar-Dashboard

# Run setup script
./setup.sh    # Linux/Mac
setup.bat     # Windows

# Configure database
cp .env.template .env
# Edit .env with your database credentials
```

### Manual Setup
```bash
# Backend
pip install -r requirements.txt
cd backend && python app.py

# Frontend  
cd hust-frontend
npm install && npm run dev
```

## Usage

**Database Requirements:**
Your MySQL database needs tables with these fields:
- Battery: `Battery_Volt`, `Battery_Current`, `Battery_Cell_*_Temp`
- Motor: `Motor_Current`, `Motor_Temp`, `Motor_Controller_Temp`  
- MPPT: `MPPT1_Watt`, `MPPT2_Watt`, `MPPT3_Watt`, `MPPT_Total_Watt`
- Vehicle: `Velocity`, `Distance_Travelled`

**Access:**
- Backend API: `http://localhost:5000`
- Frontend Dashboard: `http://localhost:5173`
- VS Code Preview: Right-click `preview.html` → "Show Preview"

## Configuration

### Racing Thresholds
Adjust alert thresholds in `TelemDashboard.vue` based on your car's specifications:
- Configure speed limits based on race regulations and road conditions
- Set battery voltage thresholds based on your pack's voltage and chemistry
- Customize solar power targets based on your panel array specifications

### Alert System
Current thresholds (modify as needed):
```javascript
// Battery (assumes 48V system)
52V - Warning: "Plan charging stop soon"  
48V - Critical: "Find charging immediately!"

// Temperature (Australian conditions)
45°C - Warning: Battery warming
55°C - Critical: Thermal danger

// Speed (Australian road limits)  
105 km/h - Warning: Approaching highway limit
135 km/h - Critical: Over Northern Territory limit
```

## API Endpoints

- `GET /data` - Fetch all telemetry data
- `GET /data/<table>` - Fetch specific table  
- `GET /health` - System health check

**Database Management:**
- `GET /admin/cleanup/stats` - Database statistics
- `GET /admin/cleanup/recommendations` - Cleanup recommendations
- `POST /admin/cleanup/dry-run` - Preview cleanup without deleting
- `POST /admin/cleanup/execute` - Execute cleanup (requires confirmation)
- `POST /admin/cleanup/scheduler/start` - Start automated cleanup
- `POST /admin/cleanup/scheduler/stop` - Stop automated cleanup

**Smart Data Protection:**
Our cleanup system uses dual protection to ensure the dashboard always has data:
- ⏰ **Time-based retention**: Keeps data for 14-30 days (configurable)
- 🛡️ **Latest records protection**: Always preserves the newest 300-500 records regardless of age
- 🔢 **Minimum thresholds**: Never deletes if tables would have fewer than 500-1000 records

This means even during long storage periods, you'll always have recent telemetry data to view.

**Command Line Utility:**
```bash
# Show database statistics
python cleanup_utility.py --stats

# Preview cleanup
python cleanup_utility.py --dry-run

# Execute cleanup
python cleanup_utility.py --execute

# Get recommendations
python cleanup_utility.py --recommendations
```

## Contributors

**William Olsson** ([wilols20@student.hh.se](mailto:wilols20@student.hh.se)) - Lead Developer

## License

MIT License - see LICENSE file for details.
