.PHONY: help build up down logs clean test dev prod restart ps health

# Cores para output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
RESET  := \033[0m

help: ## Mostrar ajuda
	@echo "$(GREEN)Anything to LLMs.txt - Docker Commands$(RESET)"
	@echo ""
	@echo "$(YELLOW)Uso:$(RESET) make [comando]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}'

# ========================================
# Build e Deploy
# ========================================

build: ## Build da imagem Docker
	@echo "$(GREEN)Building Docker image...$(RESET)"
	docker-compose build

up: ## Subir containers (produção)
	@echo "$(GREEN)Starting containers (production)...$(RESET)"
	docker-compose up -d
	@echo "$(GREEN)API disponível em: http://localhost:8000$(RESET)"
	@echo "$(YELLOW)Health check: http://localhost:8000/health$(RESET)"
	@echo "$(YELLOW)Metrics: http://localhost:8000/metrics$(RESET)"

down: ## Parar e remover containers
	@echo "$(YELLOW)Stopping containers...$(RESET)"
	docker-compose down

restart: ## Reiniciar containers
	@echo "$(YELLOW)Restarting containers...$(RESET)"
	docker-compose restart

# ========================================
# Desenvolvimento
# ========================================

dev: ## Subir containers em modo desenvolvimento (hot-reload)
	@echo "$(GREEN)Starting containers (development with hot-reload)...$(RESET)"
	docker-compose -f docker-compose.dev.yml up
	@echo "$(GREEN)API disponível em: http://localhost:8000$(RESET)"

dev-build: ## Build e subir em modo desenvolvimento
	@echo "$(GREEN)Building and starting (development)...$(RESET)"
	docker-compose -f docker-compose.dev.yml up --build

dev-down: ## Parar containers de desenvolvimento
	docker-compose -f docker-compose.dev.yml down

# ========================================
# Monitoramento
# ========================================

logs: ## Ver logs dos containers
	docker-compose logs -f

logs-api: ## Ver logs apenas da API
	docker-compose logs -f api

logs-redis: ## Ver logs do Redis
	docker-compose logs -f redis

ps: ## Listar containers rodando
	docker-compose ps

health: ## Verificar health check da API
	@echo "$(GREEN)Checking API health...$(RESET)"
	@curl -s http://localhost:8000/health | jq . || echo "$(RED)API não está respondendo$(RESET)"

metrics: ## Verificar métricas Prometheus
	@echo "$(GREEN)Fetching Prometheus metrics...$(RESET)"
	@curl -s http://localhost:8000/metrics | head -n 50

# ========================================
# Shell e Debug
# ========================================

shell: ## Abrir shell no container da API
	docker-compose exec api /bin/bash

shell-redis: ## Abrir Redis CLI
	docker-compose exec redis redis-cli

# ========================================
# Testes
# ========================================

test: ## Rodar testes dentro do container
	docker-compose exec api pytest -v

test-cov: ## Rodar testes com coverage
	docker-compose exec api pytest --cov=src --cov-report=html --cov-report=term

# ========================================
# Limpeza
# ========================================

clean: ## Limpar containers, volumes e imagens
	@echo "$(RED)Stopping and removing all containers, volumes, and images...$(RESET)"
	docker-compose down -v --rmi all
	rm -rf temp/*

clean-temp: ## Limpar apenas arquivos temporários
	@echo "$(YELLOW)Cleaning temp files...$(RESET)"
	rm -rf temp/*

prune: ## Limpar todo sistema Docker (use com cuidado!)
	@echo "$(RED)Pruning Docker system...$(RESET)"
	docker system prune -af --volumes

# ========================================
# Setup Inicial
# ========================================

init: ## Setup inicial (criar .env, build, up)
	@echo "$(GREEN)Initial setup...$(RESET)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Creating .env from .env.example...$(RESET)"; \
		cp .env.example .env; \
		echo "$(GREEN)✓ .env criado!$(RESET)"; \
		echo "$(YELLOW)⚠ IMPORTANTE: Edite .env e configure LLMS_API_KEY$(RESET)"; \
	else \
		echo "$(GREEN).env já existe$(RESET)"; \
	fi
	@make build
	@make up
	@echo ""
	@echo "$(GREEN)========================================$(RESET)"
	@echo "$(GREEN)✓ Setup completo!$(RESET)"
	@echo "$(GREEN)========================================$(RESET)"
	@echo ""
	@echo "API: http://localhost:8000"
	@echo "Health: http://localhost:8000/health"
	@echo "Docs: http://localhost:8000/docs"
	@echo ""
	@echo "$(YELLOW)Próximos passos:$(RESET)"
	@echo "  1. Edite .env e configure LLMS_API_KEY"
	@echo "  2. Reinicie: make restart"
	@echo "  3. Veja logs: make logs"

# ========================================
# Produção
# ========================================

prod: ## Deploy em produção (build + up)
	@echo "$(GREEN)Deploying to production...$(RESET)"
	@if [ ! -f .env ]; then \
		echo "$(RED)ERROR: .env não encontrado!$(RESET)"; \
		echo "$(YELLOW)Crie .env antes de fazer deploy em produção$(RESET)"; \
		exit 1; \
	fi
	docker-compose build --no-cache
	docker-compose up -d
	@echo "$(GREEN)✓ Production deploy complete!$(RESET)"
	@make health

# ========================================
# Load Testing
# ========================================

load-test: ## Rodar load test (requer locust instalado)
	@echo "$(GREEN)Starting load test...$(RESET)"
	locust -f tests/load/locustfile.py --host=http://localhost:8000 --headless -u 10 -r 2 -t 30s

quick-load: ## Quick load test com curl
	@echo "$(GREEN)Running quick load test...$(RESET)"
	bash tests/load/quick_load_test.sh

# ========================================
# Backup
# ========================================

backup-redis: ## Backup dos dados do Redis
	@echo "$(GREEN)Creating Redis backup...$(RESET)"
	docker-compose exec redis redis-cli BGSAVE
	@echo "$(GREEN)✓ Backup iniciado$(RESET)"

# Default target
.DEFAULT_GOAL := help
