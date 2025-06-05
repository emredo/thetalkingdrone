from typing import Any, Dict, List

from langchain.chat_models import init_chat_model
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from src.constant.keys import GOOGLE_API_KEY
from src.models import (
    AgentNotInitializedException,
    InvalidCommandException,
)
from src.models.physical_models import BuildingInformation, Location
from src.services.simulation_drone import SimulationDroneService

SYSTEM_PROMPT = """You are an advanced drone autopilot assistant. Your purpose is to interpret natural language commands and translate them into precise drone operations. You have direct control over the drone through specialized tools.

Guidelines for operation:
1. Safety is your highest priority - evaluate commands for potential risks before execution
2. Check current state before acting - use get_telemetry to understand the drone's current status
3. Execute commands efficiently - break complex tasks into logical sequences of actions
4. Provide clear feedback about each action taken and the drone's current status
5. When navigating to coordinates, confirm the path is clear of obstacles

When executing commands, think about:
- The current state of the drone (is it FLYING, TAKING_OFF, LANDING, etc.?)
- The necessary sequence of operations (take off before moving, etc.)
- Required parameters (altitude, coordinates)
- Safety checks at each step

Use the tools to respond to user queries about the drone or to control the drone.

Current Telemetry Data: {telemetry}
"""


class AutoPilotService:
    """AutoPilot agent implementation using Gemini 2.5 Pro with LangGraph."""

    @classmethod
    def create_autopilot_service(
        cls, drone_service: SimulationDroneService
    ) -> "AutoPilotService":
        """Create an autopilot service for a drone."""
        return cls(drone_service)

    def __init__(self, drone_service: SimulationDroneService):
        """Initialize the Gemini autopilot agent."""
        from src.config.settings import Settings

        # Create the LangGraph agent using ReAct agent
        try:
            self.drone_service = drone_service
            # Set up memory
            self.memory = ConversationBufferMemory(
                memory_key="chat_history", return_messages=True
            )
            self.agent = create_react_agent(
                model=init_chat_model(
                    model=Settings.langchain_model,
                    max_tokens=1000,
                    max_retries=3,
                    temperature=0.2,
                    google_api_key=GOOGLE_API_KEY,
                ),
                tools=self._create_drone_tools(),
                prompt=self._prepare_prompt(),
            )
            self.is_initialized = True
        except Exception as e:
            raise InvalidCommandException(f"Failed to create agent: {str(e)}")

    def _prepare_prompt(self) -> str:
        """Prepare the prompt for the agent."""
        return SYSTEM_PROMPT.format(telemetry=self.drone_service.get_telemetry())

    def _create_drone_tools(self) -> List[Any]:
        """Create tools from drone service methods."""

        @tool("get_telemetry")
        def get_telemetry() -> Dict[str, Any]:
            """Get current drone telemetry including position, fuel level, speed, and state."""
            return self.drone_service.get_telemetry()

        @tool("take_off")
        def take_off() -> str:
            """Command the drone to take off."""
            try:
                self.drone_service.take_off()
                return "Drone taking off to 1 meter"
            except Exception as e:
                return f"Take off failed: {str(e)}"

        @tool("land")
        def land() -> str:
            """Command the drone to land."""
            try:
                self.drone_service.land()
                return "Drone landing"
            except Exception as e:
                return f"Landing failed: {str(e)}"

        @tool("move_to")
        def move_to(x: float, y: float, z: float) -> str:
            """Command the drone to move to a specific 3D coordinate (x, y, z)."""
            try:
                location = Location(x=x, y=y, z=z)
                self.drone_service.move_to(location)
                return f"Drone moving to location ({x}, {y}, {z})"
            except Exception as e:
                return f"Move failed: {str(e)}"

        @tool("get_buildings")
        def get_buildings() -> List[BuildingInformation]:
            """Get the list of buildings in the environment."""
            try:
                from src.controller.environment import get_environment_instance

                environment = get_environment_instance()
                return environment.features.buildings if environment else []
            except Exception as e:
                raise RuntimeError(f"Failed to get buildings: {str(e)}")

        # Return the list of tools
        return [get_telemetry, take_off, land, move_to, get_buildings]

    def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a natural language command via the LangGraph agent."""
        if not self.is_initialized:
            raise AgentNotInitializedException("Agent not initialized. Call first.")

        try:
            # Create a state with the command as a HumanMessage
            input_state = {"messages": [HumanMessage(content=command)]}

            # Execute the agent with the input state
            response = self.agent.invoke(input_state)

            return_str = ""
            ct = 0
            for message in response.get("messages", []):
                if isinstance(message, AIMessage) and message.content != "":
                    content = (
                        message.content if message.content != "" else "No response"
                    )
                    return_str += f"\n-----{ct}-----\n{content}"
                    ct += 1

            return {"status": "success", "result": return_str}
        except Exception as e:
            raise InvalidCommandException(f"Failed to execute command: {str(e)}")
