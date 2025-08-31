#!/usr/bin/env python3
"""
Demo script to showcase the Maestro Dashboard.
Simulates orchestrator execution with realistic timing and updates.
"""

import asyncio
import json
import random
import time
from datetime import datetime
from typing import Dict

import websockets
from websockets.client import WebSocketClientProtocol


class DashboardDemo:
    """Demo class to simulate orchestrator execution for dashboard showcase."""
    
    def __init__(self, dashboard_url: str = "ws://localhost:8765"):
        self.dashboard_url = dashboard_url
        self.websocket: WebSocketClientProtocol = None
        self.current_task = "demo"
        
    async def connect(self):
        """Connect to the dashboard WebSocket server."""
        try:
            self.websocket = await websockets.connect(self.dashboard_url)
            print("✅ Connected to dashboard")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to dashboard: {e}")
            return False
            
    async def disconnect(self):
        """Disconnect from the dashboard."""
        if self.websocket:
            await self.websocket.close()
            print("🔌 Disconnected from dashboard")
            
    async def send_message(self, message: Dict):
        """Send message to dashboard."""
        if self.websocket:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                print(f"❌ Failed to send message: {e}")
                
    async def simulate_pipeline_execution(self):
        """Simulate a complete pipeline execution with realistic timing."""
        print("🎭 Starting Maestro Dashboard Demo...")
        
        # Pipeline stages with realistic timing
        stages = [
            ("planner", "Planning with Gemini CLI", 8, 15),
            ("coder", "Code generation with Codex CLI", 12, 25),
            ("integrator", "Integration with Cursor CLI", 6, 12),
            ("tester", "Testing and QA validation", 10, 20),
            ("reporter", "Generating QA report", 3, 8)
        ]
        
        # Notify pipeline start
        await self.send_message({
            "type": "pipeline_start",
            "task": self.current_task,
            "timestamp": datetime.now().isoformat()
        })
        
        print(f"🚀 Starting pipeline for task: {self.current_task}")
        
        total_start_time = time.time()
        
        for stage_name, description, min_time, max_time in stages:
            await self.simulate_stage(stage_name, description, min_time, max_time)
            
        total_time = int(time.time() - total_start_time)
        
        # Send final metrics
        await self.send_message({
            "type": "metrics_update",
            "metrics": {
                "totalTime": total_time,
                "testsPassed": random.randint(15, 25),
                "coverage": random.randint(75, 95),
                "filesTouched": random.randint(3, 8)
            },
            "timestamp": datetime.now().isoformat()
        })
        
        # Notify pipeline completion
        await self.send_message({
            "type": "pipeline_complete",
            "task": self.current_task,
            "success": True,
            "timestamp": datetime.now().isoformat()
        })
        
        print(f"✅ Pipeline completed successfully in {total_time}s")
        
    async def simulate_stage(self, stage_name: str, description: str, min_time: int, max_time: int):
        """Simulate execution of a single stage."""
        print(f"🔄 Starting {stage_name}: {description}")
        
        # Stage start
        await self.send_message({
            "type": "stage_start",
            "stage": stage_name,
            "task": self.current_task,
            "timestamp": datetime.now().isoformat()
        })
        
        # Simulate progress updates
        execution_time = random.randint(min_time, max_time)
        progress_steps = [0, 25, 50, 75, 100]
        
        for i, progress in enumerate(progress_steps):
            if i < len(progress_steps) - 1:
                # Send progress update
                await self.send_message({
                    "type": "stage_progress",
                    "stage": stage_name,
                    "progress": f"{progress}%",
                    "timestamp": datetime.now().isoformat()
                })
                
                # Simulate work
                await asyncio.sleep(execution_time / len(progress_steps))
                
                # Add some log messages
                if random.random() < 0.3:  # 30% chance of log message
                    log_messages = [
                        f"Processing {description.lower()}...",
                        f"Validating {stage_name} outputs...",
                        f"Checking {stage_name} dependencies...",
                        f"Optimizing {stage_name} performance..."
                    ]
                    await self.send_message({
                        "type": "log",
                        "level": "INFO",
                        "message": random.choice(log_messages),
                        "timestamp": datetime.now().isoformat()
                    })
        
        # Stage completion
        success = random.random() > 0.1  # 90% success rate
        
        await self.send_message({
            "type": "stage_complete",
            "stage": stage_name,
            "status": "completed" if success else "failed",
            "error": None if success else f"Simulated error in {stage_name}",
            "timestamp": datetime.now().isoformat()
        })
        
        if success:
            print(f"✅ {stage_name} completed successfully")
        else:
            print(f"❌ {stage_name} failed")
            
    async def run_demo(self):
        """Run the complete demo."""
        if not await self.connect():
            print("❌ Cannot run demo without dashboard connection")
            return
            
        try:
            await self.simulate_pipeline_execution()
            
            # Wait a bit to show final state
            print("⏳ Showing final state for 5 seconds...")
            await asyncio.sleep(5)
            
        except KeyboardInterrupt:
            print("\n🛑 Demo stopped by user")
        except Exception as e:
            print(f"❌ Demo error: {e}")
        finally:
            await self.disconnect()


async def main():
    """Main demo function."""
    print("🎭 Maestro Dashboard Demo")
    print("=" * 50)
    print("This demo will simulate a complete orchestrator pipeline")
    print("Make sure the dashboard is running on http://localhost:8080")
    print("=" * 50)
    
    # Wait for user confirmation
    try:
        input("Press Enter to start the demo...")
    except KeyboardInterrupt:
        print("\n👋 Demo cancelled")
        return
        
    demo = DashboardDemo()
    await demo.run_demo()
    
    print("\n🎉 Demo completed!")
    print("Check the dashboard at http://localhost:8080 to see the results")


if __name__ == "__main__":
    asyncio.run(main())