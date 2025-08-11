import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from logging import INFO
from dotenv import load_dotenv
from graphiti_core import Graphiti
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.openai_client import OpenAIClient
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
from graphiti_core.nodes import EpisodeType
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF

from pathlib import Path

logging.basicConfig(
    level=INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

neo4j_uri = 'bolt://localhost:7687'
neo4j_user = 'neo4j'
neo4j_password = '1q2w3e4r!!'

# Configure Ollama LLM client
llm_config = LLMConfig(
    api_key="abc",  # Ollama doesn't require a real API key
    model="gemma3:4b",
    small_model="gemma3:4b",
    base_url="http://localhost:11434/v1",  # Ollama provides this port
)

llm_client = OpenAIClient(config=llm_config)

async def main():
    graphiti = Graphiti(
        uri=neo4j_uri,
        user=neo4j_user,
        password=neo4j_password,
        llm_client=llm_client,
        embedder=OpenAIEmbedder(
        config=OpenAIEmbedderConfig(
                api_key="abc",
                embedding_model="nomic-embed-text",
                embedding_dim=768,
                base_url="http://localhost:11434/v1",
            ),      
        ),
        cross_encoder=OpenAIRerankerClient(client=llm_client, config=llm_config),
    )

    try:
        await graphiti.build_indices_and_constraints()

        episodes = [
            {
                'content': Path('markdown/1.md').read_text(encoding='utf-8'),
                'type': EpisodeType.text,
                'description': '쿠팡 광고 소개',
            },
             {
                'content': Path('markdown/2.md').read_text(encoding='utf-8'),
                'type': EpisodeType.text,
                'description': '매출 최적화 광고 세팅하기',
            },
             {
                'content': Path('markdown/3.md').read_text(encoding='utf-8'),
                'type': EpisodeType.text,
                'description': 'AI 스마트 광고 세팅하기',
            },
        ]

        for i, episode in enumerate(episodes):
            print(i, episode['description'])
            await graphiti.add_episode(
                name=f'쿠팡 Ads {i}',
                episode_body=episode['content'].strip(),
                source=episode['type'],
                source_description=episode['description'],
                reference_time=datetime.now(timezone.utc),
            )
            print(f'Added episode: 쿠팡 Ads {i} ({episode["type"].value})')

    except Exception as e:
        logger.error(f"Error: {e}")
        return
    finally:
        await graphiti.close()

if __name__ == '__main__':
    asyncio.run(main())