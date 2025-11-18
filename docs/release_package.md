release-package.md
Ketter 3.0 — Release Package

Versão: 5.1
Data: YYYY-MM-DD
Autor: Engenharia / Coordenação Técnica

1. Objetivo do Pacote

Este documento descreve o pacote oficial de release para a execução, validação e inicialização do Ketter 3.0 em ambientes macOS.
Inclui:

Script de bootstrap validado em execução real

Plano completo de testes (test_plan.md)

Versão final das migrações Alembic

Configurações necessárias para execução do backend

Processo recomendado de smoke test

Este release serve como base de homologação e como referência para desenvolvedores, QA e operações.

2. Conteúdo do Release
2.1 Scripts incluídos
Arquivo	Descrição
scripts/bootstrap_ketter_mac_5.1_fixed.sh	Script completo para preparar o ambiente local em macOS sem Docker (Homebrew, Postgres, Redis, venv, Alembic).
test_plan.md	Guia completo de validação pós-bootstrap, cobrindo Python, Postgres, Redis, Alembic e Uvicorn.
3. Requisitos
3.1 Ambiente

macOS (Intel ou Apple Silicon)

Homebrew funcional

Acesso local ao terminal com permissões elevadas quando necessário

3.2 Dependências principais instaladas pelo script

Python 3.11

PostgreSQL 16

Redis (via Homebrew)

Ambiente virtual .venv

Pacotes Python via requirements.txt

4. Processo de Instalação
4.1 Executar o bootstrap
chmod +x scripts/bootstrap_ketter_mac_5.1_fixed.sh
./scripts/bootstrap_ketter_mac_5.1_fixed.sh


O script executa:

Instalação de dependências via Homebrew

Criação dos usuários ketter_admin e ketter_user

Configuração do PostgreSQL

Configuração do Redis

Criação do .venv

Instalação das dependências Python

Criação automática do arquivo .env

Execução das migrações Alembic

Smoke test do Uvicorn

5. Execução pós-bootstrap
5.1 Ativar ambiente
source .venv/bin/activate

5.2 Carregar variáveis do .env
set -a
source .env
set +a

5.3 Rodar o backend
uvicorn app.main:app --reload

6. Plano de Testes

A documentação completa está em test_plan.md.
Ela valida:

Python 3.11.x

PostgreSQL 16 (connectivity + permissões)

Redis (porta 6379)

Alembic (migrations limpando sem erros)

Uvicorn (porta 8000, resposta HTTP válida)

Todos os testes foram executados e aprovados no ambiente real do desenvolvedor.

7. Observações Operacionais

Alembic depende obrigatoriamente das variáveis do .env.

Sempre carregar o .env antes de rodar Alembic ou backend.

Ferramentas externas como Docker não são necessárias para este release.

Este release é base para homologação interna (QA) antes do próximo build UI + backend integrado.

8. Próximas Etapas

Publicar o pacote de release no repositório.

Criar o documento “Homologação Final” para QA assinar.

A partir deste ponto, liberar o build da UI para teste integrado.

Comandos para commit

Depois de colocar o release-package.md no repositório:

git add release-package.md
git add scripts/bootstrap_ketter_mac_5.1_fixed.sh
git add test_plan.md

git commit -m "Release Package 5.1 — bootstrap macOS + test_plan + release documentation"

git push origin main


Se estiver em outro branch:

git push origin <nome-do-branch>
