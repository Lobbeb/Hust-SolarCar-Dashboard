# HUST Solar Car Dashboard

Welcome to the HUST Solar Car Dashboard project! This repository contains a comprehensive real-time telemetry system designed specifically for solar car racing, featuring advanced monitoring, critical alert systems, and race strategy optimization. Developed as part of the Halmstad University Solar Team's preparation for the Bridgestone World Solar Challenge (BWSC).

## Table of Contents

1. [Overview](#overview)
2. [Repository Contents](#repository-contents)
3. [Features](#features)
4. [Installation & Setup](#installation--setup)
5. [Usage](#usage)
6. [Technical Requirements](#technical-requirements)
7. [BWSC Racing Features](#bwsc-racing-features)
8. [API Documentation](#api-documentation)
9. [Contributors](#contributors)
10. [License](#license)

## Overview

• **Goal**: Provide real-time telemetry monitoring and race strategy optimization for solar-powered vehicles competing in endurance races.  
• **Key Focus**: Critical safety alerts, energy management, and strategic decision support for multi-day solar car racing.  
• **Context**: Built for the Halmstad University Solar Team's World Solar Challenge participation, optimized for Australian racing conditions.

## Repository Contents

1. **`backend/`**
   - Flask-based REST API with WebSocket support
   - Database connection pooling and advanced error handling
   - Real-time data fetching from MySQL telemetry database
   - Rate limiting and security features

2. **`hust-frontend/`**
   - Vue.js 3 + Pinia state management
   - Real-time dashboard with live charts and metrics
   - Mobile-responsive design for in-car use
   - Critical alert system with BWSC-optimized thresholds

3. **`preview.html`**
   - VS Code integrated preview system
   - Allows dashboard viewing without external browser
   - Auto-connection detection and error handling

4. **`.env.template`**
   - Environment configuration template
   - Database credentials and application settings
   - Security and performance configuration

5. **`IMPROVEMENTS.md`**
   - Comprehensive documentation of all enhancements
   - Technical implementation details
   - Performance optimizations and best practices

## Features

• **Real-time Telemetry**: Live monitoring of battery, motor, MPPT, and vehicle data  
• **Critical Alert System**: BWSC-optimized safety thresholds with visual/audio warnings  
• **Energy Management**: Real-time solar input vs power consumption analysis  
• **Race Strategy**: Intelligent recommendations based on energy balance  
• **Connection Pooling**: Optimized database performance for continuous monitoring  
• **Mobile Responsive**: Dashboard optimized for tablets and phones in racing environment  
• **VS Code Integration**: View dashboard directly in development environment  
• **Error Recovery**: Comprehensive error handling with automatic retry mechanisms  

## Installation & Setup

### Prerequisites
- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **MySQL Database** with telemetry tables
- **Git** for version control

### 1. Clone the Repository
```bash
git clone https://github.com/Lobbeb/Hust-SolarCar-Dashboard.git
cd Hust-SolarCar-Dashboard
```

### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.template .env
# Edit .env with your database credentials

# Start the backend server
cd backend
python app.py
```

### 3. Frontend Setup
```bash
# Install Node.js dependencies
cd hust-frontend
npm install

# Start development server
npm run dev
```

### 4. VS Code Integration (Optional)
- Install "Live Preview" extension in VS Code
- Right-click on `preview.html` → "Show Preview"
- Dashboard will open directly in VS Code

## Usage

### 1. Database Configuration
Ensure your MySQL database contains these tables with telemetry data:
- `Battery Data Table` - Voltage, current, cell temperatures
- `Motor Data Table` - Motor temperature, current, controller data
- `MPPT Data Table` - Solar panel power output (3 panels + total)
- `Vehicle Data Table` - Speed, distance, vehicle metrics

### 2. Starting the System
```bash
# Terminal 1: Backend
cd backend && python app.py

# Terminal 2: Frontend  
cd hust-frontend && npm run dev

# Access dashboard at: http://localhost:5173
```

### 3. Racing Configuration
- Adjust alert thresholds in `TelemDashboard.vue` for your specific vehicle
- Configure speed limits based on race regulations
- Set battery voltage thresholds based on your pack configuration
- Customize solar power targets based on panel specifications

### 4. Mobile/Tablet Use
- Dashboard is optimized for landscape tablet use in racing vehicles
- Touch-friendly controls for easy operation with gloves
- High contrast display for outdoor visibility

## Technical Requirements

### Hardware
- **Server**: Any computer capable of running Python/Node.js
- **Database**: MySQL 5.7+ or MariaDB 10.3+
- **Network**: WiFi or cellular connection for real-time data
- **Display**: Tablet/laptop for dashboard viewing (1024x768+ recommended)

### Software Dependencies
- **Backend**: Flask, PyMySQL, python-socketio, python-dotenv
- **Frontend**: Vue.js 3, Pinia, Chart.js, Socket.IO client
- **Database**: MySQL with proper telemetry table structure

### Performance
- **Database Pool**: 10 concurrent connections for high-frequency data
- **Update Rate**: 1-5 second intervals for real-time monitoring
- **Memory Usage**: ~50MB backend, ~100MB frontend
- **CPU Usage**: Minimal (<5% on modern hardware)

## BWSC Racing Features

### Critical Alert System
```javascript
// Battery Management
- 52V Warning: "Plan charging stop soon"
- 48V Critical: "Find charging immediately!"

// Temperature Monitoring (Australian conditions)
- 45°C Warning: Battery warming in outback heat
- 55°C Critical: Risk of thermal runaway

// Speed Compliance (Australian road rules)
- 105 km/h Warning: Approaching highway limit
- 135 km/h Critical: Over Northern Territory limit
```

### Energy Strategy Dashboard
- **Real-time Energy Balance**: Solar input vs power consumption
- **Race Recommendations**: Intelligent speed/power suggestions
- **Sustainability Indicator**: "SUSTAIN" or "ADJUST" guidance
- **Efficiency Monitoring**: km/h per watt calculations

### Solar Panel Optimization
- **Individual Panel Monitoring**: MPPT1, MPPT2, MPPT3 performance
- **Efficiency Classification**: Excellent/Good/Poor/Critical
- **Weather Impact**: Cloud/shade detection and alerts

## API Documentation

### REST Endpoints
```bash
GET /data              # Fetch all telemetry data
GET /data/<table>      # Fetch specific table data
GET /health           # System health check
GET /export/csv       # Export data as CSV
```

### WebSocket Events
```javascript
// Client → Server
'join'                # Join real-time updates
'fetch_data'          # Request data refresh

// Server → Client  
'telemetry_data'      # Real-time data broadcast
'connection_status'   # Connection state updates
'error'              # Error notifications
```

### Database Schema
```sql
-- Battery Data Table
Battery_Volt, Battery_Current, Battery_Cell_*_Temp

-- Motor Data Table  
Motor_Current, Motor_Temp, Motor_Controller_Temp

-- MPPT Data Table
MPPT1_Watt, MPPT2_Watt, MPPT3_Watt, MPPT_Total_Watt

-- Vehicle Data Table
Velocity, Distance_Travelled
```

## Contributors

• **William Olsson** ([wilols20@student.hh.se](mailto:wilols20@student.hh.se)) - Lead Developer  
• **Halmstad University Solar Team** - Racing requirements and testing  

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

This project was developed as part of the Halmstad University Solar Team's preparation for the Bridgestone World Solar Challenge and is shared openly for educational purposes and the advancement of solar vehicle technology.
