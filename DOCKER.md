# 🐳 Docker - Guia Completo

Guia completo para rodar a aplicação Anything to LLMs.txt usando Docker.

---

## 📋 Pré-requisitos

- **Docker** 20.10+ ([instalar](https://docs.docker.com/get-docker/))
- **Docker Compose** 2.0+ (geralmente incluído no Docker Desktop)
- **Make** (opcional, mas recomendado)

**Verificar instalação:**
```bash
docker --version
docker-compose --version
make --version  # opcional
```

---

## 🚀 Quick Start (30 segundos)

### Opção 1: Usando script automatizado
```bash
# Tornar executável
chmod +x docker-run.sh

# Rodar
./docker-run.sh
```

O script irá:
1. ✅ Verificar Docker
2. ✅ Criar `.env` se não existir
3. ✅ Build da imagem
4. ✅ Subir containers
5. ✅ Verificar health check
6. ✅ Mostrar URLs

### Opção 2: Usando Makefile
```bash
# Setup inicial completo
make init

# Ou manualmente:
make build  # Build da imagem
make up     # Subir containers
make logs   # Ver logs
```

### Opção 3: Docker Compose direto
```bash
# Copiar .env
cp .env.example .env

# Subir containers
docker-compose up -d

# Ver logs
docker-compose logs -f
```

---

## 📂 Estrutura de Arquivos Docker

```
.
├── Dockerfile                    # Multi-stage build otimizado
├── docker-compose.yml            # Produção
├── docker-compose.dev.yml        # Desenvolvimento (hot-reload)
├── .dockerignore                 # Ignorar arquivos no build
├── .env.example                  # Template de configuração
├── .env                          # Configuração (criar este)
├── docker-run.sh                 # Script helper
├── Makefile                      # Comandos facilitados
└── DOCKER.md                     # Este arquivo
```

---

## ⚙️ Configuração

### 1. Criar arquivo .env

```bash
# Copiar template
cp .env.example .env

# Editar configurações
nano .env  # ou vim, code, etc.
```

### 2. Configurações importantes

**Mínimo necessário:**
```bash
ENVIRONMENT=production
LLMS_API_KEY=sua-chave-super-secreta-aqui
CORS_ORIGINS=https://seu-site.com
REDIS_URL=redis://redis:6379/0
```

**Para desenvolvimento:**
```bash
ENVIRONMENT=development
LLMS_LOG_LEVEL=DEBUG
LOG_FORMAT=text
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

---

## 🏃 Rodando a Aplicação

### Modo Produção

```bash
# Build e up
make prod

# Ou manualmente
docker-compose build
docker-compose up -d
```

**URLs disponíveis:**
- API: http://localhost:8000
- Health: http://localhost:8000/health
- Docs: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics

### Modo Desenvolvimento (Hot-Reload)

```bash
# Com hot-reload (código atualiza automaticamente)
make dev

# Ou manualmente
docker-compose -f docker-compose.dev.yml up
```

**Vantagens:**
- ✅ Código fonte montado como volume
- ✅ Mudanças refletem automaticamente
- ✅ Logs detalhados (DEBUG)
- ✅ CORS permissivo para desenvolvimento

---

## 📊 Comandos Úteis

### Makefile (recomendado)

```bash
make help           # Ver todos os comandos
make build          # Build da imagem
make up             # Subir containers
make down           # Parar containers
make restart        # Reiniciar containers
make logs           # Ver logs de todos
make logs-api       # Ver logs apenas da API
make ps             # Status dos containers
make health         # Verificar health check
make metrics        # Ver métricas Prometheus
make shell          # Shell no container da API
make shell-redis    # Redis CLI
make test           # Rodar testes
make test-cov       # Testes com coverage
make clean          # Limpar tudo
make dev            # Modo desenvolvimento
make prod           # Deploy produção
```

### Docker Compose direto

```bash
# Subir
docker-compose up -d

# Ver logs
docker-compose logs -f
docker-compose logs -f api
docker-compose logs -f redis

# Status
docker-compose ps

# Parar
docker-compose down

# Reiniciar
docker-compose restart
docker-compose restart api

# Rebuild
docker-compose up -d --build

# Shell
docker-compose exec api /bin/bash
docker-compose exec redis redis-cli
```

### Docker direto

```bash
# Listar containers
docker ps

# Ver logs
docker logs llms-api -f
docker logs llms-redis -f

# Shell
docker exec -it llms-api /bin/bash
docker exec -it llms-redis redis-cli

# Reiniciar
docker restart llms-api
docker restart llms-redis

# Parar
docker stop llms-api llms-redis

# Remover
docker rm -f llms-api llms-redis
```

---

## 🔍 Monitoramento

### Health Check

```bash
# Via Makefile
make health

# Ou curl
curl http://localhost:8000/health | jq

# Resposta esperada:
# {
#   "status": "healthy",
#   "checks": {
#     "redis": "ok",
#     "disk": "ok",
#     "upload_dir": "ok"
#   }
# }
```

### Métricas Prometheus

```bash
# Via Makefile
make metrics

# Ou curl
curl http://localhost:8000/metrics

# Ver métricas específicas
curl http://localhost:8000/metrics | grep http_requests_total
curl http://localhost:8000/metrics | grep conversion_jobs
```

### Ver Logs

```bash
# Logs em tempo real
make logs

# Últimas 100 linhas
docker-compose logs --tail=100

# Apenas da API
make logs-api

# Apenas do Redis
make logs-redis

# Com timestamp
docker-compose logs -f -t

# Logs estruturados (JSON em produção)
docker-compose logs api | jq
```

---

## 🧪 Testes

### Dentro do Container

```bash
# Rodar todos os testes
make test

# Com coverage
make test-cov

# Ou manualmente
docker-compose exec api pytest -v
docker-compose exec api pytest --cov=src --cov-report=html
```

### Load Testing

```bash
# Quick test
make quick-load

# Load test completo (requer locust)
make load-test

# Ou manualmente
bash tests/load/quick_load_test.sh
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

---

## 🐛 Debugging

### Container não sobe

```bash
# Ver logs de erro
docker-compose logs api

# Ver eventos
docker-compose ps

# Rebuild sem cache
docker-compose build --no-cache
docker-compose up -d
```

### API não responde ao health check

```bash
# Ver logs detalhados
docker-compose logs -f api

# Verificar se está rodando
docker-compose ps

# Verificar portas
docker-compose port api 8000

# Entrar no container
docker-compose exec api /bin/bash

# Dentro do container:
curl localhost:8000/health
ps aux | grep uvicorn
```

### Redis não conecta

```bash
# Verificar Redis
docker-compose exec redis redis-cli ping
# Deve retornar: PONG

# Ver dados do Redis
docker-compose exec redis redis-cli
> KEYS *
> HGETALL job:some-id

# Ver logs do Redis
docker-compose logs -f redis
```

### Problemas de permissão

```bash
# Verificar permissões da pasta temp/
ls -la temp/

# Recriar com permissões corretas
rm -rf temp/
mkdir -p temp/uploads
chmod 755 temp/

# Rebuild
make restart
```

### Playwright não funciona

```bash
# Entrar no container
docker-compose exec api /bin/bash

# Reinstalar browsers
playwright install chromium --with-deps

# Verificar instalação
playwright --version
chromium --version
```

---

## 🗑️ Limpeza

```bash
# Parar e remover containers
make down

# Limpar volumes também
docker-compose down -v

# Limpar tudo (containers, volumes, imagens)
make clean

# Limpar apenas arquivos temporários
make clean-temp

# Limpar todo sistema Docker (cuidado!)
make prune
```

---

## 🏗️ Build Customizado

### Build com argumentos

```bash
# Build sem cache
docker-compose build --no-cache

# Build com tag específica
docker build -t llms-txt-api:v2.0.0 .

# Build com target específico (multi-stage)
docker build --target builder -t llms-txt-api:builder .
```

### Otimizar imagem

O Dockerfile já está otimizado com:
- ✅ Multi-stage build
- ✅ Camadas mínimas
- ✅ Cache de dependências
- ✅ Usuário não-root
- ✅ Health check integrado

**Tamanho típico:** ~1.5GB (principalmente browsers Playwright)

---

## 🔒 Segurança

### Melhores práticas aplicadas:

1. ✅ **Usuário não-root**: Container roda como `appuser`
2. ✅ **Secrets via .env**: Nunca commitar `.env`
3. ✅ **CORS configurável**: Restringir origens permitidas
4. ✅ **Health checks**: Detectar containers unhealthy
5. ✅ **Resource limits**: Limitar CPU/memória do Redis
6. ✅ **Read-only filesystem**: (opcional, adicionar `read_only: true`)

### Recomendações adicionais:

```yaml
# docker-compose.yml
services:
  api:
    # Adicionar para máxima segurança:
    read_only: true
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
```

---

## 📦 Deploy em Produção

### Checklist antes do deploy:

- [ ] `.env` configurado com valores de produção
- [ ] `LLMS_API_KEY` gerada com segurança (64+ caracteres)
- [ ] `CORS_ORIGINS` restrito aos seus domínios
- [ ] `ENVIRONMENT=production`
- [ ] `LOG_FORMAT=json`
- [ ] Health checks funcionando
- [ ] Testes passando
- [ ] Volumes de persistência configurados
- [ ] Backup do Redis configurado
- [ ] Monitoramento (Prometheus) configurado
- [ ] Alertas configurados

### Deploy

```bash
# 1. Pull do código
git pull origin main

# 2. Build
make prod

# 3. Verificar
make health
make metrics

# 4. Monitorar
make logs
```

### Com Docker Swarm

```bash
# Deploy stack
docker stack deploy -c docker-compose.yml llms-txt

# Ver serviços
docker stack services llms-txt

# Ver logs
docker service logs -f llms-txt_api
```

### Com Kubernetes

Ver [k8s/README.md](k8s/README.md) para deploy completo em Kubernetes com auto-scaling.

---

## 🔄 CI/CD

### GitHub Actions

O projeto já tem CI/CD configurado em `.github/workflows/ci.yml`:

1. ✅ Build da imagem Docker
2. ✅ Testes automatizados
3. ✅ Scan de segurança (Trivy)
4. ✅ Deploy automático (branch main)

### Deploy manual via CI

```bash
# Push para main
git push origin main

# GitHub Actions vai:
# 1. Build da imagem
# 2. Rodar testes
# 3. Scan de vulnerabilidades
# 4. Deploy (se configurado)
```

---

## 📚 Recursos Adicionais

### Documentação

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc
- **Kubernetes**: [k8s/README.md](k8s/README.md)
- **Runbook**: [docs/RUNBOOK.md](docs/RUNBOOK.md)
- **Secrets**: [docs/SECRETS_ROTATION.md](docs/SECRETS_ROTATION.md)

### Monitoramento Stack Completo

```bash
# Subir stack completo (API + Redis + Prometheus + Grafana)
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

# Acessar:
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
# - AlertManager: http://localhost:9093
```

---

## ❓ FAQ

### Q: Como mudar a porta da API?

**R:** Edite `.env`:
```bash
SERVER_PORT=8080
```

E reinicie:
```bash
make restart
```

### Q: Como adicionar mais workers?

**R:** Edite `docker-compose.yml`:
```yaml
command: uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Q: Como fazer backup do Redis?

**R:**
```bash
# Backup
make backup-redis

# Copiar arquivo
docker cp llms-redis:/data/dump.rdb ./backup/

# Restaurar
docker cp ./backup/dump.rdb llms-redis:/data/
make restart
```

### Q: Como ver uso de recursos?

**R:**
```bash
# Stats em tempo real
docker stats llms-api llms-redis

# Ou via docker-compose
docker-compose stats
```

### Q: Como atualizar dependências?

**R:**
```bash
# 1. Atualizar requirements.txt
# 2. Rebuild
make build

# 3. Reiniciar
make up
```

---

## 🆘 Suporte

### Problemas comuns:

1. **"Cannot connect to Docker daemon"**
   - Inicie o Docker Desktop/Engine

2. **"Port already in use"**
   - Mude a porta em `.env` ou pare o serviço conflitante

3. **"Health check failed"**
   - Veja logs: `make logs-api`
   - Verifique configuração em `.env`

4. **"Permission denied"**
   - Verifique permissões: `ls -la temp/`
   - Recrie pastas: `rm -rf temp && mkdir -p temp/uploads`

---

**Última atualização:** 2025-01-14
**Maintainer:** DevOps Team
**Dúvidas:** Abra uma issue no GitHub
