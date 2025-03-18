#!/usr/bin/env python
"""Run script for development."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "thetalkingdrone.app:create_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        factory=True,
    ) 