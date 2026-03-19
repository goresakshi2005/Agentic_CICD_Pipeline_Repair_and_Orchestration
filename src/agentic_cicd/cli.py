import asyncio
import click
import uvicorn
from .config_loader import load_config
from .server import app
from .graph import run_workflow

@click.group()
def cli():
    """Agentic CI/CD - Autonomous pipeline repair and release orchestration."""
    pass

@cli.command()
@click.option("--config", "-c", default="config.yaml", help="Configuration file path")
@click.option("--host", default="0.0.0.0", help="Host to bind")
@click.option("--port", default=8000, help="Port to bind")
def serve(config, host, port):
    """Start the webhook server."""
    load_config(config)
    uvicorn.run(app, host=host, port=port)

@cli.command()
@click.argument("run_id")
@click.option("--config", "-c", default="config.yaml")
def analyze(run_id, config):
    """Analyze a specific workflow run immediately."""
    load_config(config)
    asyncio.run(run_workflow(int(run_id)))

@cli.command()
@click.option("--config", "-c", default="config.yaml")
def init(config):
    """Generate a sample configuration file."""
    sample = """# Agentic CI/CD configuration
vcs_provider: github
vcs_repo: yourorg/yourproject
llm_provider: gemini
slack_channel: "#deploy-approvals"
"""
    with open(config, "w") as f:
        f.write(sample)
    click.echo(f"✅ Sample configuration written to {config}")

if __name__ == "__main__":
    cli()