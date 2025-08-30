#!/usr/bin/env python3
"""
Teste de fumaça para o orquestrador "magro".
Verifica se os componentes básicos estão funcionando.
"""

import json
import os
import sys
from pathlib import Path


def test_directory_structure():
    """Testa se a estrutura de diretórios está correta."""
    required_dirs = [
        "issues",
        "handoff", 
        "reports",
        "logs",
        "diffs",
        "src",
        "tests",
        ".cursor",
        "orchestrator",
        "secrets"
    ]
    
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            print(f"❌ Diretório não encontrado: {dir_name}")
            return False
        print(f"✅ Diretório encontrado: {dir_name}")
    
    return True


def test_template_files():
    """Testa se os arquivos de template estão presentes."""
    required_files = [
        "issues/TEMPLATE.md",
        "handoff/plan.template.json",
        "handoff/spec.template.md",
        "reports/qa.template.json"
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ Template não encontrado: {file_path}")
            return False
        print(f"✅ Template encontrado: {file_path}")
    
    return True


def test_orchestrator_scripts():
    """Testa se os scripts do orquestrador estão presentes e executáveis."""
    scripts = [
        "orchestrator/orchestrate.sh",
        "orchestrator/write_qa.py"
    ]
    
    for script in scripts:
        script_path = Path(script)
        if not script_path.exists():
            print(f"❌ Script não encontrado: {script}")
            return False
        
        if not os.access(script_path, os.X_OK):
            print(f"❌ Script não é executável: {script}")
            return False
        
        print(f"✅ Script executável: {script}")
    
    return True


def test_config_files():
    """Testa se os arquivos de configuração estão presentes e válidos."""
    config_files = [
        "orchestrator/config.json",
        "Makefile"
    ]
    
    for config_file in config_files:
        if not Path(config_file).exists():
            print(f"❌ Configuração não encontrada: {config_file}")
            return False
        
        # Testa se JSON é válido
        if config_file.endswith('.json'):
            try:
                with open(config_file, 'r') as f:
                    json.load(f)
                print(f"✅ JSON válido: {config_file}")
            except json.JSONDecodeError:
                print(f"❌ JSON inválido: {config_file}")
                return False
        else:
            print(f"✅ Configuração encontrada: {config_file}")
    
    return True


def test_demo_issue():
    """Testa se o issue de exemplo está presente."""
    demo_issue = Path("issues/demo.md")
    
    if not demo_issue.exists():
        print("❌ Issue de exemplo não encontrado")
        return False
    
    # Verifica se tem conteúdo mínimo
    content = demo_issue.read_text()
    required_sections = ["# Title", "## Contexto", "## Objetivo", "## Critérios de aceitação"]
    
    for section in required_sections:
        if section not in content:
            print(f"❌ Seção obrigatória não encontrada: {section}")
            return False
    
    print("✅ Issue de exemplo válido")
    return True


def test_security_files():
    """Testa se os arquivos de segurança estão configurados corretamente."""
    # Verifica se .env.example existe mas .env não
    env_example = Path("secrets/env.example")
    env_real = Path("secrets/.env")
    
    if not env_example.exists():
        print("❌ secrets/env.example não encontrado")
        return False
    
    if env_real.exists():
        print("⚠️  secrets/.env encontrado (deve ser ignorado pelo git)")
    
    print("✅ Configuração de segurança válida")
    return True


def main():
    """Executa todos os testes de fumaça."""
    print("🧪 Executando testes de fumaça do orquestrador...\n")
    
    tests = [
        ("Estrutura de diretórios", test_directory_structure),
        ("Arquivos de template", test_template_files),
        ("Scripts do orquestrador", test_orchestrator_scripts),
        ("Arquivos de configuração", test_config_files),
        ("Issue de exemplo", test_demo_issue),
        ("Configuração de segurança", test_security_files)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - PASS")
            else:
                print(f"❌ {test_name} - FAIL")
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")
    
    print(f"\n📊 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todos os testes de fumaça passaram!")
        return 0
    else:
        print("⚠️  Alguns testes falharam - verifique a configuração")
        return 1


if __name__ == "__main__":
    sys.exit(main())
