"""Command-line interface for the Talking Drone."""

import uvicorn
import typer

from thetalkingdrone.app import create_app

app = typer.Typer()


@app.command()
def serve(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
):
    """Run the API server."""
    uvicorn.run(
        "thetalkingdrone.app:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
    )


def main():
    """Run the CLI application."""
    app() 