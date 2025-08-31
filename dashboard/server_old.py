#!/usr/bin/env python3
"""
WebSocket server for Maestro Orchestrator Dashboard.
Provides real-time status updates and monitoring.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import websockets
from websockets.server import WebSocketServerProtocol

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrchestratorMonitor:
    """Monitors the orchestrator and provides real-time updates."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.connected_clients: List[WebSocketServerProtocol] = []
        self.current_task = "demo"
        self.pipeline_status = {
            "planner": {"status": "waiting", "progress": None, "error": None},
            "coder": {"status": "waiting", "progress": None, "error": None},
            "integrator": {"status": "waiting", "progress": None, "error": None},
            "tester": {"status": "waiting", "progress": None, "error": None},
            "reporter": {"status": "waiting", "progress": None, "error": None}
        }
        self.metrics = {
            "totalTime": 0,
            "testsPassed": 0,
            "coverage": 0,
            "filesTouched": 0
        }
        self.start_time = None
        
    async def register_client(self, websocket: WebSocketServerProtocol):
        """Register a new WebSocket client."""
        self.connected_clients.append(websocket)
        logger.info(f"Client connected. Total clients: {len(self.connected_clients)}")
        
        # Send current status to new client
        await self.send_status_update(websocket)
        
    async def unregister_client(self, websocket: WebSocketServerProtocol):
        """Unregister a WebSocket client."""
        if websocket in self.connected_clients:
            self.connected_clients.remove(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.connected_clients)}")
        
    async def send_to_all_clients(self, message: dict):
        """Send message to all connected clients."""
        if not self.connected_clients:
            return
            
        message_str = json.dumps(message)
        disconnected = []
        
        for client in self.connected_clients:
            try:
                await client.send(message_str)
            except websockets.exceptions.ConnectionClosed:
                disconnected.append(client)
                
        # Remove disconnected clients
        for client in disconnected:
            await self.unregister_client(client)
            
    async def send_status_update(self, websocket: WebSocketServerProtocol = None):
        """Send current status to client(s)."""
        message = {
            "type": "status_update",
            "task": self.current_task,
            "pipeline": self.pipeline_status,
            "metrics": self.metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        if websocket:
            await websocket.send(json.dumps(message))
        else:
            await self.send_to_all_clients(message)
            
    async def update_node_status(self, node: str, status: str, progress: Optional[str] = None, error: Optional[str] = None):
        """Update status of a specific node."""
        if node in self.pipeline_status:
            self.pipeline_status[node]["status"] = status
            self.pipeline_status[node]["progress"] = progress
            self.pipeline_status[node]["error"] = error
            
            await self.send_to_all_clients({
                "type": "node_update",
                "node": node,
                "status": status,
                "progress": progress,
                "error": error,
                "timestamp": datetime.now().isoformat()
            })
            
    async def update_metrics(self, metrics: Dict):
        """Update pipeline metrics."""
        self.metrics.update(metrics)
        
        await self.send_to_all_clients({
            "type": "metrics_update",
            "metrics": self.metrics,
            "timestamp": datetime.now().isoformat()
        })
        
    async def add_log(self, level: str, message: str):
        """Add a log entry."""
        await self.send_to_all_clients({
            "type": "log",
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
    def read_log_file(self, task: str, stage: str) -> List[str]:
        """Read log file for a specific task and stage."""
        log_file = self.project_root / "logs" / f"{task}.{stage}.log"
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    return f.readlines()[-50:]  # Last 50 lines
            except Exception as e:
                logger.error(f"Error reading log file {log_file}: {e}")
        return []
        
    def get_qa_report(self, task: str) -> Optional[Dict]:
        """Get QA report for a specific task."""
        qa_file = self.project_root / "reports" / "qa.json"
        if qa_file.exists():
            try:
                with open(qa_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading QA report {qa_file}: {e}")
        return None
        
    async def monitor_orchestrator(self):
        """Monitor orchestrator files for changes and update status."""
        last_modified = {}
        
        while True:
            try:
                # Check for log files
                for stage in ["plan", "code", "integrate", "test", "report"]:
                    log_file = self.project_root / "logs" / f"{self.current_task}.{stage}.log"
                    
                    if log_file.exists():
                        current_mtime = log_file.stat().st_mtime
                        
                        if log_file not in last_modified or current_mtime > last_modified[log_file]:
                            last_modified[log_file] = current_mtime
                            
                            # Determine node status based on log content
                            logs = self.read_log_file(self.current_task, stage)
                            if logs:
                                last_log = logs[-1].strip()
                                
                                if "ERROR" in last_log:
                                    await self.update_node_status(stage, "failed", error=last_log)
                                elif "completed" in last_log.lower() or "concluído" in last_log.lower():
                                    await self.update_node_status(stage, "completed")
                                elif "starting" in last_log.lower() or "iniciando" in last_log.lower():
                                    await self.update_node_status(stage, "running", "0%")
                                    
                # Check for QA report updates
                qa_report = self.get_qa_report(self.current_task)
                if qa_report:
                    await self.update_metrics({
                        "totalTime": qa_report.get("elapsed_sec", 0),
                        "testsPassed": qa_report.get("passed", 0),
                        "coverage": qa_report.get("coverage", 0),
                        "filesTouched": len(qa_report.get("artifacts", []))
                    })
                    
            except Exception as e:
                logger.error(f"Error monitoring orchestrator: {e}")
                
            await asyncio.sleep(2)  # Check every 2 seconds


async def handle_client(websocket: WebSocketServerProtocol, path: str):
    """Handle WebSocket client connections."""
    monitor = OrchestratorMonitor()
    
    await monitor.register_client(websocket)
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                await handle_client_message(websocket, data, monitor)
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON"
                }))
            except Exception as e:
                logger.error(f"Error handling client message: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await monitor.unregister_client(websocket)


async def handle_client_message(websocket: WebSocketServerProtocol, data: dict, monitor: OrchestratorMonitor):
    """Handle messages from WebSocket clients."""
    message_type = data.get("type")
    
    if message_type == "get_status":
        await monitor.send_status_update(websocket)
        
    elif message_type == "start_pipeline":
        monitor.current_task = data.get("task", "demo")
        monitor.start_time = time.time()
        
        # Reset pipeline status
        for node in monitor.pipeline_status:
            monitor.pipeline_status[node] = {"status": "waiting", "progress": None, "error": None}
            
        await monitor.add_log("INFO", f"Starting pipeline for task: {monitor.current_task}")
        await monitor.send_to_all_clients({
            "type": "pipeline_start",
            "task": monitor.current_task,
            "timestamp": datetime.now().isoformat()
        })
        
    elif message_type == "update_task":
        monitor.current_task = data.get("task", "demo")
        await monitor.add_log("INFO", f"Switched to task: {monitor.current_task}")
        
    else:
        await websocket.send(json.dumps({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }))


async def main():
    """Main server function."""
    host = os.getenv("DASHBOARD_HOST", "localhost")
    port = int(os.getenv("DASHBOARD_PORT", "8765"))
    
    logger.info(f"Starting Maestro Dashboard server on {host}:{port}")
    
    # Start monitoring task
    monitor = OrchestratorMonitor()
    monitoring_task = asyncio.create_task(monitor.monitor_orchestrator())
    
    # Start WebSocket server
    async with websockets.serve(handle_client, host, port):
        logger.info(f"Dashboard server running on ws://{host}:{port}")
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")