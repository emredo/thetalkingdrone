from typing import Any, Dict, List

from langchain.chat_models import init_chat_model
from langchain.prompts import PromptTemplate
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from src.constant.keys import GOOGLE_API_KEY
from src.models import (
    AgentNotInitializedException,
    InvalidCommandException,
)
from src.models.physical_models import BuildingInformation, Location
from src.services.drone_base import DroneServiceBase

SYSTEM_PROMPT = """You are an intelligent drone autopilot agent designed to interpret natural language commands and execute precise drone operations in a simulated environment. You have complete control over a simulation drone through a comprehensive set of specialized tools.

## YOUR MISSION
You serve as the bridge between human operators and drone hardware, translating conversational commands into safe, efficient flight operations. Your responses should be professional, informative, and always prioritize safety.

## AVAILABLE CAPABILITIES
You have access to the following drone control tools:

1. **get_telemetry()** - Retrieve real-time drone status including:
   - Current 3D position (x, y, z coordinates)
   - Flight state (GROUNDED, TAKING_OFF, FLYING, LANDING, etc.)
   - Fuel/battery level
   - Speed and velocity vectors
   - System health indicators

2. **take_off()** - Command drone to launch from ground to 1-meter altitude
   - Only works when drone is GROUNDED
   - Automatically sets altitude to 1 meter for safety

3. **land()** - Command drone to descend and land at current location
   - Can be executed from any flying state
   - Drone will automatically navigate to ground level

4. **move_to(x, y, z)** - Navigate drone to specific 3D coordinates
   - Requires drone to be in FLYING state (take off first if grounded)
   - Parameters: x (east-west), y (north-south), z (altitude in meters)
   - Always validate coordinates are reasonable and safe

5. **get_buildings()** - Query environment for building information
   - Returns list of all structures with positions and dimensions
   - Use this for obstacle avoidance and navigation planning

## OPERATIONAL PROTOCOLS

**Safety First:**
- Always check current telemetry before executing movement commands
- Ensure drone is in appropriate state for requested operation
- Validate coordinates are within safe operational boundaries
- Consider obstacle avoidance using building information

**Command Execution Sequence:**
1. Assess current drone state via telemetry
2. Determine required sequence of operations
3. Execute commands in logical order (e.g., take off before movement)
4. Provide clear status updates after each action
5. Confirm successful completion or report any issues

**Response Guidelines:**
- Be conversational but professional
- Explain what you're doing and why
- Report current status after actions
- If commands fail, explain the issue and suggest alternatives
- For complex operations, break them into clear steps

## CURRENT STATUS
{telemetry}

## BUILDINGS
{buildings}
"""


class AutoPilotService:
    """AutoPilot agent implementation using Gemini 2.5 Pro with LangGraph."""

    @classmethod
    def create_autopilot_service(
        cls, drone_service: DroneServiceBase
    ) -> "AutoPilotService":
        """Create an autopilot service for a drone."""
        return cls(drone_service)

    def __init__(self, drone_service: DroneServiceBase):
        """Initialize the Gemini autopilot agent."""
        from src.config.settings import Settings

        # Create the LangGraph agent using ReAct agent
        try:
            self.drone_service = drone_service
            # Set up memory
            self.memory: List[BaseMessage] = []
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

    def _create_chat_history(self) -> str:
        """Create the chat history."""
        chat_history = ""
        for message in self.memory:
            if isinstance(message, HumanMessage):
                chat_history += f"Human: {message.content}\n"
            elif (
                isinstance(message, AIMessage)
                and message.content != ""
                and message.tool_calls is None
            ):
                chat_history += f"AI: {message.content}\n"
        return chat_history

    def _prepare_prompt(self) -> str:
        """Prepare the prompt for the agent."""
        prompt = PromptTemplate(
            template=SYSTEM_PROMPT,
            input_variables=["telemetry", "buildings"],
        )
        buildings: List[BuildingInformation] = (
            self.drone_service.environment.features.buildings
        )
        buildings_str = "\n".join(
            [str(building.model_dump()) for building in buildings]
        )
        # chat_history = self._create_chat_history()
        prepared_prompt = prompt.format(
            telemetry=self.drone_service.get_telemetry(),
            buildings=buildings_str,
        )

        return prepared_prompt

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

        @tool("turn")
        def turn(angle: float) -> str:
            """Command the drone to turn at yawin a specific angle."""
            try:
                self.drone_service.turn(angle)
                return f"Drone turning {angle} degrees"
            except Exception as e:
                return f"Turn failed: {str(e)}"

        # Return the list of tools
        return [turn, get_telemetry, take_off, land, move_to, turn]

    def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a natural language command via the LangGraph agent."""
        if not self.is_initialized:
            raise AgentNotInitializedException("Agent not initialized. Call first.")

        try:
            # Create a state with the command as a HumanMessage
            self.memory.append(HumanMessage(content=command))
            # Execute the agent with the input state
            response = self.agent.invoke({"messages": self.memory})
            self.memory = response.get("messages", [])
            return {"status": "success", "result": self.memory[-1].content}
        except Exception as e:
            raise InvalidCommandException(f"Failed to execute command: {str(e)}")
