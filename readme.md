# Knowledge base study

## How-to
### 1. neo4j docker run
```
docker run -d --publish=7474:7474 --publish=7687:7687 --env NEO4J_AUTH=neo4j/1q2w3e4r!! --name neo4j --volume=./data:/data neo4j:community-ubi9
```

#### 1.1 neo4j all query
```
MATCH (n)-[r]->(m) RETURN n, r, m
```

### 2. graphiti install
```
pip install graphiti-core
```

### 3. ollama pdf tools
```
pip install pdf2md-llm
```