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

        # Example: Add Episodes
        # Episodes list containing both text and JSON episodes
        episodes = [
            {
                'content': 'Kamala Harris is the Attorney General of California. She was previously '
                'the district attorney for San Francisco.',
                'type': EpisodeType.text,
                'description': 'podcast transcript',
            },
            {
                'content': 'As AG, Harris was in office from January 3, 2011 – January 3, 2017',
                'type': EpisodeType.text,
                'description': 'podcast transcript',
            },
            {
                'content': {
                    'name': 'Gavin Newsom',
                    'position': 'Governor',
                    'state': 'California',
                    'previous_role': 'Lieutenant Governor',
                    'previous_location': 'San Francisco',
                },
                'type': EpisodeType.json,
                'description': 'podcast metadata',
            },
            {
                'content': {
                    'name': 'Gavin Newsom',
                    'position': 'Governor',
                    'term_start': 'January 7, 2019',
                    'term_end': 'Present',
                },
                'type': EpisodeType.json,
                'description': 'podcast metadata',
            },
        ]

        # Add episodes to the graph
        for i, episode in enumerate(episodes):
            await graphiti.add_episode(
                name=f'Freakonomics Radio {i}',
                episode_body=episode['content']
                if isinstance(episode['content'], str)
                else json.dumps(episode['content']),
                source=episode['type'],
                source_description=episode['description'],
                reference_time=datetime.now(timezone.utc),
            )
            print(f'Added episode: Freakonomics Radio {i} ({episode["type"].value})')


        #################################################
        # BASIC SEARCH
        #################################################
        # The simplest way to retrieve relationships (edges)
        # from Graphiti is using the search method, which
        # performs a hybrid search combining semantic
        # similarity and BM25 text retrieval.
        #################################################

        # Perform a hybrid search combining semantic similarity and BM25 retrieval
        print("\nSearching for: 'Who was the California Attorney General?'")
        results = await graphiti.search('Who was the California Attorney General?')

        # Print search results
        print('\nSearch Results:')
        for result in results:
            print(f'UUID: {result.uuid}')
            print(f'Fact: {result.fact}')
            if hasattr(result, 'valid_at') and result.valid_at:
                print(f'Valid from: {result.valid_at}')
            if hasattr(result, 'invalid_at') and result.invalid_at:
                print(f'Valid until: {result.invalid_at}')
            print('---')

        #################################################
        # CENTER NODE SEARCH
        #################################################
        # For more contextually relevant results, you can
        # use a center node to rerank search results based
        # on their graph distance to a specific node
        #################################################

        # Use the top search result's UUID as the center node for reranking
        if results and len(results) > 0:
            # Get the source node UUID from the top result
            center_node_uuid = results[0].source_node_uuid

            print('\nReranking search results based on graph distance:')
            print(f'Using center node UUID: {center_node_uuid}')

            reranked_results = await graphiti.search(
                'Who was the California Attorney General?', center_node_uuid=center_node_uuid
            )

            # Print reranked search results
            print('\nReranked Search Results:')
            for result in reranked_results:
                print(f'UUID: {result.uuid}')
                print(f'Fact: {result.fact}')
                if hasattr(result, 'valid_at') and result.valid_at:
                    print(f'Valid from: {result.valid_at}')
                if hasattr(result, 'invalid_at') and result.invalid_at:
                    print(f'Valid until: {result.invalid_at}')
                print('---')
        else:
            print('No results found in the initial search to use as center node.')

         #################################################
        # NODE SEARCH USING SEARCH RECIPES
        #################################################
        # Graphiti provides predefined search recipes
        # optimized for different search scenarios.
        # Here we use NODE_HYBRID_SEARCH_RRF for retrieving
        # nodes directly instead of edges.
        #################################################

        # Example: Perform a node search using _search method with standard recipes
        print(
            '\nPerforming node search using _search method with standard recipe NODE_HYBRID_SEARCH_RRF:'
        )

        # Use a predefined search configuration recipe and modify its limit
        node_search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        node_search_config.limit = 5  # Limit to 5 results

        # Execute the node search
        node_search_results = await graphiti._search(
            query='California Governor',
            config=node_search_config,
        )

        # Print node search results
        print('\nNode Search Results:')
        for node in node_search_results.nodes:
            print(f'Node UUID: {node.uuid}')
            print(f'Node Name: {node.name}')
            node_summary = node.summary[:100] + '...' if len(node.summary) > 100 else node.summary
            print(f'Content Summary: {node_summary}')
            print(f'Node Labels: {", ".join(node.labels)}')
            print(f'Created At: {node.created_at}')
            if hasattr(node, 'attributes') and node.attributes:
                print('Attributes:')
                for key, value in node.attributes.items():
                    print(f'  {key}: {value}')
            print('---')

    finally:
        #################################################
        # CLEANUP
        #################################################
        # Always close the connection to Neo4j when
        # finished to properly release resources
        #################################################

        # Close the connection
        await graphiti.close()
        print('\nConnection closed')

if __name__ == '__main__':
    asyncio.run(main())