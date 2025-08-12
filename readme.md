# Knowledge base study

## How-to
### 1. neo4j docker run
```
docker-compose up -d
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

### 4. data import/export
```
-- import
docker exec -it neo4j bin/cypher-shell -u neo4j -p password < import/all.cypher

-- export
CALL apoc.export.cypher.all("all.cypher", {format: "cypher-shell"})
YIELD file, batches, source, format, nodes, relationships, properties
RETURN file, nodes, relationships;
```