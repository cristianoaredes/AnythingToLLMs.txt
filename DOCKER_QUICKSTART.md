# 🐳 Docker Quick Start (1 minuto)

Guia ultra-rápido para rodar a aplicação no Docker.

---

## ⚡ 3 Formas de Rodar

### 1️⃣ Script Automático (Mais Fácil)

```bash
./docker-run.sh
```

**O que faz:**
- ✅ Cria `.env` automaticamente
- ✅ Build da imagem
- ✅ Sobe containers
- ✅ Verifica health
- ✅ Mostra URLs

### 2️⃣ Makefile (Recomendado)

```bash
# Setup inicial (primeira vez)
make init

# Próximas vezes
make up     # Subir
make down   # Parar
make logs   # Ver logs
```

**Ver todos comandos:**
```bash
make help
```

### 3️⃣ Docker Compose Manual

```bash
# Copiar configuração
cp .env.example .env

# Subir containers
docker-compose up -d

# Ver logs
docker-compose logs -f
```

---

## 🎯 URLs Disponíveis

Após rodar, acesse:

| Serviço | URL |
|---------|-----|
| **API** | http://localhost:8000 |
| **Health Check** | http://localhost:8000/health |
| **Docs (Swagger)** | http://localhost:8000/docs |
| **Redoc** | http://localhost:8000/redoc |
| **Metrics** | http://localhost:8000/metrics |

---

## 🛠️ Comandos Úteis

```bash
# Ver o que está rodando
make ps

# Ver logs em tempo real
make logs

# Parar tudo
make down

# Reiniciar
make restart

# Entrar no container
make shell

# Rodar testes
make test

# Limpar tudo
make clean
```

---

## 🔧 Desenvolvimento

Para desenvolvimento com hot-reload (código atualiza automaticamente):

```bash
make dev
```

Agora edite arquivos em `src/` e veja mudanças instantâneas!

---

## ⚙️ Configuração Rápida

Edite `.env` para customizar:

```bash
# Obrigatório em produção
LLMS_API_KEY=sua-chave-super-secreta

# Seus domínios permitidos
CORS_ORIGINS=https://seu-site.com

# Opcional: mudar porta
SERVER_PORT=8080
```

Reinicie após editar:
```bash
make restart
```

---

## 🐛 Problemas?

### API não responde
```bash
# Ver logs
make logs-api

# Verificar configuração
cat .env

# Rebuild
make build && make up
```

### Porta em uso
```bash
# Mude a porta no .env
echo "SERVER_PORT=8080" >> .env
make restart
```

### Redis não conecta
```bash
# Verificar Redis
docker-compose exec redis redis-cli ping
# Deve retornar: PONG
```

---

## 📚 Documentação Completa

Para mais detalhes, veja:
- **[DOCKER.md](DOCKER.md)** - Guia completo
- **[k8s/README.md](k8s/README.md)** - Deploy Kubernetes
- **[docs/RUNBOOK.md](docs/RUNBOOK.md)** - Operações

---

## 🚀 Deploy em Produção

```bash
# 1. Configurar .env para produção
cp .env.example .env
nano .env  # Editar valores

# 2. Deploy
make prod

# 3. Verificar
make health
```

**Checklist:**
- [ ] `LLMS_API_KEY` configurada (64+ chars)
- [ ] `CORS_ORIGINS` restrito aos seus domínios
- [ ] `ENVIRONMENT=production`
- [ ] `LOG_FORMAT=json`

---

**Pronto! Sua API está rodando! 🎉**

Próximo passo: Acesse http://localhost:8000/docs para ver a documentação interativa.
