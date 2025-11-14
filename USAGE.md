# 📖 Guia de Uso - Anything to LLMs.txt

Guia completo de uso com todas as novas funcionalidades implementadas.

---

## 🚀 Início Rápido

### CLI - Interface de Linha de Comando

O projeto agora possui uma interface CLI totalmente funcional!

```bash
# Conversão simples
python -m src.main --file documento.pdf

# Com perfil específico
python -m src.main --file documento.pdf --profile llms-min

# Salvar em arquivo específico
python -m src.main --file documento.pdf --output resultado.txt

# Com OCR customizado
python -m src.main --file documento.pdf --ocr-engine tesseract --ocr-language eng

# Modo verbose (debug)
python -m src.main --file documento.pdf --verbose

# Sem salvar (apenas exibir no terminal)
python -m src.main --file documento.pdf --no-save
```

### API REST

```bash
# Iniciar servidor
python run_api.py

# Ou com docker-compose
docker-compose up -d
```

---

## ⚙️ Configuração

### Método 1: Arquivo .env (Recomendado)

```bash
# Copiar template
cp .env.example .env

# Editar com suas configurações
nano .env
```

### Método 2: Variáveis de Ambiente

```bash
export ENVIRONMENT=production
export CORS_ORIGINS="https://meu-site.com"
export LLMS_API_KEY="sua-chave-secreta"
export MAX_FILE_SIZE=104857600  # 100MB
export LOG_FORMAT=json
```

### Configurações Principais

| Variável | Descrição | Padrão | Exemplo |
|----------|-----------|--------|---------|
| `ENVIRONMENT` | Ambiente | `production` | `development` |
| `CORS_ORIGINS` | Origens permitidas | `localhost` | `https://site.com` |
| `LLMS_API_KEY` | Chave API | *(vazio)* | `abc123...` |
| `REDIS_URL` | URL do Redis | `redis://redis:6379/0` | `redis://localhost:6379` |
| `MAX_FILE_SIZE` | Tamanho máximo | `52428800` (50MB) | `104857600` (100MB) |
| `LOG_FORMAT` | Formato de log | `text` | `json` |
| `LOG_LEVEL` | Nível de log | `INFO` | `DEBUG` |

Veja `.env.example` para lista completa!

---

## 🏥 Health Check

O endpoint `/health` agora é inteligente e verifica:

```bash
curl http://localhost:8000/health
```

**Resposta saudável:**
```json
{
  "status": "healthy",
  "checks": {
    "redis": {"status": "ok", "message": "Connected"},
    "disk": {
      "status": "ok",
      "free_gb": 45.23,
      "total_gb": 100.0,
      "percent_used": 54.8
    },
    "upload_dir": {"status": "ok", "writable": true}
  }
}
```

**Resposta com problema:**
```json
{
  "status": "unhealthy",
  "checks": {
    "redis": {"status": "error", "message": "Connection refused"},
    "disk": {"status": "warning", "percent_used": 92.1},
    "upload_dir": {"status": "ok", "writable": true}
  }
}
```

Integre com Kubernetes, Docker Swarm, ou seu sistema de monitoramento!

---

## 📊 Logging

### Formato Texto (Desenvolvimento)

```bash
export LOG_FORMAT=text
export LLMS_LOG_LEVEL=DEBUG
```

**Saída:**
```
[2025-01-14 10:30:45] INFO - src.api.main: API iniciada
[2025-01-14 10:30:50] DEBUG - src.tools.converter: Processando arquivo documento.pdf
```

### Formato JSON (Produção)

```bash
export LOG_FORMAT=json
export LLMS_LOG_LEVEL=INFO
```

**Saída:**
```json
{"timestamp":"2025-01-14T10:30:45.123","level":"INFO","logger":"src.api.main","message":"API iniciada","module":"main","function":"startup","line":45}
{"timestamp":"2025-01-14T10:30:50.456","level":"INFO","logger":"src.tools.converter","message":"Processando arquivo","module":"converter","function":"run","line":120}
```

Perfeito para integração com:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Splunk
- DataDog
- CloudWatch

---

## 🐳 Docker

### Build e Run

```bash
# Build da imagem otimizada
docker build -t llms-txt-api .

# Run com configurações
docker run -d \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e CORS_ORIGINS="https://meu-site.com" \
  -e LLMS_API_KEY="sua-chave" \
  -e LOG_FORMAT=json \
  --name llms-api \
  llms-txt-api
```

### Docker Compose

```bash
# Iniciar todos os serviços (API + Redis)
docker-compose up -d

# Ver logs
docker-compose logs -f api

# Parar
docker-compose down
```

### Características do Dockerfile Otimizado

✅ **Multi-stage build** - Imagem final menor
✅ **Usuário não-root** - Segurança
✅ **Health check integrado** - Monitoramento automático
✅ **Labels** - Metadados organizados
✅ **Tesseract OCR** - Português e Inglês incluídos
✅ **Workers** - 2 workers Uvicorn para melhor performance

---

## 🔒 Segurança

### Validação de URL

A API agora valida URLs para prevenir ataques:

❌ **Rejeitado:**
```
file:///etc/passwd
javascript:alert('xss')
http://localhost/admin
http://192.168.1.1/router
```

✅ **Aceito:**
```
https://example.com/document.pdf
http://public-website.com/file.docx
```

### CORS Configurável

Antes: ⚠️ `allow_origins=["*"]` (vulnerável)
Agora: ✅ `CORS_ORIGINS=https://meu-site.com` (seguro)

### Error Handling Inteligente

```bash
# Desenvolvimento: mostra detalhes
export ENVIRONMENT=development

# Produção: mensagem genérica
export ENVIRONMENT=production
```

---

## 📝 Exemplos de Uso

### Exemplo 1: Conversão Básica

```bash
# CLI
python -m src.main --file relatorio.pdf --output relatorio.txt

# Resultado: relatorio.txt com formato LLMs.txt
```

### Exemplo 2: API com cURL

```bash
# Upload de arquivo
curl -X POST "http://localhost:8000/v1/convert/" \
  -H "X-API-Key: sua-chave" \
  -F "file=@documento.pdf" \
  -F 'params={"profile":"llms-full"}'

# Resposta
{
  "job_id": "abc-123-def",
  "status": "processing"
}

# Verificar status
curl "http://localhost:8000/v1/convert/abc-123-def" \
  -H "X-API-Key: sua-chave"
```

### Exemplo 3: Conversão de URL

```bash
curl -X POST "http://localhost:8000/v1/convert/" \
  -H "X-API-Key: sua-chave" \
  -F "url=https://example.com/document.pdf" \
  -F 'params={"profile":"llms-min"}'
```

### Exemplo 4: Perfis Diferentes

```bash
# Mínimo (só título e conteúdo)
python -m src.main --file doc.pdf --profile llms-min

# Com contexto (+ resumo)
python -m src.main --file doc.pdf --profile llms-ctx

# Com tabelas
python -m src.main --file doc.pdf --profile llms-tables

# Com imagens
python -m src.main --file doc.pdf --profile llms-images

# Completo (tudo + análise de tokens)
python -m src.main --file doc.pdf --profile llms-full
```

---

## 🔧 Troubleshooting

### Problema: Health check falha

```bash
# Verificar se Redis está rodando
docker ps | grep redis

# Verificar logs
docker-compose logs redis
```

### Problema: Disco cheio

```bash
# Limpar arquivos temporários
rm -rf temp/uploads/*

# Verificar espaço
df -h
```

### Problema: Logs não aparecem

```bash
# Verificar configuração
python -m src.config

# Ajustar nível
export LLMS_LOG_LEVEL=DEBUG
```

---

## 📈 Performance

### Configurações Recomendadas

**Desenvolvimento:**
```bash
ENVIRONMENT=development
LOG_FORMAT=text
LOG_LEVEL=DEBUG
JOB_TTL_PROCESSING=600  # 10 min
```

**Produção:**
```bash
ENVIRONMENT=production
LOG_FORMAT=json
LOG_LEVEL=INFO
JOB_TTL_PROCESSING=3600  # 1h
JOB_TTL_COMPLETED=86400  # 24h
MAX_FILE_SIZE=104857600  # 100MB
```

### TTL (Time To Live) para Jobs

Jobs do Redis agora expiram automaticamente:

- **Em processamento**: 1 hora (padrão)
- **Completados**: 24 horas (padrão)
- **Com erro**: 24 horas (para debug)

Configure via variáveis de ambiente!

---

## 🎓 Próximos Passos

1. ✅ Revise `.env.example` e configure seu `.env`
2. ✅ Teste o health check: `curl localhost:8000/health`
3. ✅ Experimente o CLI: `python -m src.main --file test.pdf`
4. ✅ Configure logging estruturado para produção
5. ✅ Integre o health check com seu sistema de monitoramento

---

## 📚 Mais Recursos

- [README Principal](README.md)
- [Configurações](.env.example)
- [Docker Compose](docker-compose.yml)
- [Documentação API](http://localhost:8000/docs) (Swagger)

**Dúvidas?** Abra uma issue no GitHub!
