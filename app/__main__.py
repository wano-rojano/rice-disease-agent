import logging
import os
import sys

import click
import httpx
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
)
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from dotenv import load_dotenv

from app.agent import Agent
from app.agent_executor import GeneralAgentExecutor

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MissingAPIKeyError(Exception):
    """Exception for missing API key."""

@click.command()
@click.option('--host', 'host', default='0.0.0.0')
@click.option('--port', 'port', default=int(os.environ.get('PORT', 10000)))
def main(host, port):
    """Starts the Rice Disease Agent server with A2A protocol support."""
    try:
        if not os.getenv('OPENAI_API_KEY'):
            raise MissingAPIKeyError(
                'OPENAI_API_KEY environment variable not set.'
            )

        logger.info(f"Starting Rice Disease Agent server on {host}:{port}")

        # Configure agent capabilities and skills
        capabilities = AgentCapabilities(
            streaming=True, 
            push_notifications=True,
            text_input=True,
            file_upload=False,
            web_browsing=True,
            data_analysis=False
        )
        
        skills = [
            AgentSkill(
                id='disease_diagnosis',
                name='Rice Disease Diagnosis',
                description='Diagnose rice diseases from symptoms and conditions',
                tags=['agriculture', 'pathology', 'diagnosis'],
                examples=['My rice plants have brown spots on leaves, what disease is this?'],
            ),
            AgentSkill(
                id='ipm_recommendations',
                name='Integrated Pest Management',
                description='Provide integrated pest management strategies for rice',
                tags=['agronomy', 'ipm', 'management'],
                examples=['What IPM strategy should I use for rice blast disease?'],
            ),
            AgentSkill(
                id='scientific_research',
                name='Agricultural Research',
                description='Access scientific literature and research papers on rice diseases',
                tags=['research', 'literature', 'academic'],
                examples=['Find recent research on rice disease resistance breeding'],
            ),
        ]

        agent_card = AgentCard(
            name='Rice Disease Agent',
            description='AI assistant for rice disease diagnosis and integrated pest management',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            defaultInputModes=['text'],
            defaultOutputModes=['text'],
            capabilities=capabilities,
            skills=skills,
        )

        # Create required components following the working pattern
        httpx_client = httpx.AsyncClient()
        push_config_store = InMemoryPushNotificationConfigStore()
        push_sender = BasePushNotificationSender(
            httpx_client=httpx_client,
            config_store=push_config_store
        )
        
        request_handler = DefaultRequestHandler(
            agent_executor=GeneralAgentExecutor(),
            task_store=InMemoryTaskStore(),
            push_config_store=push_config_store,
            push_sender=push_sender
        )
        
        server = A2AStarletteApplication(
            agent_card=agent_card, 
            http_handler=request_handler
        )

        # Build and run the server
        uvicorn.run(server.build(), host=host, port=port)

    except MissingAPIKeyError as e:
        logger.error(f'Error: {e}')
        sys.exit(1)
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()