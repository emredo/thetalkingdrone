# LLM Autopilot for Drone Control

This module provides natural language drone control using Gemini 2.5 Pro and LangChain tools.

## Overview

The LLM Autopilot allows you to control drones using natural language commands. It leverages Google's Gemini 2.5 Pro LLM and LangChain tools to interpret and execute commands such as "take off to 10 meters, move to coordinates (20, 30, 15), and then land".

## Setup

1. Set the Google API key as an environment variable:
   ```bash
   export GOOGLE_API_KEY="your-google-api-key"
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### API Endpoints

#### Initialize Autopilot for a Drone

```http
POST /api/autopilot/{drone_id}/initialize
```

This initializes the LLM-based autopilot for the specified drone.

#### Execute Natural Language Command

```http
POST /api/autopilot/{drone_id}/command
Content-Type: application/json

{
    "command": "take off to 20 meters, then move to coordinates (50, 60, 15), and finally land"
}
```

The LLM will interpret the command and execute the appropriate drone actions.

#### List Autopilot Agents

```http
GET /api/autopilot/list
```

Returns a list of all drones with autopilot agents and their initialization status.

## Example Commands

- "Take off to 30 meters"
- "Move to coordinates (40, 50, 20)"
- "Land the drone"
- "What is the current position and fuel level?"
- "Take off, move to coordinates (25, 35, 40), hover for a moment, and then land safely"
