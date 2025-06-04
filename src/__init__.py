"""The FastAPI application for the Talking Drone."""

import time
import traceback

import typer
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.config.settings import Settings
from src.controller.autopilot import router as autopilot_router
from src.controller.drone import router as drone_router
from src.controller.environment import router as environment_router
from src.controller.environment import set_environment_instance
from src.services.environment import EnvironmentService
from src.utils.logger import log_endpoint_error, logger
from src.utils.simulation_monitor import get_simulation_monitor


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=Settings.app_name,
        description="API for the Talking Drone simulation",
        version="0.1.0",
        debug=Settings.debug,
    )

    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log information about API requests."""
        # Get request details
        endpoint = f"{request.method} {request.url.path}"
        start_time = time.time()

        # Log the request
        logger.info(f"REQUEST: {endpoint}")

        # Process the request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log response information
        logger.info(
            f"RESPONSE: {endpoint} - Status {response.status_code} - Took {process_time:.3f}s"
        )

        return response

    # Add exception handlers for logging errors
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Log HTTP exceptions with details."""
        endpoint = f"{request.method} {request.url.path}"
        detail = {
            "status_code": exc.status_code,
            "headers": dict(request.headers),
            "path_params": request.path_params,
            "query_params": dict(request.query_params)
            if request.query_params
            else None,
        }
        log_endpoint_error(error=exc, endpoint=endpoint, detail=detail)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Log validation errors with details."""
        endpoint = f"{request.method} {request.url.path}"
        detail = {
            "errors": exc.errors(),
            "body": exc.body,
            "headers": dict(request.headers),
        }
        log_endpoint_error(error=exc, endpoint=endpoint, detail=detail)
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Log unhandled exceptions from the application."""
        endpoint = f"{request.method} {request.url.path}"
        error_msg = f"\n--- UNHANDLED EXCEPTION: {endpoint} ---\n"
        error_msg += f"Exception Type: {type(exc).__name__}\n"
        error_msg += f"Exception Message: {str(exc)}\n"
        error_msg += f"Stack Trace:\n{traceback.format_exc()}\n"
        error_msg += "-----------------------------------"

        # Log the error with high visibility
        logger.error(error_msg)

        # Return a generic error message to the client
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected error occurred. Please check the logs for details."
            },
        )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create a global environment instance
    environment = EnvironmentService()

    # Start the simulation monitor to log simulation time every 10 seconds
    simulation_monitor = get_simulation_monitor(environment)
    simulation_monitor.start()

    # Set the environment instance for the API
    set_environment_instance(environment)

    # Include router for drone endpoints
    app.include_router(drone_router)

    # Include router for environment endpoints
    app.include_router(environment_router)

    # Include router for autopilot endpoints
    app.include_router(autopilot_router)

    # Mount static files
    app.mount("/viz", StaticFiles(directory="static", html=True), name="viz")

    # Add root endpoint
    @app.get("/")
    def read_root():
        return {
            "app_name": Settings.app_name,
            "version": "0.1.0",
            "api_docs": "/docs",
            "visualization": "/viz",
        }

    return app


app = typer.Typer()


@app.command()
def serve(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
):
    """Run the API server."""
    uvicorn.run(
        "src:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
    )


def main():
    """Run the CLI application."""
    app()
