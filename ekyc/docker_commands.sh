# Docker Commands untuk Elasticsearch v8 dengan Vector Database Support

# 1. Basic Elasticsearch v8 dengan vector support
docker run -d \
  --name elasticsearch-rag \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "xpack.security.enrollment.enabled=false" \
  -e "xpack.security.http.ssl.enabled=false" \
  -e "xpack.security.transport.ssl.enabled=false" \
  -e "bootstrap.memory_lock=true" \
  -e "ES_JAVA_OPTS=-Xms1g -Xmx1g" \
  --ulimit memlock=-1:-1 \
  elasticsearch:8.11.0

# 2. Elasticsearch dengan persistent volume
docker run -d \
  --name elasticsearch-rag \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "xpack.security.enrollment.enabled=false" \
  -e "xpack.security.http.ssl.enabled=false" \
  -e "xpack.security.transport.ssl.enabled=false" \
  -e "bootstrap.memory_lock=true" \
  -e "ES_JAVA_OPTS=-Xms1g -Xmx1g" \
  --ulimit memlock=-1:-1 \
  -v elasticsearch_data:/usr/share/elasticsearch/data \
  elasticsearch:8.11.0

# 3. Elasticsearch dengan Kibana untuk monitoring
docker network create elastic

docker run -d \
  --name elasticsearch-rag \
  --net elastic \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "xpack.security.enrollment.enabled=false" \
  -e "xpack.security.http.ssl.enabled=false" \
  -e "xpack.security.transport.ssl.enabled=false" \
  -e "bootstrap.memory_lock=true" \
  -e "ES_JAVA_OPTS=-Xms1g -Xmx1g" \
  --ulimit memlock=-1:-1 \
  -v elasticsearch_data:/usr/share/elasticsearch/data \
  elasticsearch:8.11.0

docker run -d \
  --name kibana-rag \
  --net elastic \
  -p 5601:5601 \
  -e "ELASTICSEARCH_HOSTS=http://elasticsearch-rag:9200" \
  -e "xpack.security.enabled=false" \
  kibana:8.11.0

# 4. Test koneksi
curl -X GET "localhost:9200/_cluster/health?pretty"

# 5. Test vector index creation
curl -X PUT "localhost:9200/test-vectors" \
  -H "Content-Type: application/json" \
  -d '{
    "mappings": {
      "properties": {
        "text": {"type": "text"},
        "vector": {
          "type": "dense_vector",
          "dims": 384
        }
      }
    }
  }'

# 6. Stop dan remove containers
docker stop elasticsearch-rag kibana-rag
docker rm elasticsearch-rag kibana-rag
docker network rm elastic

# 7. Remove volumes (HATI-HATI: akan menghapus data)
docker volume rm elasticsearch_data
