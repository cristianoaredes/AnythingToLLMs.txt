#!/bin/bash
# Script rápido de load testing com curl
#
# Uso: ./tests/load/quick_load_test.sh [URL] [REQUESTS]
# Exemplo: ./tests/load/quick_load_test.sh http://localhost:8000 1000

set -e

# Configuração
URL="${1:-http://localhost:8000}"
REQUESTS="${2:-100}"
CONCURRENT="${3:-10}"

echo "🚀 Load Test Rápido"
echo "================================"
echo "URL: $URL"
echo "Requisições: $REQUESTS"
echo "Concorrentes: $CONCURRENT"
echo "================================"
echo ""

# Verificar se servidor está up
echo "1️⃣  Verificando se servidor está online..."
if curl -f -s "$URL/health" > /dev/null; then
    echo "✅ Servidor online"
else
    echo "❌ Servidor offline ou inacessível"
    exit 1
fi

# Criar arquivo temporário para resultados
TEMP_FILE=$(mktemp)
trap "rm -f $TEMP_FILE" EXIT

# Função para fazer requisições
make_requests() {
    local endpoint="$1"
    local name="$2"
    local count="${3:-10}"

    echo ""
    echo "2️⃣  Testando: $name ($count requisições)"

    start_time=$(date +%s.%N)

    # Fazer requisições em paralelo
    for i in $(seq 1 $count); do
        (
            response_time=$(curl -w "%{time_total}" -o /dev/null -s "$URL$endpoint")
            echo "$response_time" >> "$TEMP_FILE"
        ) &

        # Limitar concorrência
        if (( i % CONCURRENT == 0 )); then
            wait
        fi
    done
    wait

    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc)

    # Calcular estatísticas
    total_time=$(awk '{sum+=$1} END {print sum}' "$TEMP_FILE")
    avg_time=$(echo "scale=3; $total_time / $count" | bc)
    rps=$(echo "scale=2; $count / $duration" | bc)

    echo "   ⏱️  Tempo total: ${duration}s"
    echo "   📊 Tempo médio: ${avg_time}s"
    echo "   🚄 RPS: $rps req/s"

    # Limpar arquivo temp
    > "$TEMP_FILE"
}

# Testes
make_requests "/health" "Health Check" "$REQUESTS"
make_requests "/metrics" "Metrics" $(( REQUESTS / 10 ))
make_requests "/" "Root Endpoint" $(( REQUESTS / 5 ))

echo ""
echo "✅ Load test concluído!"
echo ""
echo "💡 Para testes mais detalhados, use Locust:"
echo "   locust -f tests/load/locustfile.py --host=$URL"
