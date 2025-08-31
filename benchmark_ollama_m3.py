#!/usr/bin/env python3
"""
🚀 Ollama Performance Benchmark for Mac M3
Testa performance atual vs otimizada
"""

import time
import subprocess
import psutil
import json
from datetime import datetime

class OllamaBenchmark:
    def __init__(self):
        self.results = {}
        self.start_time = None
        
    def get_system_info(self):
        """Coleta informações do sistema"""
        try:
            # CPU info
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # GPU info (simplificado para M3)
            gpu_info = {
                "chip": "Apple M3",
                "memory": "8GB Unified",
                "neural_engine": "Available"
            }
            
            return {
                "cpu_percent": cpu_percent,
                "memory_total": memory.total,
                "memory_available": memory.available,
                "memory_percent": memory.percent,
                "gpu_info": gpu_info
            }
        except Exception as e:
            return {"error": str(e)}
    
    def test_ollama_response(self, prompt="Write a simple Python function to calculate fibonacci numbers", model="qwen3-coder:7b"):
        """Testa tempo de resposta do Ollama"""
        try:
            start_time = time.time()
            
            # Comando para testar resposta
            cmd = ["ollama", "run", model, prompt]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            return {
                "success": result.returncode == 0,
                "response_time": response_time,
                "output_length": len(result.stdout),
                "error": result.stderr if result.returncode != 0 else None
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "response_time": 60,
                "output_length": 0,
                "error": "Timeout after 60 seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "response_time": 0,
                "output_length": 0,
                "error": str(e)
            }
    
    def benchmark_current_config(self):
        """Benchmark da configuração atual"""
        print("🔍 Testando configuração atual...")
        
        # Info do sistema antes
        system_before = self.get_system_info()
        
        # Teste de resposta
        response_test = self.test_ollama_response()
        
        # Info do sistema depois
        system_after = self.get_system_info()
        
        self.results["current"] = {
            "timestamp": datetime.now().isoformat(),
            "system_before": system_before,
            "system_after": system_after,
            "response_test": response_test
        }
        
        return self.results["current"]
    
    def get_ollama_config(self):
        """Obtém configuração atual do Ollama"""
        try:
            # Verifica variáveis de ambiente
            config = {}
            
            # Testa se ollama está rodando
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            config["ollama_running"] = result.returncode == 0
            
            # Verifica variáveis de ambiente
            env_vars = ["OLLAMA_FLASH_ATTENTION", "OLLAMA_LLM_LIBRARY", "OLLAMA_GPU_OVERHEAD"]
            for var in env_vars:
                config[var] = subprocess.run(["echo", f"${var}"], capture_output=True, text=True).stdout.strip()
            
            return config
        except Exception as e:
            return {"error": str(e)}
    
    def generate_report(self):
        """Gera relatório completo"""
        print("\n📊 RELATÓRIO DE PERFORMANCE OLLAMA M3")
        print("=" * 50)
        
        # Configuração atual
        config = self.get_ollama_config()
        print(f"\n🔧 Configuração Atual:")
        print(f"   Ollama Running: {config.get('ollama_running', 'Unknown')}")
        print(f"   Flash Attention: {config.get('OLLAMA_FLASH_ATTENTION', 'Not set')}")
        print(f"   LLM Library: {config.get('OLLAMA_LLM_LIBRARY', 'Not set')}")
        print(f"   GPU Overhead: {config.get('OLLAMA_GPU_OVERHEAD', 'Not set')}")
        
        # Resultados do benchmark
        if "current" in self.results:
            current = self.results["current"]
            print(f"\n⚡ Performance Atual:")
            print(f"   Response Time: {current['response_test']['response_time']:.2f}s")
            print(f"   Success: {current['response_test']['success']}")
            print(f"   Output Length: {current['response_test']['output_length']} chars")
            
            if current['response_test']['error']:
                print(f"   Error: {current['response_test']['error']}")
        
        # Recomendações
        print(f"\n💡 Recomendações:")
        if config.get('OLLAMA_FLASH_ATTENTION') != 'true':
            print("   ❌ Flash Attention não está habilitado")
            print("   ✅ Execute: export OLLAMA_FLASH_ATTENTION=true")
        
        if not config.get('OLLAMA_LLM_LIBRARY'):
            print("   ❌ LLM Library não está definida")
            print("   ✅ Execute: export OLLAMA_LLM_LIBRARY=metal")
        
        print(f"\n🚀 Para otimizar, execute:")
        print(f"   ./optimize_ollama_m3.sh")
        
        return self.results

def main():
    """Função principal"""
    print("🚀 Ollama Performance Benchmark for Mac M3")
    print("=" * 50)
    
    benchmark = OllamaBenchmark()
    
    # Testa configuração atual
    current_results = benchmark.benchmark_current_config()
    
    # Gera relatório
    report = benchmark.generate_report()
    
    # Salva resultados
    with open("ollama_benchmark_results.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Resultados salvos em: ollama_benchmark_results.json")

if __name__ == "__main__":
    main()
