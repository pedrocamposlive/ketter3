# Diagramas de Arquitetura - Sistema Multi-Agente Ketter 3.0

## 1. Visão Geral do Sistema

```

                      ENTRADA DO SISTEMA                         

                                
                    
                         CLAUDE.md         
                     (Project Spec)        
                     - 4 week timeline     
                     - MRC principles      
                     - Success criteria    
                    
                                

                    ORCHESTRATOR LAYER                           
                                                                  
      
             ORCHESTRATOR AGENT (Maestro)                     
    - Reads CLAUDE.md                                         
    - Creates state.md with 13 tasks                          
    - Manages dependencies (DAG)                              
    - Validates milestones                                    
    - Coordinates all agents                                  
      

                                
        
                                                      
            
  WEEK 1 AGENTS         WEEK 2 AGENTS         WEEK 3-4     
                                              AGENTS       
                     
   DevOps             Backend            Frontend  
    Agent              Agent              Agent    
                     
                                                      
                     
   Backend            Worker             Backend   
    Agent              Agent              Agent    
                     
                                                          
                                  
     Test                                     Test    
    Agent                                    Agent    
                                  
            
                                                      
        
                                
                    
                          state.md         
                     (Single Source of     
                      Truth)               
                     - Task status         
                     - Progress metrics    
                     - Agent updates       
                     - Next actions        
                    
```

## 2. Fluxo de Dependências (DAG)

```

 DevOps       Docker + DB
 Agent        

        completa
       

 Backend      Database Schema
 Agent        (Week 1)

        completa
       

 Backend      Copy Engine
 Agent        (Week 1)

        completa
       
                       
  
 Test           Worker      
 Agent          Agent       
 (Week 1)       (Week 2)    
  
                       
        completa        completa
                       
  
 Backend        Backend     
 Agent          Agent       
 API            API+Worker  
 (Week 2)       Integration 
  
                       
       
                 completa
                
         
          Frontend    
          Agent       
          (Week 3)    
         
                 completa
                
         
          Backend     
          Agent       
          PDF Reports 
          (Week 4)    
         
                 completa
                
         
          Test        
          Agent       
          Integration 
          + 500GB     
          (Week 4)    
         
                
                
          PRODUCTION READY
```

## 3. Ciclo de Vida de uma Task

```

                    TASK LIFECYCLE                        


    
     NOT_STARTED  [ ] Task criada pelo Orchestrator
    
           
            Todas dependências satisfeitas
           
           
    
     IN_PROGRESS  [⏳] Agent iniciou execução
    
           
           
                                
                                
          
      COMPLETED           BLOCKED   
         []                []     
          
                                
                                 Retry ou
                                 Intervenção manual
                                
            Atualiza            
            state.md     
                          IN_PROGRESS 
                         
                                
                                
           
                     
                     
           
            Desbloqueia     
            dependências    
           
                     
                     
           
            Próximo Agent   
            pode iniciar    
           
```

## 4. Atualização do state.md

```

              AGENT EXECUTES TASK                            

                       
            
              Execute Task       
              (code, test, etc)  
            
                       
            
              Collect Results    
              - Files created    
              - Tests passed     
              - Metrics          
            
                       
            
              Update state.md    
              - Change status    
              - Add timestamp    
              - Add notes        
              - List next steps  
            
                       
            
              Check Dependencies 
              - Find blocked     
              - Validate deps    
              - Unblock if ready 
            
                       
            
              Notify Orchestrator
              - Task complete    
              - Next actions     
              - Any blockers     
            
```

## 5. Integração com Claude Code

```

              CLAUDE CODE INTEGRATION                     



   Agent     
 (Python)    

       
        Prepara prompt com contexto completo
        - Lê CLAUDE.md
        - Lê state.md (dependências completadas)
        - Monta prompt específico da task
       
       

  subprocess.run(["claude", "code", prompt]) 

                   
                   

               Claude Code CLI                        
  - Lê CLAUDE.md e state.md                          
  - Entende contexto do projeto                      
  - Implementa código real                           
  - Cria testes                                      
  - Valida tudo funciona                             
  - Gera documentação                                

                   
                    Retorna resultado
                    - Arquivos criados
                    - Testes executados
                    - Logs
                   
                   

   Agent      Processa output
 (Python)     Atualiza state.md

       
       

  state.md     Task completa
  atualizado  → Próximo agent desbloqueado

```

## 6. Exemplo: Week 1 Timeline

```
16:00                16:30                17:15                18:45                19:30
                                                                                  
    DevOps Agent        Backend Agent       Backend Agent       Test Agent        
    Docker Setup        Database Schema     Copy Engine         Validation        
                                                                                  
                                                                                  
                                                        
 0%   25%  50%  75% 100% 
                                                        
                                                                                  
                                                                                  
                                                                                  
state.md           state.md           state.md           state.md           state.md
[ ] Docker         [] Docker         [] Docker         [] Docker         [] Week 1
[ ] DB Schema      [⏳] DB Schema      [] DB Schema      [] DB Schema       COMPLETE
[ ] Copy Engine    [ ] Copy Engine    [⏳] Copy Engine    [] Copy Engine    
[ ] Test           [ ] Test           [ ] Test           [⏳] Test          
```

## 7. Paralelização Inteligente

```
Week 2 Example - Tasks podem rodar em paralelo quando dependências satisfeitas:

                    
                     Week 1 Done  
                    
                           
                
                                    
                                    
           
          Backend    Worker     Backend  
          API        RQ Setup   API Docs 
                                         
          Agent 1    Agent 2    Agent 3  
           
                                      
                 PARALLEL EXECUTION   
                                      
              
                           
                           
                    
                     Integration  
                     Agent        
                    

Time saved: ~40% vs sequential execution
```

## 8. Estrutura de Arquivos Gerada

```
ketter-3.0/
  CLAUDE.md                    ← Você fornece (spec)
  state.md                     ← Gerado/atualizado por agentes
  orchestrator.py              ← Sistema base
  claude_code_agents.py        ← Automação

  docker-compose.yml           ← DevOps Agent (Week 1)
  .env.example                 ← DevOps Agent

  app/
     main.py                  ← Backend Agent
     models/
       transfer.py             ← Backend Agent (Week 1)
     services/
       copy_engine.py          ← Backend Agent (Week 1)
       disk_validation.py      ← Backend Agent (Week 1)
     api/
        endpoints.py            ← Backend Agent (Week 2)

  worker/
    tasks.py                    ← Worker Agent (Week 2)
    worker.py                   ← Worker Agent (Week 2)

  frontend/
     src/                     ← Frontend Agent (Week 3)
        App.jsx
        components/

  tests/
     test_copy_engine.py         ← Test Agent (Week 1)
     test_integration.py         ← Test Agent (Week 4)
     test_500gb.py               ← Test Agent (Week 4)

Legend:
 = Documentation
 = State tracking
 = Orchestration
 = Automation
 = Infrastructure
 = Configuration
 = Directory
 = Application code
```

## 9. Métricas e Monitoramento

```

              state.md - Metrics Section                

                                                        
  Progress:  31% (4/13 tasks)       
                                                        
  Week 1:  100%                  
  Week 2:    0%                   
  Week 3:    0%                   
  Week 4:    0%                   
                                                        
  Tests:     15/15 passing                            
  Coverage:  100% (core modules)                       
  LOC:       1,245 / 2,000 target                      
  Commits:   18                                        
  Time:      3h 25min / 160h estimated (2% used)       
                                                        

```

## 10. Recuperação de Falhas

```
SCENARIO: Backend Agent falha ao criar Copy Engine


  state.md    mostra status

       
       
[] Backend: Copy Engine - BLOCKED
    Error: ImportError: hashlib not found
    

  Opções de Recuperação:     

                             
 1. Auto-retry:              
    python orchestrator.py   
    --retry backend_copy_    
    engine                   
                             
 2. Manual fix:              
    - Fix import             
    - Update state.md        
    - Continue               
                             
 3. Skip & continue:         
    - Mark as todo           
    - Continue Week 2        
    - Return later           
                             

```

---

## Legenda de Símbolos

-  = Completo
- ⏳ = Em progresso
- [ ] = Não iniciado
-  = Bloqueado/Erro
- → = Próximo passo
-  = Fluxo/Sequência
-  = Conexão vertical
-  = Conexão horizontal
-  = Box/Container

---

*Diagramas v1.0 - Sistema Multi-Agente Ketter 3.0*
