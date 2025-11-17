#!/usr/bin/env python3
"""
Ketter 3.0 - Multi-Agent Orchestrator
Coordena agentes especializados para construir o projeto automaticamente
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class TaskStatus(Enum):
    """Status de uma tarefa"""
    NOT_STARTED = "[ ]"
    IN_PROGRESS = "⏳"
    COMPLETED = ""
    BLOCKED = ""


@dataclass
class Task:
    """Representa uma tarefa individual"""
    id: str
    agent: str
    description: str
    week: int
    status: TaskStatus
    dependencies: List[str]
    completed_at: Optional[str] = None
    notes: str = ""
    
    def to_markdown(self) -> str:
        """Converte task para formato markdown"""
        status_icon = self.status.value
        completion = f" ({self.completed_at})" if self.completed_at else ""
        return f"- [{status_icon}] {self.agent}: {self.description}{completion}"


class StateManager:
    """Gerencia o state.md do projeto"""
    
    def __init__(self, state_file: str = "state.md"):
        self.state_file = state_file
        self.tasks: Dict[str, Task] = {}
        self.load_or_create()
    
    def load_or_create(self):
        """Carrega state.md existente ou cria novo"""
        if os.path.exists(self.state_file):
            self.load()
        else:
            self.initialize()
    
    def initialize(self):
        """Cria state.md inicial com todas as tarefas"""
        # Week 1 tasks
        self.add_task(Task(
            id="devops_docker_setup",
            agent="DevOps",
            description="Docker Compose com PostgreSQL, Redis, API, Worker",
            week=1,
            status=TaskStatus.NOT_STARTED,
            dependencies=[]
        ))
        
        self.add_task(Task(
            id="backend_db_schema",
            agent="Backend",
            description="Database schema (transfers, checksums, logs)",
            week=1,
            status=TaskStatus.NOT_STARTED,
            dependencies=["devops_docker_setup"]
        ))
        
        self.add_task(Task(
            id="backend_copy_engine",
            agent="Backend",
            description="Copy Engine com SHA-256 triplo",
            week=1,
            status=TaskStatus.NOT_STARTED,
            dependencies=["backend_db_schema"]
        ))
        
        self.add_task(Task(
            id="test_copy_1file",
            agent="Test",
            description="Teste de cópia de 1 arquivo com checksum",
            week=1,
            status=TaskStatus.NOT_STARTED,
            dependencies=["backend_copy_engine"]
        ))
        
        # Week 2 tasks
        self.add_task(Task(
            id="backend_api_endpoints",
            agent="Backend",
            description="API REST endpoints completos",
            week=2,
            status=TaskStatus.NOT_STARTED,
            dependencies=["test_copy_1file"]
        ))
        
        self.add_task(Task(
            id="worker_rq_setup",
            agent="Worker",
            description="RQ worker com job transfer_file_job",
            week=2,
            status=TaskStatus.NOT_STARTED,
            dependencies=["backend_copy_engine"]
        ))
        
        self.add_task(Task(
            id="worker_api_integration",
            agent="Worker",
            description="Integração API → Worker via RQ",
            week=2,
            status=TaskStatus.NOT_STARTED,
            dependencies=["backend_api_endpoints", "worker_rq_setup"]
        ))
        
        # Week 3 tasks
        self.add_task(Task(
            id="frontend_react_setup",
            agent="Frontend",
            description="React app com Vite",
            week=3,
            status=TaskStatus.NOT_STARTED,
            dependencies=["worker_api_integration"]
        ))
        
        self.add_task(Task(
            id="frontend_operational_ui",
            agent="Frontend",
            description="UI: file picker + progress + history",
            week=3,
            status=TaskStatus.NOT_STARTED,
            dependencies=["frontend_react_setup"]
        ))
        
        # Week 4 tasks
        self.add_task(Task(
            id="backend_pdf_reports",
            agent="Backend",
            description="Geração de PDF reports profissionais",
            week=4,
            status=TaskStatus.NOT_STARTED,
            dependencies=["frontend_operational_ui"]
        ))
        
        self.add_task(Task(
            id="test_integration",
            agent="Test",
            description="Testes de integração end-to-end",
            week=4,
            status=TaskStatus.NOT_STARTED,
            dependencies=["backend_pdf_reports"]
        ))
        
        self.add_task(Task(
            id="test_500gb",
            agent="Test",
            description="Teste real de 500GB com zero erros",
            week=4,
            status=TaskStatus.NOT_STARTED,
            dependencies=["test_integration"]
        ))
        
        self.save()
    
    def add_task(self, task: Task):
        """Adiciona tarefa ao state"""
        self.tasks[task.id] = task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Obtém tarefa por ID"""
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, status: TaskStatus, notes: str = ""):
        """Atualiza status de uma tarefa"""
        task = self.tasks.get(task_id)
        if task:
            task.status = status
            task.notes = notes
            if status == TaskStatus.COMPLETED:
                task.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.save()
            self.check_unblock_dependencies(task_id)
    
    def check_unblock_dependencies(self, completed_task_id: str):
        """Verifica se tarefas bloqueadas podem ser desbloqueadas"""
        for task in self.tasks.values():
            if task.status == TaskStatus.BLOCKED:
                if completed_task_id in task.dependencies:
                    # Verifica se todas dependências foram completadas
                    deps_complete = all(
                        self.tasks[dep].status == TaskStatus.COMPLETED
                        for dep in task.dependencies
                        if dep in self.tasks
                    )
                    if deps_complete:
                        task.status = TaskStatus.NOT_STARTED
                        print(f" Task {task.id} desbloqueada!")
        self.save()
    
    def get_next_tasks(self, agent: str = None) -> List[Task]:
        """Retorna próximas tarefas disponíveis (sem dependências bloqueadas)"""
        available = []
        for task in self.tasks.values():
            if agent and task.agent != agent:
                continue
            
            if task.status != TaskStatus.NOT_STARTED:
                continue
            
            # Verifica se todas dependências foram completadas
            deps_complete = all(
                self.tasks[dep].status == TaskStatus.COMPLETED
                for dep in task.dependencies
                if dep in self.tasks
            )
            
            if deps_complete:
                available.append(task)
        
        return sorted(available, key=lambda t: t.week)
    
    def get_progress(self, week: int = None) -> Dict:
        """Calcula progresso geral ou por semana"""
        tasks = list(self.tasks.values())
        if week:
            tasks = [t for t in tasks if t.week == week]
        
        total = len(tasks)
        completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        in_progress = len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS])
        
        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "percentage": (completed / total * 100) if total > 0 else 0
        }
    
    def save(self):
        """Salva state.md no formato markdown"""
        with open(self.state_file, 'w') as f:
            f.write(self.to_markdown())
    
    def load(self):
        """Carrega state.md (simplificado - parse markdown)"""
        # Por simplicidade, usamos JSON auxiliar
        json_file = self.state_file.replace('.md', '.json')
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                data = json.load(f)
                self.tasks = {
                    task_id: Task(**task_data)
                    for task_id, task_data in data.items()
                }
    
    def to_markdown(self) -> str:
        """Converte state para markdown"""
        md = "# Ketter 3.0 - Project State\n\n"
        md += f"**Última Atualização:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        # Progress geral
        progress = self.get_progress()
        md += f"## Status Geral: {progress['completed']}/{progress['total']} tasks ({progress['percentage']:.0f}%)\n\n"
        
        # Por semana
        for week in range(1, 5):
            week_tasks = [t for t in self.tasks.values() if t.week == week]
            week_progress = self.get_progress(week)
            
            md += f"## Week {week} ({week_progress['percentage']:.0f}% complete)\n"
            md += f"**Objetivo:** {self._get_week_objective(week)}\n\n"
            
            for task in sorted(week_tasks, key=lambda t: t.id):
                md += task.to_markdown() + "\n"
                if task.notes:
                    md += f"  *{task.notes}*\n"
            md += "\n"
        
        # Next actions
        md += "## Próximas Ações (Prioridade)\n\n"
        next_tasks = self.get_next_tasks()[:5]
        for i, task in enumerate(next_tasks, 1):
            md += f"{i}. **{task.agent} Agent:** {task.description}\n"
        
        md += "\n---\n"
        md += f"*Gerado automaticamente pelo Orchestrator*\n"
        
        # Salva também JSON para facilitar load
        json_file = self.state_file.replace('.md', '.json')
        with open(json_file, 'w') as f:
            json.dump(
                {tid: asdict(t) for tid, t in self.tasks.items()},
                f,
                indent=2,
                default=str
            )
        
        return md
    
    def _get_week_objective(self, week: int) -> str:
        """Retorna objetivo da semana"""
        objectives = {
            1: "Copy 1 file with checksum verification",
            2: "Transfer via API functional",
            3: "Operator can complete full workflow",
            4: "Production-ready system"
        }
        return objectives.get(week, "")


class Agent:
    """Classe base para agentes"""
    
    def __init__(self, name: str, state: StateManager):
        self.name = name
        self.state = state
    
    def execute_task(self, task: Task) -> bool:
        """Executa uma tarefa (implementado por subclasse)"""
        raise NotImplementedError
    
    def run(self):
        """Loop principal do agente"""
        print(f" {self.name} Agent iniciado")
        
        while True:
            tasks = self.state.get_next_tasks(agent=self.name)
            
            if not tasks:
                print(f" {self.name} Agent: Sem tarefas disponíveis")
                break
            
            task = tasks[0]  # Pega primeira tarefa disponível
            print(f" {self.name} executando: {task.description}")
            
            # Atualiza para in progress
            self.state.update_task(task.id, TaskStatus.IN_PROGRESS)
            
            # Executa tarefa
            success = self.execute_task(task)
            
            if success:
                self.state.update_task(
                    task.id,
                    TaskStatus.COMPLETED,
                    f"Completado por {self.name} Agent"
                )
                print(f" {self.name} completou: {task.id}")
            else:
                self.state.update_task(
                    task.id,
                    TaskStatus.BLOCKED,
                    f"Falha ao executar - requer intervenção"
                )
                print(f" {self.name} falhou: {task.id}")
                break


class DevOpsAgent(Agent):
    """Agente responsável por infraestrutura"""
    
    def __init__(self, state: StateManager):
        super().__init__("DevOps", state)
    
    def execute_task(self, task: Task) -> bool:
        """Executa tarefa de DevOps"""
        if task.id == "devops_docker_setup":
            return self.setup_docker()
        return False
    
    def setup_docker(self) -> bool:
        """Cria Docker Compose e configurações"""
        print("  → Criando docker-compose.yml...")
        print("  → Configurando PostgreSQL...")
        print("  → Configurando Redis...")
        print("  → Health checks implementados")
        # Aqui chamaria Claude Code ou criaria arquivos
        return True


class BackendAgent(Agent):
    """Agente responsável por backend"""
    
    def __init__(self, state: StateManager):
        super().__init__("Backend", state)
    
    def execute_task(self, task: Task) -> bool:
        """Executa tarefa de backend"""
        task_handlers = {
            "backend_db_schema": self.create_db_schema,
            "backend_copy_engine": self.implement_copy_engine,
            "backend_api_endpoints": self.create_api_endpoints,
            "backend_pdf_reports": self.implement_pdf_reports
        }
        
        handler = task_handlers.get(task.id)
        if handler:
            return handler()
        return False
    
    def create_db_schema(self) -> bool:
        print("  → Criando tabelas: transfers, checksums, audit_logs")
        return True
    
    def implement_copy_engine(self) -> bool:
        print("  → Implementando SHA-256 triplo")
        print("  → Validação de espaço em disco")
        return True
    
    def create_api_endpoints(self) -> bool:
        print("  → POST /transfers")
        print("  → GET /transfers/history")
        return True
    
    def implement_pdf_reports(self) -> bool:
        print("  → Gerando PDF com reportlab")
        return True


# Implementar outros agentes: WorkerAgent, FrontendAgent, TestAgent...


class Orchestrator:
    """Orquestrador principal"""
    
    def __init__(self):
        self.state = StateManager()
        self.agents = [
            DevOpsAgent(self.state),
            BackendAgent(self.state),
            # Adicionar outros agentes
        ]
    
    def run(self):
        """Executa orquestração completa"""
        print(" Ketter 3.0 Multi-Agent Orchestrator")
        print("=" * 60)
        
        for week in range(1, 5):
            print(f"\n WEEK {week} - {self.state._get_week_objective(week)}")
            print("-" * 60)
            
            # Executa todos agentes para a semana
            for agent in self.agents:
                agent.run()
            
            # Valida milestone da semana
            week_progress = self.state.get_progress(week)
            if week_progress['percentage'] < 100:
                print(f"\n  Week {week} incompleta: {week_progress['percentage']:.0f}%")
                break
            else:
                print(f"\n Week {week} completada!")
        
        print("\n" + "=" * 60)
        print(" Resultado Final:")
        total_progress = self.state.get_progress()
        print(f"   {total_progress['completed']}/{total_progress['total']} tasks completadas")
        print(f"   Progresso: {total_progress['percentage']:.0f}%")


if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.run()
