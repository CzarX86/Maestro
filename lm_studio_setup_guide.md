# 🎨 LM Studio Setup Guide for Mac M3
## Guia Completo de Instalação e Configuração

---

## 📋 **PRÉ-REQUISITOS**

- ✅ macOS 13.0+ (Ventura)
- ✅ MacBook Air M3 (8GB RAM)
- ✅ Conexão estável com internet
- ✅ ~10GB espaço livre (para modelos)

---

## 🚀 **PASSO 1: DOWNLOAD E INSTALAÇÃO**

### **1.1 Download**
```bash
# Abra o navegador e vá para:
https://lmstudio.ai

# Ou use o link direto:
https://lmstudio.ai/download
```

### **1.2 Instalação**
1. **Baixe** o arquivo `.dmg` para macOS
2. **Abra** o arquivo baixado
3. **Arraste** LM Studio para a pasta Applications
4. **Abra** LM Studio pela primeira vez
5. **Permita** acesso quando solicitado

### **1.3 Primeira Execução**
```bash
# LM Studio irá:
✅ Detectar seu Mac M3 automaticamente
✅ Configurar otimizações nativas
✅ Criar pasta de modelos em ~/Library/Application Support/LM Studio
```

---

## ⚙️ **PASSO 2: CONFIGURAÇÃO INICIAL**

### **2.1 Configurações do Sistema**
```bash
# Abra LM Studio e vá em:
Settings → System Settings

# Configure:
✅ GPU: Apple M3 (detectado automaticamente)
✅ Memory: 6GB (deixe 2GB para sistema)
✅ Threads: 8 (otimizado para M3)
✅ Context Length: 4096
```

### **2.2 Configurações de Performance**
```bash
# Em Performance Settings:
✅ Enable Metal Performance Shaders
✅ Enable Neural Engine (se disponível)
✅ Optimize for Apple Silicon
✅ Enable Flash Attention
```

---

## 📦 **PASSO 3: DOWNLOAD DE MODELOS**

### **3.1 Modelos Recomendados para M3**

#### **🥇 qwen3-coder:7b (Recomendado)**
```bash
# No LM Studio:
1. Vá em "Search Models"
2. Digite: "qwen3-coder"
3. Selecione: "qwen3-coder:7b"
4. Clique em "Download"
5. Aguarde download (~4.2GB)
```

#### **🥈 codellama:7b (Alternativa)**
```bash
# Para desenvolvimento geral:
1. Search: "codellama"
2. Selecione: "codellama:7b"
3. Download (~4.1GB)
```

#### **🥉 llama3.2:3b (Leve)**
```bash
# Para uso rápido:
1. Search: "llama3.2"
2. Selecione: "llama3.2:3b"
3. Download (~2.1GB)
```

### **3.2 Formatos Suportados**
- ✅ **GGUF** (recomendado)
- ✅ **GGML** (legado)
- ✅ **EXL2** (experimental)

---

## 🎯 **PASSO 4: CONFIGURAÇÃO DE MODELOS**

### **4.1 Configuração qwen3-coder:7b**
```bash
# Após download, configure:
✅ Model: qwen3-coder:7b
✅ Context Length: 4096
✅ Temperature: 0.7
✅ Top P: 0.9
✅ Top K: 40
✅ Repeat Penalty: 1.1
```

### **4.2 Otimizações Específicas**
```bash
# Para desenvolvimento:
✅ Enable Code Completion
✅ Enable Function Calling
✅ Enable Structured Output
✅ Enable Safety Filters (opcional)
```

---

## 🧪 **PASSO 5: TESTE DE PERFORMANCE**

### **5.1 Teste Básico**
```python
# Prompt de teste:
"Write a Python function to calculate the factorial of a number using recursion"

# Métricas para observar:
✅ Response Time: < 5 segundos
✅ Token Generation: 20-35 tokens/seg
✅ Memory Usage: < 6GB
✅ Temperature: 60-70°C
```

### **5.2 Teste de Código**
```python
# Prompt de teste:
"Create a React component that displays a counter with increment and decrement buttons"

# Verifique:
✅ Syntax highlighting
✅ Code completion
✅ Error detection
✅ Best practices
```

---

## 🔧 **PASSO 6: CONFIGURAÇÕES AVANÇADAS**

### **6.1 Integração com VS Code**
```bash
# Instale a extensão:
1. VS Code → Extensions
2. Search: "LM Studio"
3. Install: "LM Studio Integration"
4. Configure API endpoint: http://localhost:1234
```

### **6.2 API Configuration**
```bash
# Em LM Studio:
Settings → API Settings

# Configure:
✅ Enable API Server
✅ Port: 1234
✅ Host: localhost
✅ Authentication: None (local)
```

### **6.3 Chat History**
```bash
# Configure backup:
✅ Enable Chat History
✅ Auto-save: Every 5 minutes
✅ Export Format: JSON
✅ Backup Location: ~/Documents/LMStudio/
```

---

## 📊 **PASSO 7: MONITORAMENTO**

### **7.1 Métricas de Performance**
```bash
# Monitore em tempo real:
✅ CPU Usage: < 80%
✅ Memory Usage: < 6GB
✅ GPU Usage: < 90%
✅ Temperature: < 75°C
✅ Battery Drain: < 20%/hour
```

### **7.2 Logs e Debugging**
```bash
# Logs localizados em:
~/Library/Logs/LM Studio/

# Para debugging:
✅ Enable Debug Mode
✅ Verbose Logging
✅ Performance Metrics
```

---

## 🚨 **SOLUÇÃO DE PROBLEMAS**

### **Problema: Modelo não carrega**
```bash
# Soluções:
1. Verifique espaço em disco (> 10GB)
2. Reinicie LM Studio
3. Redownload do modelo
4. Verifique formato GGUF
```

### **Problema: Performance lenta**
```bash
# Otimizações:
1. Reduza context length
2. Use modelo quantizado (q4_K_M)
3. Fechar outros apps
4. Verificar temperatura do Mac
```

### **Problema: Erro de memória**
```bash
# Soluções:
1. Reduza memory allocation
2. Use modelo menor (3b vs 7b)
3. Reinicie LM Studio
4. Limpe cache do sistema
```

---

## 🎉 **PRÓXIMOS PASSOS**

### **7.1 Primeiro Uso**
```bash
# Teste básico:
1. Abra LM Studio
2. Carregue qwen3-coder:7b
3. Digite: "Hello, how are you?"
4. Verifique resposta em < 3 segundos
```

### **7.2 Uso Avançado**
```bash
# Para desenvolvimento:
1. Configure VS Code integration
2. Teste code completion
3. Experimente diferentes prompts
4. Ajuste parâmetros conforme necessário
```

### **7.3 Backup e Sincronização**
```bash
# Configure backup:
1. Export chat history
2. Backup modelos baixados
3. Sync configurações
4. Documente preferências
```

---

## 📞 **SUPORTE**

- **Documentação**: https://lmstudio.ai/docs
- **Discord**: https://discord.gg/lmstudio
- **GitHub**: https://github.com/lmstudio-ai
- **Email**: support@lmstudio.ai

---

**🎯 Resultado Esperado**: LM Studio rodando otimizado no seu Mac M3 com performance 20-35 tokens/seg e interface amigável para desenvolvimento!
