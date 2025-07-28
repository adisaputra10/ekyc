#!/bin/bash
# Script untuk menjalankan Elasticsearch v8 dengan Vector Database support

echo "🚀 Starting Elasticsearch v8 with Vector Database support..."

# Stop dan remove container yang sudah ada jika ada
echo "🧹 Cleaning up existing containers..."
docker stop ekyc-elasticsearch 2>/dev/null || true
docker rm ekyc-elasticsearch 2>/dev/null || true
docker stop ekyc-kibana 2>/dev/null || true  
docker rm ekyc-kibana 2>/dev/null || true

# Create network jika belum ada
echo "🔗 Creating Docker network..."
docker network create ekyc-network 2>/dev/null || true

# Create volume untuk data persistence
echo "💾 Creating volume for data persistence..."
docker volume create elasticsearch_data 2>/dev/null || true

# Run Elasticsearch v8 dengan vector support
echo "🔥 Starting Elasticsearch v8..."
docker run -d \
  --name ekyc-elasticsearch \
  --network ekyc-network \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "xpack.security.enrollment.enabled=false" \
  -e "xpack.security.http.ssl.enabled=false" \
  -e "xpack.security.transport.ssl.enabled=false" \
  -e "bootstrap.memory_lock=true" \
  -e "ES_JAVA_OPTS=-Xms1g -Xmx1g" \
  -e "action.destructive_requires_name=false" \
  --ulimit memlock=-1:-1 \
  -v elasticsearch_data:/usr/share/elasticsearch/data \
  elasticsearch:8.11.0

# Wait for Elasticsearch to start
echo "⏳ Waiting for Elasticsearch to start..."
sleep 30

# Check if Elasticsearch is running
echo "🔍 Checking Elasticsearch status..."
if curl -s http://localhost:9200/_cluster/health | grep -q "yellow\|green"; then
    echo "✅ Elasticsearch is running successfully!"
    echo "📊 Elasticsearch URL: http://localhost:9200"
    
    # Show cluster info
    echo "📋 Cluster Information:"
    curl -s http://localhost:9200 | jq '.' || curl -s http://localhost:9200
    
    echo ""
    echo "🎯 Vector Database Features Enabled:"
    echo "   - Dense Vector Support: ✅"
    echo "   - Cosine Similarity: ✅" 
    echo "   - KNN Search: ✅"
    echo "   - Script Score Queries: ✅"
    
else
    echo "❌ Failed to start Elasticsearch"
    echo "📝 Container logs:"
    docker logs ekyc-elasticsearch
    exit 1
fi

# Optional: Start Kibana for monitoring
read -p "🤔 Do you want to start Kibana for monitoring? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🎛️ Starting Kibana..."
    docker run -d \
      --name ekyc-kibana \
      --network ekyc-network \
      -p 5601:5601 \
      -e "ELASTICSEARCH_HOSTS=http://ekyc-elasticsearch:9200" \
      -e "xpack.security.enabled=false" \
      kibana:8.11.0
    
    echo "⏳ Waiting for Kibana to start..."
    sleep 60
    
    if curl -s http://localhost:5601/api/status | grep -q "available"; then
        echo "✅ Kibana is running!"
        echo "🌐 Kibana URL: http://localhost:5601"
    else
        echo "⚠️ Kibana might still be starting..."
        echo "🌐 Try accessing: http://localhost:5601 in a few minutes"
    fi
fi

echo ""
echo "🎉 Setup Complete!"
echo "📚 Usage:"
echo "   - Elasticsearch: http://localhost:9200"
echo "   - Kibana (if started): http://localhost:5601"
echo ""
echo "🛠️ Management Commands:"
echo "   Stop: docker stop ekyc-elasticsearch ekyc-kibana"
echo "   Start: docker start ekyc-elasticsearch ekyc-kibana"
echo "   Logs: docker logs ekyc-elasticsearch"
echo "   Remove: docker rm -f ekyc-elasticsearch ekyc-kibana"
