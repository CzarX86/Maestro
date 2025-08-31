# 🎭 Maestro Dashboard

Real-time visualization and monitoring dashboard for the Maestro Orchestrator pipeline.

## 🌟 Features

- **Real-time Graph Visualization**: Interactive D3.js graph showing pipeline stages
- **Live Status Updates**: WebSocket-based real-time status updates for each agent
- **Progress Tracking**: Visual progress indicators and status text boxes
- **Metrics Dashboard**: Live metrics including execution time, test results, and coverage
- **Log Streaming**: Real-time log streaming with color-coded levels
- **Responsive Design**: Modern, mobile-friendly interface

## 🏗️ Architecture

```
┌─────────────────┐    WebSocket    ┌─────────────────┐
│   Dashboard     │◄──────────────►│  WebSocket      │
│   (Frontend)    │                 │  Server         │
└─────────────────┘                 └─────────────────┘
         │                                    │
         │                                    │
         ▼                                    ▼
┌─────────────────┐                 ┌─────────────────┐
│   D3.js Graph   │                 │  Orchestrator   │
│   Visualization │                 │  Integration    │
└─────────────────┘                 └─────────────────┘
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# From project root
poetry install

# Or using make
make install
```

### 2. Start the Dashboard

```bash
# Using Poetry
poetry run python dashboard/server.py

# Or using make
make dashboard

# Or using the startup script
./start_dashboard.sh
```

This will start:
- WebSocket server on `ws://localhost:8765`
- HTTP server on `http://localhost:8080`

### 3. Open Dashboard

Open your browser to: `http://localhost:8080`

## 📊 Dashboard Components

### Pipeline Graph
- **Nodes**: Each agent (Planner, Coder, Integrator, Tester, Reporter)
- **Status Colors**:
  - 🔵 Blue: Running (with pulsing animation)
  - 🟢 Green: Completed
  - 🟡 Yellow: Waiting
  - 🔴 Red: Failed
- **Text Boxes**: Real-time status information above each node

### Status Bar
- Current task being executed
- Connection status to WebSocket server
- Real-time connection indicator

### Metrics Grid
- **Total Time**: Pipeline execution time
- **Tests Passed**: Number of successful tests
- **Coverage**: Code coverage percentage
- **Files Touched**: Number of files modified

### Logs Panel
- Real-time log streaming
- Color-coded log levels (INFO, WARN, ERROR, SUCCESS)
- Timestamps for each log entry
- Auto-scrolling to latest entries

## 🎮 Controls

- **Start Pipeline**: Begin orchestrator execution
- **Pause**: Pause current execution
- **Reset**: Reset pipeline to initial state
- **Toggle Logs**: Show/hide logs panel

## 🔧 Configuration

### Environment Variables

```bash
# Dashboard server configuration
DASHBOARD_HOST=localhost          # WebSocket server host
DASHBOARD_PORT=8765              # WebSocket server port
DASHBOARD_HTTP_PORT=8080         # HTTP server port

# Orchestrator integration
DASHBOARD_URL=ws://localhost:8765 # WebSocket URL for integration
```

### WebSocket Messages

The dashboard communicates via WebSocket messages:

#### Client → Server
```json
{
  "type": "get_status",
  "task": "demo"
}
```

#### Server → Client
```json
{
  "type": "stage_update",
  "stage": "planner",
  "status": "running",
  "progress": "50%",
  "task": "demo",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 🔌 Integration with Orchestrator

### Using Enhanced Orchestrator

```bash
# Run orchestrator with dashboard integration
./orchestrator/orchestrate_with_dashboard.sh demo
```

### Manual Integration

Add dashboard updates to your orchestrator scripts:

```bash
# Send stage start notification
send_dashboard_update "planner" "running" "0%"

# Send progress update
send_dashboard_update "planner" "running" "50%"

# Send completion notification
send_dashboard_update "planner" "completed" "100%"
```

## 🎨 Customization

### Styling
The dashboard uses CSS custom properties for easy theming:

```css
:root {
  --primary-color: #3498db;
  --success-color: #27ae60;
  --warning-color: #f39c12;
  --error-color: #e74c3c;
}
```

### Adding New Metrics
Extend the metrics grid by modifying the HTML and JavaScript:

```javascript
// Add new metric card
const newMetric = {
  value: "42",
  label: "New Metric"
};
```

## 🐛 Troubleshooting

### Dashboard Not Loading
1. Check if HTTP server is running on port 8080
2. Verify browser console for JavaScript errors
3. Ensure all dependencies are installed

### WebSocket Connection Issues
1. Check if WebSocket server is running on port 8765
2. Verify firewall settings
3. Check browser WebSocket support

### No Real-time Updates
1. Verify orchestrator is sending WebSocket messages
2. Check WebSocket server logs
3. Ensure correct DASHBOARD_URL configuration

## 📈 Performance

- **WebSocket**: Low-latency real-time updates
- **D3.js**: Efficient graph rendering and updates
- **Log Streaming**: Optimized for high-volume logs
- **Memory Management**: Automatic log rotation (100 entries max)

## 🔒 Security

- **CORS**: Configured for local development
- **Input Validation**: All WebSocket messages validated
- **Error Handling**: Graceful degradation on failures
- **Log Sanitization**: Sensitive data filtered from logs

## 🚀 Future Enhancements

- [ ] **Multi-task Support**: Monitor multiple tasks simultaneously
- [ ] **Historical Data**: Store and display execution history
- [ ] **Alert System**: Notifications for failures and milestones
- [ ] **Export Features**: Export logs and metrics
- [ ] **Mobile App**: Native mobile dashboard
- [ ] **Plugin System**: Extensible architecture for custom visualizations

## 📝 Development

### Project Structure
```
dashboard/
├── index.html          # Main dashboard HTML
├── server.py           # WebSocket server
├── integrate.py        # Orchestrator integration
├── start_dashboard.sh  # Startup script
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

### Adding New Features
1. Modify `index.html` for UI changes
2. Update `server.py` for backend logic
3. Extend `integrate.py` for orchestrator integration
4. Test with `start_dashboard.sh`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the main project LICENSE file for details.

---

**Built with ❤️ for the Maestro Orchestrator project**