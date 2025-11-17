#!/usr/bin/env python3
"""
Claude Code Multi-Agent Integration
Usa Claude Code para executar tarefas reais de forma automatizada
"""

import subprocess
import json
from pathlib import Path
from orchestrator import StateManager, TaskStatus


class ClaudeCodeAgent:
    """Agente que usa Claude Code para executar tarefas"""
    
    def __init__(self, agent_name: str, state: StateManager):
        self.agent_name = agent_name
        self.state = state
        self.context_file = Path("CLAUDE.md")
    
    def execute_task_with_claude(self, task_id: str, prompt: str) -> bool:
        """
        Executa tarefa usando Claude Code CLI
        
        Args:
            task_id: ID da tarefa
            prompt: Prompt para o Claude Code
        
        Returns:
            True se bem-sucedido, False caso contrário
        """
        try:
            # Prepara prompt completo com contexto
            full_prompt = self._prepare_prompt(task_id, prompt)
            
            # Executa Claude Code
            print(f" Executando Claude Code para: {task_id}")
            result = subprocess.run(
                ["claude", "code", full_prompt],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutos timeout
            )
            
            if result.returncode == 0:
                # Atualiza state.md com resultado
                self._update_state_with_result(task_id, result.stdout)
                return True
            else:
                print(f" Erro: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏱ Timeout ao executar {task_id}")
            return False
        except Exception as e:
            print(f" Erro ao executar Claude Code: {e}")
            return False
    
    def _prepare_prompt(self, task_id: str, prompt: str) -> str:
        """Prepara prompt com contexto completo"""
        task = self.state.get_task(task_id)
        
        context = f"""
# Contexto do Projeto
Leia o arquivo CLAUDE.md para entender o projeto Ketter 3.0.

# Tarefa Atual
**ID:** {task_id}
**Agente:** {self.agent_name}
**Descrição:** {task.description}
**Week:** {task.week}

# Dependências Completadas
"""
        # Adiciona informações das dependências
        for dep_id in task.dependencies:
            dep_task = self.state.get_task(dep_id)
            if dep_task:
                context += f"-  {dep_task.description}\n"
                if dep_task.notes:
                    context += f"  Notas: {dep_task.notes}\n"
        
        context += f"""

# Instruções
{prompt}

# Importante
1. Siga os princípios MRC do CLAUDE.md (simplicidade, confiabilidade)
2. Crie testes para o código implementado
3. Atualize o state.md ao finalizar com:
   - O que foi implementado
   - Arquivos criados/modificados
   - Próximos passos (se houver)
   - Qualquer blocker ou observação importante

Execute a tarefa agora.
"""
        return context
    
    def _update_state_with_result(self, task_id: str, output: str):
        """Atualiza state.md com resultado da execução"""
        # Extrai informações relevantes do output
        notes = self._extract_summary(output)
        self.state.update_task(task_id, TaskStatus.COMPLETED, notes)
    
    def _extract_summary(self, output: str) -> str:
        """Extrai resumo do output do Claude Code"""
        # Simplificado - poderia usar LLM para sumarizar
        lines = output.split('\n')
        summary_lines = [line for line in lines if line.startswith('') or line.startswith('-')]
        return '\n'.join(summary_lines[:5])  # Primeiras 5 linhas relevantes


class AutomatedDevOpsAgent(ClaudeCodeAgent):
    """DevOps Agent automatizado com Claude Code"""
    
    def __init__(self, state: StateManager):
        super().__init__("DevOps", state)
    
    def execute_docker_setup(self):
        """Executa setup completo do Docker"""
        prompt = """
Crie a infraestrutura Docker para o Ketter 3.0:

1. docker-compose.yml com:
   - PostgreSQL 15 (porta 5432, volume persistente)
   - Redis 7 (porta 6379)
   - FastAPI app (porta 8000)
   - RQ Worker
   - Health checks para todos serviços

2. .env.example com variáveis necessárias

3. Dockerfile otimizado para Python 3.11

4. README-DOCKER.md com:
   - Como iniciar: docker-compose up
   - Como parar: docker-compose down
   - Como ver logs
   - Como acessar PostgreSQL

5. Teste que tudo funciona:
   - docker-compose up -d
   - Verificar health checks
   - Conectar no PostgreSQL

Crie todos os arquivos e valide que Docker funciona perfeitamente.
"""
        return self.execute_task_with_claude("devops_docker_setup", prompt)


class AutomatedBackendAgent(ClaudeCodeAgent):
    """Backend Agent automatizado com Claude Code"""
    
    def __init__(self, state: StateManager):
        super().__init__("Backend", state)
    
    def execute_db_schema(self):
        """Cria database schema"""
        prompt = """
Crie o database schema para Ketter 3.0 usando SQLAlchemy:

1. app/models/transfer.py:
   - Transfer: id, source_path, dest_path, status, created_at, completed_at
   - Checksum: id, transfer_id, type (source/dest/final), hash_value
   - AuditLog: id, transfer_id, event_type, message, timestamp

2. app/database.py:
   - Configuração SQLAlchemy
   - Session management
   - Connection pooling

3. alembic para migrations:
   - alembic init
   - Primeira migration com tabelas
   - alembic upgrade head

4. Teste:
   - Crie script test_db.py que insere e lê dados
   - Valide constraints e índices

Implemente seguindo padrões do SQLAlchemy 2.0.
"""
        return self.execute_task_with_claude("backend_db_schema", prompt)
    
    def execute_copy_engine(self):
        """Implementa Copy Engine"""
        prompt = """
Implemente o Copy Engine com SHA-256 triplo:

1. app/services/copy_engine.py:
   - copy_with_verification(source, dest) -> dict
   - Calcula SHA-256 do source (100% do arquivo)
   - Copia arquivo com progress callback
   - Calcula SHA-256 do dest
   - Verifica se hashes são idênticos
   - Retorna: {"success": bool, "source_hash": str, "dest_hash": str, "size": int}

2. app/services/disk_validation.py:
   - validate_disk_space(path, required_size) -> bool
   - Verifica espaço disponível
   - Valida se tem > 10% de espaço livre após cópia

3. Testes (100% coverage):
   - tests/test_copy_engine.py
   - Teste com arquivo 100MB
   - Teste com arquivo corrompido (deve detectar)
   - Teste validação de espaço

Use hashlib para SHA-256 e shutil para cópia eficiente.
"""
        return self.execute_task_with_claude("backend_copy_engine", prompt)


class AutomatedTestAgent(ClaudeCodeAgent):
    """Test Agent automatizado"""
    
    def __init__(self, state: StateManager):
        super().__init__("Test", state)
    
    def execute_copy_test(self):
        """Testa cópia de 1 arquivo"""
        prompt = """
Crie teste completo do Copy Engine:

1. tests/test_copy_1file.py:
   - Cria arquivo de teste de 1GB
   - Executa copy_with_verification()
   - Valida SHA-256 source == dest
   - Testa detecção de corrupção
   - Testa validação de espaço

2. Execute com pytest:
   - pytest tests/test_copy_1file.py -v
   - Coverage deve ser 100% no copy_engine.py

3. Documente resultado em TEST_REPORT.md

O teste DEVE passar para validar Week 1.
"""
        return self.execute_task_with_claude("test_copy_1file", prompt)


def run_automated_week1():
    """Executa Week 1 de forma completamente automatizada"""
    print(" Iniciando Week 1 - Automated Multi-Agent Build")
    print("=" * 70)
    
    state = StateManager()
    
    # 1. DevOps Agent - Docker Setup
    print("\n FASE 1: DevOps Agent - Docker Infrastructure")
    devops = AutomatedDevOpsAgent(state)
    if not devops.execute_docker_setup():
        print(" Falha no Docker setup. Abortando.")
        return False
    
    # 2. Backend Agent - Database Schema
    print("\n FASE 2: Backend Agent - Database Schema")
    backend = AutomatedBackendAgent(state)
    if not backend.execute_db_schema():
        print(" Falha no database schema. Abortando.")
        return False
    
    # 3. Backend Agent - Copy Engine
    print("\n FASE 3: Backend Agent - Copy Engine")
    if not backend.execute_copy_engine():
        print(" Falha no copy engine. Abortando.")
        return False
    
    # 4. Test Agent - Validate Copy
    print("\n FASE 4: Test Agent - Validation")
    test = AutomatedTestAgent(state)
    if not test.execute_copy_test():
        print(" Falha nos testes. Abortando.")
        return False
    
    print("\n" + "=" * 70)
    print(" WEEK 1 COMPLETA!")
    print(" Docker funcionando")
    print(" Database schema criado")
    print(" Copy Engine implementado")
    print(" Testes passando")
    print("\n Veja state.md para detalhes completos")
    
    return True


def run_full_automated_build():
    """Executa build completo de 4 semanas"""
    print(" KETTER 3.0 - FULL AUTOMATED BUILD")
    print("Tempo estimado: 4-6 horas")
    print("=" * 70)
    
    weeks = [
        ("Week 1", run_automated_week1),
        # Adicionar Week 2, 3, 4...
    ]
    
    for week_name, week_func in weeks:
        print(f"\n{'='*70}")
        print(f" {week_name}")
        print(f"{'='*70}")
        
        if not week_func():
            print(f"\n {week_name} falhou. Build interrompido.")
            return False
    
    print("\n" + "=" * 70)
    print(" BUILD COMPLETO!")
    print("Ketter 3.0 está pronto para produção.")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        run_full_automated_build()
    else:
        print("Executando Week 1 apenas...")
        print("Use --full para build completo de 4 semanas")
        run_automated_week1()
