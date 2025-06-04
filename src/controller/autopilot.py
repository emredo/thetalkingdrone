from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.autopilot.agent import AutoPilotAgent
from src.controller.drone import get_drone_service
from src.services.drone import DroneService
from src.models import AgentNotInitializedException, AutopilotException
from src.utils.logger import logger

router = APIRouter(prefix="/autopilot", tags=["autopilot"])

# In-memory store for autopilot agents
_autopilot_agents: Dict[str, AutoPilotAgent] = {}


class CommandInput(BaseModel):
    """Model for natural language command input."""

    command: str


def get_autopilot_agent(drone_id: str) -> AutoPilotAgent:
    """Dependency to get autopilot agent for a specific drone."""
    if drone_id not in _autopilot_agents:
        raise HTTPException(
            status_code=404, detail=f"No autopilot agent found for drone {drone_id}"
        )
    return _autopilot_agents[drone_id]


@router.post("/{drone_id}/initialize")
def initialize_autopilot(
    drone_service: DroneService = Depends(get_drone_service),
) -> Dict[str, str]:
    """Initialize autopilot agent for a drone."""
    drone_id = drone_service.drone.drone_id

    # Check if agent already exists
    if drone_id in _autopilot_agents:
        return {
            "status": "success",
            "message": f"Autopilot agent already initialized for drone {drone_id}",
        }

    # Create and initialize the agent
    try:
        agent = AutoPilotAgent(drone_service)
        agent.setup_agent()
        _autopilot_agents[drone_id] = agent

        return {
            "status": "success",
            "message": f"Autopilot agent initialized for drone {drone_id}",
        }
    except Exception as e:
        logger.error(
            f"Failed to initialize autopilot agent for drone {drone_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to initialize autopilot agent: {str(e)}"
        )


@router.post("/{drone_id}/command")
def execute_command(
    command_input: CommandInput,
    drone_id: str,
    agent: AutoPilotAgent = Depends(get_autopilot_agent),
) -> Dict[str, Any]:
    """Execute a natural language command via the autopilot agent."""
    try:
        result = agent.execute_command(command_input.command)
        return result
    except AgentNotInitializedException:
        logger.error(f"Autopilot agent for drone {drone_id} not initialized")
        raise HTTPException(
            status_code=400,
            detail="Autopilot agent not initialized. Initialize it first.",
        )
    except AutopilotException as e:
        logger.error(
            f"Autopilot error for drone {drone_id}: {str(e)} - Command: {command_input.command}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"Unexpected error executing command for drone {drone_id}: {str(e)} - Command: {command_input.command}"
        )
        raise HTTPException(
            status_code=500, detail=f"Error executing command: {str(e)}"
        )


@router.get("/list")
def list_autopilot_agents() -> Dict[str, bool]:
    """List all drones with autopilot agents and their initialization status."""
    return {
        drone_id: agent.is_initialized for drone_id, agent in _autopilot_agents.items()
    }
