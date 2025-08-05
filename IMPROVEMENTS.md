# HUST Solar Car Dashboard - Enhanced Version

## 🚀 New Features & Improvements

### Backend Improvements
- ✅ **Database Connection Pooling** - Better performance and reliability
- ✅ **Enhanced Error Handling & Logging** - Comprehensive logging system
- ✅ **Input Validation** - Secure parameter validation
- ✅ **Rate Limiting** - Protect against abuse (30 req/min by default)
- ✅ **Health Check Endpoint** - `/health` for monitoring
- ✅ **Environment Variables** - Secure configuration management

### Frontend Improvements
- ✅ **Enhanced Vue Store** - Better state management with error handling
- ✅ **Loading States** - Visual feedback during data loading
- ✅ **Error States** - User-friendly error messages with retry
- ✅ **Connection Status** - Real-time connection indicators
- ✅ **Data Staleness Detection** - Alerts when data is outdated
- ✅ **Improved CSV Export** - Better file naming and error handling

## 🛠️ Setup Instructions

### 1. Environment Configuration
Create a `.env` file in the root directory:
```bash
cp .env.template .env
```

Edit `.env` with your database credentials:
```env
DB_HOST=your_database_host
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_NAME=your_database_name
SECRET_KEY=your_secret_key_here
```

### 2. Backend Setup
```bash
pip install -r requirements.txt
python backend/app.py
```

### 3. Frontend Setup
```bash
cd hust-frontend
npm install
npm run dev
```

## 🔧 Configuration Options

### Environment Variables
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` - Database connection
- `SECRET_KEY` - Flask secret key
- `FLASK_ENV` - `development` or `production`
- `LOG_LEVEL` - `DEBUG`, `INFO`, `WARNING`, `ERROR`
- `MAX_DB_CONNECTIONS` - Database connection pool size (default: 10)
- `RATE_LIMIT_PER_MINUTE` - API rate limit (default: 30)

## 📊 New Endpoints

### Health Check
```
GET /health
```
Returns application health status and database connectivity.

### Enhanced Data API
```
GET /data?limit=100
```
- Input validation (limit: 1-1000)
- Rate limiting
- Better error responses

### Enhanced CSV Export
```
GET /export_csv?limit=500
```
- Supports larger exports (up to 5000 records)
- Timestamped filenames
- All data types included

## 🎨 Frontend Features

### Connection Status
- Real-time connection indicator
- Automatic reconnection attempts
- Visual feedback for connection state

### Error Handling
- Loading spinners during data fetching
- Error overlays with retry buttons
- Graceful fallbacks for missing data

### Data Quality Indicators
- Stale data warnings
- Data availability checks
- Enhanced statistics with trends

## 🔍 Monitoring

### Logs
Application logs are written to `app.log` and console with timestamps and severity levels.

### Health Monitoring
Monitor the `/health` endpoint:
```bash
curl http://localhost:5000/health
```

Example response:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-05T10:30:00.000Z",
  "database": "connected",
  "version": "1.0.0"
}
```

## 🚨 Error Handling

### Database Issues
- Connection pooling with automatic retry
- Graceful degradation when DB is unavailable
- Health checks for monitoring

### Network Issues
- WebSocket reconnection logic
- Retry mechanisms with exponential backoff
- User-friendly error messages

## 🔒 Security Features

- Input validation on all endpoints
- Rate limiting to prevent abuse
- Parameterized SQL queries (existing)
- Secure environment variable handling

## 📝 Development Notes

### Core Functionality Preserved
All original features remain intact:
- Real-time telemetry streaming
- Interactive charts and metrics
- CSV data export
- Multi-metric dashboard

### Vue.js Enhancements
- Upgraded to use Pinia for state management
- Better component composition
- Enhanced user experience
- More robust error handling

## 🎯 Quick Start Checklist

1. [ ] Copy `.env.template` to `.env`
2. [ ] Configure database credentials in `.env`
3. [ ] Install Python dependencies: `pip install -r requirements.txt`
4. [ ] Install Node dependencies: `cd hust-frontend && npm install`
5. [ ] Start backend: `python backend/app.py`
6. [ ] Start frontend: `npm run dev`
7. [ ] Check health: `curl http://localhost:5000/health`

## 🆘 Troubleshooting

### Common Issues
1. **Database Connection Error**: Check `.env` credentials
2. **Port Already in Use**: Change port in app.py or kill existing process
3. **Node Module Errors**: Delete `node_modules` and run `npm install`
4. **Import Errors**: Ensure all Python dependencies are installed

### Debug Mode
Set `FLASK_ENV=development` in `.env` for detailed error messages.
