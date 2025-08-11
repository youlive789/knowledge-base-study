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

    print("\n쿼리: '쿠팡 광고 플랫폼에서 입찰가를 자동으로 설정하는 상품이 있어?'")
    results = await graphiti.search('쿠팡 광고 플랫폼에서 입찰가를 자동으로 설정하는 상품이 있어?', num_results=3)
    print('\nSearch Results:')
    search_result_list = []
    for result in results:
        now_result = {}
        now_result['uuid'] = result.uuid
        now_result['fact'] = result.fact
        now_result['valid_at'] = str(result.valid_at)
        search_result_list.append(now_result)

        print(f'UUID: {result.uuid}')
        print(f'Fact: {result.fact}')
        if hasattr(result, 'valid_at') and result.valid_at:
            print(f'Valid from: {result.valid_at}')
        if hasattr(result, 'invalid_at') and result.invalid_at:
            print(f'Valid until: {result.invalid_at}')
        print('---')

    with open('coupang_ads_testing/search_results_1.json', 'w', encoding='utf-8') as f:
        json.dump(search_result_list, f, ensure_ascii=False, indent=4)


    print("\n쿼리: '캠페인 예산이 잘 소진 안되는데 어떡해야해?'")
    results = await graphiti.search('캠페인 예산이 잘 소진 안되는데 어떡해야해?' , num_results=3)
    print('\nSearch Results:')
    search_result_list = []
    for result in results:
        now_result = {}
        now_result['uuid'] = result.uuid
        now_result['fact'] = result.fact
        now_result['valid_at'] = str(result.valid_at)
        search_result_list.append(now_result)

        print(f'UUID: {result.uuid}')
        print(f'Fact: {result.fact}')
        if hasattr(result, 'valid_at') and result.valid_at:
            print(f'Valid from: {result.valid_at}')
        if hasattr(result, 'invalid_at') and result.invalid_at:
            print(f'Valid until: {result.invalid_at}')
        print('---')

    with open('coupang_ads_testing/search_results_2.json', 'w', encoding='utf-8') as f:
        json.dump(search_result_list, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    asyncio.run(main())