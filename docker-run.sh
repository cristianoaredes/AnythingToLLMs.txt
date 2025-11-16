#!/bin/bash
set -e

# ========================================
# Anything to LLMs.txt - Docker Run Script
# ========================================
# Script simplificado para rodar a aplicação no Docker

# Cores
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
RESET='\033[0m'

echo -e "${GREEN}========================================${RESET}"
echo -e "${GREEN}Anything to LLMs.txt - Docker Setup${RESET}"
echo -e "${GREEN}========================================${RESET}"
echo ""

# Verificar se .env existe
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ Arquivo .env não encontrado!${RESET}"
    echo -e "${YELLOW}Criando .env a partir de .env.example...${RESET}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env criado!${RESET}"
    echo ""
    echo -e "${RED}IMPORTANTE:${RESET}"
    echo -e "  Edite o arquivo .env e configure:"
    echo -e "  - LLMS_API_KEY (obrigatório para produção)"
    echo -e "  - CORS_ORIGINS (seus domínios permitidos)"
    echo ""
    read -p "Pressione ENTER para continuar (ou Ctrl+C para sair e editar .env)..."
fi

# Verificar se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker não está rodando!${RESET}"
    echo -e "  Inicie o Docker Desktop/Engine e tente novamente."
    exit 1
fi

echo -e "${GREEN}✓ Docker está rodando${RESET}"
echo ""

# Perguntar modo de execução
echo -e "${YELLOW}Escolha o modo:${RESET}"
echo "  1) Produção (recomendado)"
echo "  2) Desenvolvimento (hot-reload)"
read -p "Opção [1]: " MODE
MODE=${MODE:-1}

if [ "$MODE" = "2" ]; then
    echo -e "${GREEN}Iniciando em modo DESENVOLVIMENTO...${RESET}"
    docker-compose -f docker-compose.dev.yml up --build
else
    echo -e "${GREEN}Iniciando em modo PRODUÇÃO...${RESET}"

    # Build
    echo -e "${YELLOW}Building Docker image...${RESET}"
    docker-compose build

    # Up
    echo -e "${YELLOW}Starting containers...${RESET}"
    docker-compose up -d

    # Aguardar containers ficarem saudáveis
    echo -e "${YELLOW}Aguardando containers ficarem saudáveis...${RESET}"
    sleep 5

    # Verificar health
    echo ""
    echo -e "${GREEN}Verificando health check...${RESET}"

    MAX_RETRIES=12
    RETRY=0
    while [ $RETRY -lt $MAX_RETRIES ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ API está saudável!${RESET}"
            break
        fi
        RETRY=$((RETRY+1))
        echo -e "${YELLOW}  Tentativa $RETRY/$MAX_RETRIES...${RESET}"
        sleep 5
    done

    if [ $RETRY -eq $MAX_RETRIES ]; then
        echo -e "${RED}✗ API não respondeu ao health check${RESET}"
        echo -e "${YELLOW}Verificando logs...${RESET}"
        docker-compose logs --tail=20 api
        exit 1
    fi

    # Sucesso!
    echo ""
    echo -e "${GREEN}========================================${RESET}"
    echo -e "${GREEN}✓ Aplicação rodando com sucesso!${RESET}"
    echo -e "${GREEN}========================================${RESET}"
    echo ""
    echo -e "${GREEN}URLs disponíveis:${RESET}"
    echo -e "  API:         http://localhost:8000"
    echo -e "  Health:      http://localhost:8000/health"
    echo -e "  Docs:        http://localhost:8000/docs"
    echo -e "  Redoc:       http://localhost:8000/redoc"
    echo -e "  Metrics:     http://localhost:8000/metrics"
    echo ""
    echo -e "${YELLOW}Comandos úteis:${RESET}"
    echo -e "  Ver logs:          docker-compose logs -f"
    echo -e "  Ver logs API:      docker-compose logs -f api"
    echo -e "  Parar:             docker-compose down"
    echo -e "  Reiniciar:         docker-compose restart"
    echo -e "  Shell na API:      docker-compose exec api /bin/bash"
    echo -e "  Redis CLI:         docker-compose exec redis redis-cli"
    echo ""
    echo -e "${GREEN}Ou use o Makefile:${RESET}"
    echo -e "  make help    - Ver todos os comandos disponíveis"
    echo -e "  make logs    - Ver logs"
    echo -e "  make down    - Parar containers"
    echo ""
fi
