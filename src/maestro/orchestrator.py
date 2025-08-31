"""
Core orchestrator functionality for the Maestro pipeline.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class Orchestrator:
    """Main orchestrator class for managing the AI-powered development pipeline."""
    
    def __init__(self, project_root: str = ".", dashboard_url: Optional[str] = None):
        self.project_root = Path(project_root)
        self.dashboard_url = dashboard_url
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
        
    async def run_pipeline(self, task: str) -> bool:
        """Run the complete pipeline for a given task."""
        self.current_task = task
        logger.info(f"Starting pipeline for task: {task}")
        
        try:
            # Validate environment
            await self._validate_environment()
            
            # Run stages
            stages = [
                ("planner", self._run_planner),
                ("coder", self._run_coder),
                ("integrator", self._run_integrator),
                ("tester", self._run_tester),
                ("reporter", self._run_reporter)
            ]
            
            for stage_name, stage_func in stages:
                await self._run_stage(stage_name, stage_func)
                
            logger.info(f"Pipeline completed successfully for task: {task}")
            return True
            
        except Exception as e:
            logger.error(f"Pipeline failed for task {task}: {e}")
            return False
            
    async def _validate_environment(self) -> None:
        """Validate that all required tools and files are available."""
        # Check if issue exists
        issue_file = self.project_root / "issues" / f"{self.current_task}.md"
        if not issue_file.exists():
            raise FileNotFoundError(f"Issue file not found: {issue_file}")
            
        # Check if CLIs are available
        required_clis = ["gemini", "codex", "cursor"]
        for cli in required_clis:
            if not self._command_exists(cli):
                raise RuntimeError(f"Required CLI not found: {cli}")
                
        logger.info("Environment validation passed")
        
    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in the system PATH."""
        import shutil
        return shutil.which(command) is not None
        
    async def _run_stage(self, stage_name: str, stage_func) -> None:
        """Run a single pipeline stage with error handling."""
        logger.info(f"Starting stage: {stage_name}")
        
        try:
            self.pipeline_status[stage_name]["status"] = "running"
            self.pipeline_status[stage_name]["progress"] = "0%"
            
            await stage_func()
            
            self.pipeline_status[stage_name]["status"] = "completed"
            self.pipeline_status[stage_name]["progress"] = "100%"
            logger.info(f"Stage completed: {stage_name}")
            
        except Exception as e:
            self.pipeline_status[stage_name]["status"] = "failed"
            self.pipeline_status[stage_name]["error"] = str(e)
            logger.error(f"Stage failed: {stage_name} - {e}")
            raise
            
    async def _run_planner(self) -> None:
        """Run the planning stage with Gemini CLI."""
        # Simulate planning stage
        await asyncio.sleep(2)
        logger.info("Planning stage completed")
        
    async def _run_coder(self) -> None:
        """Run the code generation stage with Codex CLI."""
        # Simulate coding stage
        await asyncio.sleep(3)
        logger.info("Code generation stage completed")
        
    async def _run_integrator(self) -> None:
        """Run the integration stage with Cursor CLI."""
        # Simulate integration stage
        await asyncio.sleep(2)
        logger.info("Integration stage completed")
        
    async def _run_tester(self) -> None:
        """Run the testing stage."""
        # Simulate testing stage
        await asyncio.sleep(4)
        logger.info("Testing stage completed")
        
    async def _run_reporter(self) -> None:
        """Run the reporting stage."""
        # Simulate reporting stage
        await asyncio.sleep(1)
        logger.info("Reporting stage completed")


def main():
    """Main entry point for the orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Maestro Orchestrator")
    parser.add_argument("task", help="Task ID to execute")
    parser.add_argument("--dashboard-url", help="Dashboard WebSocket URL")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Run orchestrator
    orchestrator = Orchestrator(dashboard_url=args.dashboard_url)
    
    async def run():
        success = await orchestrator.run_pipeline(args.task)
        return 0 if success else 1
        
    return asyncio.run(run())


if __name__ == "__main__":
    exit(main())