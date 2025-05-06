from typing import Any, Dict, List

from langchain.memory import ConversationBufferMemory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from src.config.llm_config import get_llm_object
from src.drone.service import DroneService
from src.environment.models import Location, Obstacle

from .exceptions import AgentNotInitializedException, InvalidCommandException


class AutoPilotAgent:
    """AutoPilot agent implementation using Gemini 2.5 Pro with LangGraph."""

    def __init__(self, drone_service: DroneService):
        """Initialize the Gemini autopilot agent."""
        self.drone_service = drone_service
        self.tools = []
        self.llm = None
        self.memory = None
        self.agent = None
        self.is_initialized = False

    def setup_agent(self) -> None:
        """Setup the LangGraph agent with Gemini 2.5 Pro and tools for drone control."""

        # Initialize the LLM
        self.llm = get_llm_object()

        # Create tools from drone service methods
        self.tools = self._create_drone_tools()

        # Set up memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )

        # Create system message
        system_message = """You are an advanced drone autopilot assistant powered by Gemini 2.5 Pro.

Your purpose is to interpret natural language commands and translate them into precise drone operations. You have direct control over the drone through specialized tools.

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
"""

        # Create the LangGraph agent using ReAct agent
        try:
            self.agent = create_react_agent(
                model=self.llm, tools=self.tools, state_modifier=system_message
            )
            self.is_initialized = True
        except Exception as e:
            raise InvalidCommandException(f"Failed to create agent: {str(e)}")

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
        def get_buildings() -> List[Obstacle]:
            """Get the list of buildings in the environment."""
            try:
                buildings = []
                for obstacle in self.drone_service.get_obstacles():
                    buildings.append(obstacle)
                return buildings
            except Exception as e:
                return f"Failed to get buildings: {str(e)}"

        # Return the list of tools
        return [get_telemetry, take_off, land, move_to, get_buildings]

    def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a natural language command via the LangGraph agent."""
        if not self.is_initialized:
            raise AgentNotInitializedException(
                "Agent not initialized. Call setup_agent() first."
            )

        try:
            # Create a state with the command as a HumanMessage
            input_state = {"messages": [HumanMessage(content=command)]}

            # Execute the agent with the input state
            response = self.agent.invoke(input_state)

            return_str = ""
            for message in response.get("messages", []):
                if isinstance(message, AIMessage):
                    return_str += f"\n-----------\n{message.content}"

            return {"status": "success", "result": return_str}
        except Exception as e:
            raise InvalidCommandException(f"Failed to execute command: {str(e)}")
