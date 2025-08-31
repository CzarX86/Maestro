#!/usr/bin/env python3
"""
Integration script to connect the dashboard with the orchestrator.
Monitors orchestrator execution and sends updates to the dashboard.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import websockets
from websockets.client import WebSocketClientProtocol

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrchestratorIntegration:
    """Integrates orchestrator execution with dashboard monitoring."""
    
    def __init__(self, dashboard_url: str = "ws://localhost:8765", project_root: str = "."):
        self.dashboard_url = dashboard_url
        self.project_root = Path(project_root)
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.current_task = "demo"
        self.is_connected = False
        
    async def connect(self):
        """Connect to the dashboard WebSocket server."""
        try:
            self.websocket = await websockets.connect(self.dashboard_url)
            self.is_connected = True
            logger.info(f"Connected to dashboard at {self.dashboard_url}")
            
            # Send initial status
            await self.send_message({
                "type": "update_task",
                "task": self.current_task
            })
            
        except Exception as e:
            logger.error(f"Failed to connect to dashboard: {e}")
            self.is_connected = False
            
    async def disconnect(self):
        """Disconnect from the dashboard."""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("Disconnected from dashboard")
            
    async def send_message(self, message: dict):
        """Send message to dashboard."""
        if self.websocket and self.is_connected:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to dashboard: {e}")
                self.is_connected = False
                
    async def notify_stage_start(self, stage: str, task: str):
        """Notify dashboard that a stage has started."""
        await self.send_message({
            "type": "stage_start",
            "stage": stage,
            "task": task,
            "timestamp": datetime.now().isoformat()
        })
        
    async def notify_stage_progress(self, stage: str, progress: str):
        """Notify dashboard of stage progress."""
        await self.send_message({
            "type": "stage_progress",
            "stage": stage,
            "progress": progress,
            "timestamp": datetime.now().isoformat()
        })
        
    async def notify_stage_complete(self, stage: str, success: bool, error: Optional[str] = None):
        """Notify dashboard that a stage has completed."""
        status = "completed" if success else "failed"
        await self.send_message({
            "type": "stage_complete",
            "stage": stage,
            "status": status,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        
    async def notify_pipeline_start(self, task: str):
        """Notify dashboard that pipeline has started."""
        self.current_task = task
        await self.send_message({
            "type": "pipeline_start",
            "task": task,
            "timestamp": datetime.now().isoformat()
        })
        
    async def notify_pipeline_complete(self, task: str, success: bool):
        """Notify dashboard that pipeline has completed."""
        await self.send_message({
            "type": "pipeline_complete",
            "task": task,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
        
    async def send_metrics(self, metrics: Dict):
        """Send metrics to dashboard."""
        await self.send_message({
            "type": "metrics_update",
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        })
        
    async def send_log(self, level: str, message: str):
        """Send log message to dashboard."""
        await self.send_message({
            "type": "log",
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })


class OrchestratorWrapper:
    """Wrapper around the orchestrator to provide dashboard integration."""
    
    def __init__(self, integration: OrchestratorIntegration):
        self.integration = integration
        
    async def run_orchestrator(self, task: str):
        """Run the orchestrator with dashboard integration."""
        try:
            # Notify pipeline start
            await self.integration.notify_pipeline_start(task)
            await self.integration.send_log("INFO", f"Starting orchestrator for task: {task}")
            
            # Import and run orchestrator stages
            stages = [
                ("planner", "plan"),
                ("coder", "code"), 
                ("integrator", "integrate"),
                ("tester", "test"),
                ("reporter", "report")
            ]
            
            for stage_name, stage_command in stages:
                await self.run_stage(stage_name, stage_command, task)
                
            # Notify pipeline completion
            await self.integration.notify_pipeline_complete(task, True)
            await self.integration.send_log("SUCCESS", f"Pipeline completed for task: {task}")
            
        except Exception as e:
            await self.integration.notify_pipeline_complete(task, False)
            await self.integration.send_log("ERROR", f"Pipeline failed for task {task}: {e}")
            raise
            
    async def run_stage(self, stage_name: str, stage_command: str, task: str):
        """Run a single stage with dashboard integration."""
        try:
            # Notify stage start
            await self.integration.notify_stage_start(stage_name, task)
            await self.integration.send_log("INFO", f"Starting {stage_name} stage")
            
            # Simulate stage execution with progress updates
            for progress in ["0%", "25%", "50%", "75%", "100%"]:
                await self.integration.notify_stage_progress(stage_name, progress)
                await asyncio.sleep(1)  # Simulate work
                
            # Notify stage completion
            await self.integration.notify_stage_complete(stage_name, True)
            await self.integration.send_log("SUCCESS", f"{stage_name} stage completed")
            
        except Exception as e:
            await self.integration.notify_stage_complete(stage_name, False, str(e))
            await self.integration.send_log("ERROR", f"{stage_name} stage failed: {e}")
            raise


async def main():
    """Main function to run the integrated orchestrator."""
    integration = OrchestratorIntegration()
    
    try:
        # Connect to dashboard
        await integration.connect()
        
        if not integration.is_connected:
            logger.error("Failed to connect to dashboard. Running without integration.")
            return
            
        # Create orchestrator wrapper
        orchestrator = OrchestratorWrapper(integration)
        
        # Get task from command line or use default
        task = os.getenv("TASK", "demo")
        
        # Run orchestrator with dashboard integration
        await orchestrator.run_orchestrator(task)
        
    except KeyboardInterrupt:
        logger.info("Orchestrator stopped by user")
    except Exception as e:
        logger.error(f"Orchestrator error: {e}")
    finally:
        await integration.disconnect()


if __name__ == "__main__":
    asyncio.run(main())