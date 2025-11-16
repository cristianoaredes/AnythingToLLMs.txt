# Kubernetes Deployment Guide

Guia para deploy da API em Kubernetes com auto-scaling.

---

## 📋 Pré-requisitos

- Kubernetes cluster (v1.24+)
- `kubectl` configurado
- Metrics Server instalado (para HPA)

**Verificar Metrics Server:**
```bash
kubectl get deployment metrics-server -n kube-system
```

**Instalar Metrics Server (se necessário):**
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

---

## 🚀 Deploy Rápido

### 1. Criar Namespace
```bash
kubectl create namespace llms-txt
kubectl config set-context --current --namespace=llms-txt
```

### 2. Criar Secret com API Key
```bash
# Gerar API key segura
API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")

# Criar secret
kubectl create secret generic llms-secrets \
  --from-literal=api-key="$API_KEY" \
  -n llms-txt
```

### 3. Aplicar Configurações
```bash
# Configuração
kubectl apply -f k8s/configmap.yaml

# Redis
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/redis-service.yaml

# API
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# HPA (auto-scaling)
kubectl apply -f k8s/hpa.yaml
```

### 4. Verificar Deploy
```bash
# Ver pods
kubectl get pods -n llms-txt

# Ver serviços
kubectl get svc -n llms-txt

# Ver HPA
kubectl get hpa -n llms-txt

# Logs
kubectl logs -l app=llms-api -n llms-txt --tail=50 -f
```

---

## 📊 Monitorar Auto-Scaling

### Ver Status do HPA
```bash
kubectl get hpa llms-api-hpa -n llms-txt --watch
```

**Output esperado:**
```
NAME            REFERENCE             TARGETS         MINPODS   MAXPODS   REPLICAS
llms-api-hpa    Deployment/llms-api   45%/70%, 60%/80%   3         20        3
```

### Métricas Detalhadas
```bash
# CPU e memória por pod
kubectl top pods -l app=llms-api -n llms-txt

# Eventos do HPA
kubectl describe hpa llms-api-hpa -n llms-txt
```

---

## 🧪 Testar Auto-Scaling

### Gerar Carga
```bash
# Pegar IP do LoadBalancer
LB_IP=$(kubectl get svc llms-api -n llms-txt -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Gerar carga (requer Apache Bench)
ab -n 10000 -c 100 http://$LB_IP/health
```

### Monitorar Scaling
```bash
# Em outro terminal
watch kubectl get hpa,pods -n llms-txt
```

**Você verá:**
1. CPU aumenta
2. HPA detecta > 70% CPU
3. Pods novos são criados
4. Carga distribui
5. CPU normaliza
6. Após 5min, HPA reduz réplicas

---

## 🔧 Configuração

### Ajustar Limites de Scaling

**Editar HPA:**
```bash
kubectl edit hpa llms-api-hpa -n llms-txt
```

**Ou atualizar YAML e aplicar:**
```yaml
spec:
  minReplicas: 5     # Aumentar mínimo
  maxReplicas: 50    # Aumentar máximo
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        averageUtilization: 60  # Mais agressivo (era 70%)
```

```bash
kubectl apply -f k8s/hpa.yaml
```

### Ajustar Recursos dos Pods

**Editar deployment:**
```bash
kubectl edit deployment llms-api -n llms-txt
```

**Ou atualizar YAML:**
```yaml
resources:
  requests:
    cpu: 1000m      # 1 CPU (era 500m)
    memory: 1Gi     # (era 512Mi)
  limits:
    cpu: 4000m      # 4 CPUs (era 2000m)
    memory: 4Gi     # (era 2Gi)
```

---

## 🔄 Rollout e Rollback

### Deploy Nova Versão
```bash
# Atualizar imagem
kubectl set image deployment/llms-api api=llms-txt-api:v2.0.0 -n llms-txt

# Monitorar rollout
kubectl rollout status deployment/llms-api -n llms-txt

# Ver histórico
kubectl rollout history deployment/llms-api -n llms-txt
```

### Rollback
```bash
# Voltar versão anterior
kubectl rollout undo deployment/llms-api -n llms-txt

# Voltar para revisão específica
kubectl rollout undo deployment/llms-api --to-revision=2 -n llms-txt
```

---

## 🗑️ Limpeza

```bash
# Deletar tudo
kubectl delete -f k8s/ -n llms-txt

# Deletar namespace
kubectl delete namespace llms-txt
```

---

## 📚 Recursos Adicionais

### Health Check
```bash
curl http://$LB_IP/health
```

### Métricas Prometheus
```bash
curl http://$LB_IP/metrics
```

### Logs Estruturados
```bash
kubectl logs -l app=llms-api -n llms-txt | jq
```

---

## ⚙️ Configurações Avançadas

### Usar Ingress (em vez de LoadBalancer)

**ingress.yaml:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: llms-api-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.example.com
    secretName: llms-api-tls
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: llms-api
            port:
              number: 80
```

```bash
kubectl apply -f ingress.yaml
```

### Redis com Alta Disponibilidade

Para produção, considere:
- **Redis Sentinel** (HA master-slave)
- **Redis Cluster** (sharding + HA)
- **Managed Redis** (AWS ElastiCache, GCP Memorystore, Azure Cache)

---

## 🚨 Troubleshooting

### HPA não escala

```bash
# 1. Verificar Metrics Server
kubectl get apiservice v1beta1.metrics.k8s.io

# 2. Ver métricas
kubectl top nodes
kubectl top pods -n llms-txt

# 3. Ver eventos
kubectl get events -n llms-txt --sort-by='.lastTimestamp'
```

### Pods crashando

```bash
# Ver logs
kubectl logs -l app=llms-api -n llms-txt --previous

# Ver eventos
kubectl describe pod <pod-name> -n llms-txt

# Entrar no pod
kubectl exec -it <pod-name> -n llms-txt -- /bin/bash
```

### Redis sem persistência

```bash
# Verificar PVC
kubectl get pvc -n llms-txt

# Ver eventos do PVC
kubectl describe pvc redis-pvc -n llms-txt
```

---

**Última atualização:** 2025-01-14
**Maintainer:** DevOps Team
