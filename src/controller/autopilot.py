from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.controller.drone import get_drone_service
from src.controller.environment import get_environment_instance
from src.models import (
    AgentNotInitializedException,
    AutopilotException,
    DroneException,
    OutOfBoundsException,
)
from src.models.physical_models import Location
from src.services.autopilot_service import AutoPilotService
from src.services.drone_base import DroneServiceBase
from src.services.environment import EnvironmentService
from src.utils.logger import logger

router = APIRouter(prefix="/autopilot", tags=["autopilot"])


class CommandInput(BaseModel):
    """Model for natural language command input."""

    command: str


class TurnRequest(BaseModel):
    """Model for turn request."""

    angle: float


def get_autopilot_service(drone_id: str) -> AutoPilotService:
    from src.controller.environment import get_environment_instance

    environment = get_environment_instance()
    if drone_id not in environment.autopilot_agents:
        raise HTTPException(
            status_code=404, detail=f"No autopilot agent found for drone {drone_id}"
        )
    return environment.autopilot_agents[drone_id]


@router.post("/{drone_id}/command/")
def execute_command(
    command_input: CommandInput,
    drone_id: str,
    environment: EnvironmentService = Depends(get_environment_instance),
):
    """Execute a natural language command via the autopilot agent."""
    if drone_id not in environment.autopilot_agents:
        raise HTTPException(
            status_code=404, detail=f"No autopilot agent found for drone {drone_id}"
        )
    agent = environment.autopilot_agents[drone_id]
    try:
        agent.execute_command(command_input.command)
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


@router.get("/{drone_id}/chat_history/")
def get_chat_history(
    drone_id: str, autopilot_service: AutoPilotService = Depends(get_autopilot_service)
) -> List[Dict[str, str]]:
    """Get the chat history for the specified drone."""
    return autopilot_service.get_chat_history()


@router.get("/{drone_id}/ham_chat_history/")
def get_ham_chat_history(
    drone_id: str, autopilot_service: AutoPilotService = Depends(get_autopilot_service)
) -> List[Dict[str, Any]]:
    """Get the ham chat history for the specified drone."""
    return [msg.model_dump() for msg in autopilot_service.memory]


@router.post("/{drone_id}/takeoff/")
def take_off(
    drone_service: DroneServiceBase = Depends(get_drone_service),
) -> Dict[str, str]:
    """Command drone to take off to the specified altitude."""
    try:
        drone_service.take_off()
        return {
            "status": "success",
            "message": "Taking off to altitude 1 meter",
        }
    except (DroneException, OutOfBoundsException) as e:
        logger.error(
            f"Takeoff failed for drone {drone_service.drone.drone_id}: {str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{drone_id}/land/")
def land(
    drone_service: DroneServiceBase = Depends(get_drone_service),
) -> Dict[str, str]:
    """Command drone to land."""
    try:
        drone_service.land()
        return {"status": "success", "message": "Landing initiated"}
    except (DroneException, OutOfBoundsException) as e:
        logger.error(
            f"Landing failed for drone {drone_service.drone.drone_id}: {str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{drone_id}/move_global/")
def move_global(
    target: Location, drone_service: DroneServiceBase = Depends(get_drone_service)
) -> Dict[str, str]:
    """Command drone to move to the specified location."""
    try:
        drone_service.move_global(target)
        return {
            "status": "success",
            "message": f"Moving to location ({target.x}, {target.y}, {target.z})",
        }
    except (DroneException, OutOfBoundsException) as e:
        logger.error(
            f"Move operation failed for drone {drone_service.drone.drone_id} to location ({target.x}, {target.y}, {target.z}): {str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{drone_id}/move_body/")
def move_body(
    target: Location, drone_service: DroneServiceBase = Depends(get_drone_service)
) -> Dict[str, str]:
    """Command drone to move to the specified location."""
    try:
        drone_service.move_body(target)
        return {
            "status": "success",
            "message": f"Moving to location ({target.x}, {target.y}, {target.z})",
        }
    except (DroneException, OutOfBoundsException) as e:
        logger.error(
            f"Move operation failed for drone {drone_service.drone.drone_id} to location ({target.x}, {target.y}, {target.z}): {str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{drone_id}/turn_global/")
def turn_global(
    request: TurnRequest,
    drone_service: DroneServiceBase = Depends(get_drone_service),
) -> Dict[str, str]:
    """Command drone to turn to the specified angle."""
    try:
        drone_service.turn_global(request.angle)
        return {"status": "success", "message": f"Turning to {request.angle} degrees"}
    except (DroneException, OutOfBoundsException) as e:
        logger.error(
            f"Turn operation failed for drone {drone_service.drone.drone_id} to angle {request.angle}: {str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{drone_id}/turn_body/")
def turn_body(
    request: TurnRequest,
    drone_service: DroneServiceBase = Depends(get_drone_service),
) -> Dict[str, str]:
    """Command drone to turn to the specified angle at body frame"""
    try:
        drone_service.turn_body(request.angle)
        return {"status": "success", "message": f"Turning to {request.angle} degrees"}
    except (DroneException, OutOfBoundsException) as e:
        logger.error(
            f"Turn operation failed for drone {drone_service.drone.drone_id} to angle {request.angle}: {str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))
