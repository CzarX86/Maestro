"""
Dashboard server for real-time monitoring of the Maestro orchestrator.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)


class DashboardServer:
    """WebSocket server for real-time dashboard monitoring."""
    
    def __init__(self, host: str = "localhost", port: int = 8765, project_root: str = "."):
        self.host = host
        self.port = port
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
        self.doc_status: Optional[Dict] = None
        
    async def register_client(self, websocket: WebSocketServerProtocol) -> None:
        """Register a new WebSocket client."""
        self.connected_clients.append(websocket)
        logger.info(f"Client connected. Total clients: {len(self.connected_clients)}")
        
        # Send current status to new client
        await self.send_status_update(websocket)
        
    async def unregister_client(self, websocket: WebSocketServerProtocol) -> None:
        """Unregister a WebSocket client."""
        if websocket in self.connected_clients:
            self.connected_clients.remove(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.connected_clients)}")
        
    async def send_to_all_clients(self, message: Dict) -> None:
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
            
    async def send_status_update(self, websocket: Optional[WebSocketServerProtocol] = None) -> None:
        """Send current status to client(s)."""
        message = {
            "type": "status_update",
            "task": self.current_task,
            "pipeline": self.pipeline_status,
            "metrics": self.metrics,
            "doc_status": self.doc_status,
            "timestamp": datetime.now().isoformat()
        }
        
        if websocket:
            await websocket.send(json.dumps(message))
        else:
            await self.send_to_all_clients(message)
            
    async def update_node_status(self, node: str, status: str, progress: Optional[str] = None, error: Optional[str] = None) -> None:
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
            
    async def update_metrics(self, metrics: Dict) -> None:
        """Update pipeline metrics."""
        self.metrics.update(metrics)
        
        await self.send_to_all_clients({
            "type": "metrics_update",
            "metrics": self.metrics,
            "timestamp": datetime.now().isoformat()
        })
        
    async def add_log(self, level: str, message: str) -> None:
        """Add a log entry."""
        await self.send_to_all_clients({
            "type": "log",
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
    async def start_server(self) -> None:
        """Start the WebSocket server."""
        logger.info(f"Starting Maestro Dashboard server on {self.host}:{self.port}")
        
        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info(f"Dashboard server running on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever
            
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """Handle WebSocket client connections."""
        await self.register_client(websocket)
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_client_message(websocket, data)
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
            await self.unregister_client(websocket)
            
    async def handle_client_message(self, websocket: WebSocketServerProtocol, data: Dict) -> None:
        """Handle messages from WebSocket clients."""
        message_type = data.get("type")
        
        if message_type == "get_status":
            await self.send_status_update(websocket)
            
        elif message_type == "start_pipeline":
            self.current_task = data.get("task", "demo")
            
            # Reset pipeline status
            for node in self.pipeline_status:
                self.pipeline_status[node] = {"status": "waiting", "progress": None, "error": None}
                
            await self.add_log("INFO", f"Starting pipeline for task: {self.current_task}")
            await self.send_to_all_clients({
                "type": "pipeline_start",
                "task": self.current_task,
                "timestamp": datetime.now().isoformat()
            })
            
        elif message_type == "update_task":
            self.current_task = data.get("task", "demo")
            await self.add_log("INFO", f"Switched to task: {self.current_task}")
        
        elif message_type == "doc_update":
            # Store and broadcast documentation status update
            self.doc_status = {
                "task": data.get("task"),
                "status": data.get("status"),
                "passed": data.get("passed"),
                "failed": data.get("failed"),
                "coverage": data.get("coverage"),
                "lint_errors": data.get("lint_errors"),
                "type_errors": data.get("type_errors"),
                "timestamp": data.get("timestamp", datetime.now().isoformat()),
            }
            await self.send_to_all_clients({"type": "doc_update", **self.doc_status})

        else:
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            }))


def main():
    """Main entry point for the dashboard server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Maestro Dashboard Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind to")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Start server
    server = DashboardServer(args.host, args.port, args.project_root)
    
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")


if __name__ == "__main__":
    main()
