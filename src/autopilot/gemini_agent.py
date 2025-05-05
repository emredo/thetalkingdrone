import os
from typing import Any, Dict, List

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.base import BaseTool, StructuredTool
from langchain_google_genai import ChatGoogleGenerativeAI

from src.autopilot.agent import AutopilotAgent
from src.autopilot.exceptions import (
    AgentNotInitializedException,
    InvalidCommandException,
)
from src.drone.service import DroneService
from src.environment.models import Location


class GeminiAutopilotAgent(AutopilotAgent):
    """Autopilot agent implementation using Gemini 2.5 Pro with LangChain."""

    def __init__(self, drone_service: DroneService):
        """Initialize the Gemini autopilot agent."""
        super().__init__(drone_service)
        self.tools = []
        self.llm = None
        self.memory = None
        self.agent_executor = None

    def setup_agent(self) -> None:
        """Setup the LangChain agent with Gemini 2.5 Pro and tools for drone control."""
        # Set up Gemini
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")


        # Initialize the LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            temperature=0.2,
            convert_system_message_to_human=True,
            google_api_key=api_key,
        )

        # Create tools from drone service methods
        self.tools = self._create_drone_tools()

        # Set up memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an intelligent drone autopilot system that helps control a drone using natural language commands.
            
You have access to several drone control functions. Your job is to interpret the user's natural language request and 
execute the appropriate functions to fulfill that request.

When given a command, think through what steps need to be taken to satisfy the request, then use the appropriate tools.
Always prioritize safety - don't perform actions that could put the drone or its surroundings at risk.

Current drone state information is available through the get_telemetry tool.
            """,
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        # Create the agent
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)

        # Create the agent executor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
        )

        self.is_initialized = True

    def _create_drone_tools(self) -> List[BaseTool]:
        """Create LangChain tools from drone service methods."""
        tools = []

        # Tool for getting telemetry
        tools.append(
            StructuredTool.from_function(
                func=self.drone_service.get_telemetry,
                name="get_telemetry",
                description="Get current drone telemetry including position, fuel level, speed, and state",
            )
        )

        # Tool for takeoff
        def take_off_tool(altitude: float) -> str:
            """Command the drone to take off to the specified altitude."""
            try:
                self.drone_service.take_off(altitude)
                return f"Drone taking off to altitude {altitude}m"
            except Exception as e:
                return f"Take off failed: {str(e)}"

        tools.append(
            StructuredTool.from_function(
                func=take_off_tool,
                name="take_off",
                description="Command the drone to take off to a specified altitude in meters",
            )
        )

        # Tool for landing
        def land_tool() -> str:
            """Command the drone to land."""
            try:
                self.drone_service.land()
                return "Drone landing"
            except Exception as e:
                return f"Landing failed: {str(e)}"

        tools.append(
            StructuredTool.from_function(
                func=land_tool, name="land", description="Command the drone to land"
            )
        )

        # Tool for moving to a location
        def move_to_tool(x: float, y: float, z: float) -> str:
            """Command the drone to move to the specified location."""
            try:
                location = Location(x=x, y=y, z=z)
                self.drone_service.move_to(location)
                return f"Drone moving to location ({x}, {y}, {z})"
            except Exception as e:
                return f"Move failed: {str(e)}"

        tools.append(
            StructuredTool.from_function(
                func=move_to_tool,
                name="move_to",
                description="Command the drone to move to a specific 3D coordinate (x, y, z)",
            )
        )

        return tools

    def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a natural language command via the LangChain agent."""
        if not self.is_initialized:
            raise AgentNotInitializedException(
                "Agent not initialized. Call setup_agent() first."
            )

        try:
            result = self.agent_executor.invoke({"input": command})

            return {
                "status": "success",
                "result": result.get("output", "Command executed"),
                "raw_result": result,
            }
        except Exception as e:
            raise InvalidCommandException(f"Failed to execute command: {str(e)}")
