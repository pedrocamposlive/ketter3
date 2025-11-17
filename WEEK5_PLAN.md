# Week 5: ZIP Smart + Watch Folder Intelligence

**Status:** Planning
**Data:** 2025-11-05
**Objetivo:** Support Pro Tools session workflows without over-engineering

##  Problema a Resolver

**Cenário Real:** Estúdios de dublagem com sessões Pro Tools
- 1.000 arquivos de 1MB cada (áudio, metadata, settings)
- Transferência do client → servidor origem → servidor destino
- Necessidade de garantir integridade de TODOS os arquivos
- Sistema atual: só funciona com 1 arquivo por vez

##  Solução: MRC-Compliant

### Princípios Mantidos:
-  **Simplicidade** - ZIP é simples e universal
-  **Confiabilidade** - Triple SHA-256 no .zip garante integridade
-  **Transparência** - Operador vê claramente o processo
-  **Sem over-engineering** - Não adiciona complexidade desnecessária

### 2 Funcionalidades Novas:

## 1.  ZIP Smart Engine

**O que faz:**
- Detecta se source_path é pasta (não arquivo)
- Empacota automaticamente usando ZIP **STORE mode** (sem compressão)
- Mantém estrutura de pastas original
- Calcula triple SHA-256 do arquivo .zip
- Auto-descompacta no destino após verificação

**Por que STORE mode (sem compressão)?**
- Áudio já está comprimido (WAV, MP3, AAC)
- Compressão adicional é desperdício de CPU
- Store mode = cópia bit-a-bit dentro do container
- Velocidade: ~100-200 MB/s vs 20-50 MB/s (compressed)

**Fluxo:**
```
1. Operador seleciona: /path/to/protools_session/ (folder)
2. Sistema detecta: É pasta? → SIM
3. Status: "Zipping... (store mode)"
4. Cria: protools_session.zip (1.02 GB, 1000 files)
5. Triple SHA-256 no .zip
6. Transfer: protools_session.zip → destino
7. Verifica checksums
8. Status: "Unzipping..."
9. Descompacta no destino
10. Status: "Completed"
```

**Database changes:**
```python
# Adicionar campos ao Transfer model
is_folder_transfer = Column(Boolean, default=False)
original_folder_path = Column(String(4096), nullable=True)
zip_file_path = Column(String(4096), nullable=True)
file_count = Column(Integer, nullable=True)
unzip_completed = Column(Boolean, default=False)
```

## 2.  Watch Folder Intelligence

**O que faz:**
- Monitora pasta origem aguardando transferência do client terminar
- "Settle time" - aguarda X segundos sem modificações
- Auto-inicia transfer quando pasta está estável
- Evita copiar arquivos pela metade

**Settle Time Detection:**
```python
# Algoritmo simples e confiável
1. Listar todos os arquivos na pasta
2. Guardar: (path, size, mtime) de cada arquivo
3. Aguardar 30 segundos (configurável)
4. Listar novamente
5. Comparar: Se NADA mudou → Pasta estável
6. Auto-iniciar transfer
```

**Por que 30 segundos?**
- Pro Tools session: ~1-2 GB → demora 30-60s para transferir via rede
- Se nada mudou em 30s, transferência provavelmente terminou
- Configurável: usuário pode ajustar (15s, 60s, 120s)

**Database changes:**
```python
# Adicionar campos ao Transfer model
watch_mode_enabled = Column(Boolean, default=False)
settle_time_seconds = Column(Integer, default=30)
watch_started_at = Column(DateTime, nullable=True)
watch_triggered_at = Column(DateTime, nullable=True)
```

**UI Controls:**
```
 Watch Mode (aguardar pasta estabilizar)
    Settle time: [30] segundos
```

##  Tasks Detalhadas

### Task 1: Backend - ZIP Smart Engine (2-3h)

**Arquivos a criar/modificar:**

1. **`app/zip_engine.py`** (novo, ~400 lines)
```python
def is_directory(path: str) -> bool
def count_files_recursive(path: str) -> tuple[int, int]  # (count, total_bytes)
def zip_folder_smart(source_folder: str, zip_path: str, progress_callback) -> str
def unzip_folder_smart(zip_path: str, dest_folder: str, progress_callback) -> str
def validate_zip_integrity(zip_path: str) -> bool
```

2. **`app/models.py`** (modificar)
```python
# Add to Transfer model:
is_folder_transfer = Column(Boolean, default=False)
original_folder_path = Column(String(4096), nullable=True)
zip_file_path = Column(String(4096), nullable=True)
file_count = Column(Integer, nullable=True)
unzip_completed = Column(Boolean, default=False)
```

3. **`app/copy_engine.py`** (modificar)
```python
# Update transfer_file_with_verification() para:
# 1. Detectar se é folder
# 2. Se SIM: chamar zip_folder_smart() primeiro
# 3. Processar .zip com triple SHA-256
# 4. Após verification: chamar unzip_folder_smart()
```

4. **`alembic/versions/xxx_add_folder_support.py`** (migration)

**Testes unitários:**
- `tests/test_zip_engine.py` - 8 testes

### Task 2: Backend - Watch Folder Intelligence (1-2h)

**Arquivos a criar/modificar:**

1. **`app/watch_folder.py`** (novo, ~200 lines)
```python
def get_folder_state(path: str) -> dict  # {file: (size, mtime)}
def compare_folder_states(state1: dict, state2: dict) -> bool  # True = stable
def watch_folder_until_stable(path: str, settle_time: int, callback) -> bool
```

2. **`app/models.py`** (modificar)
```python
# Add to Transfer model:
watch_mode_enabled = Column(Boolean, default=False)
settle_time_seconds = Column(Integer, default=30)
watch_started_at = Column(DateTime, nullable=True)
watch_triggered_at = Column(DateTime, nullable=True)
```

3. **`app/worker_jobs.py`** (modificar)
```python
def watch_and_transfer_job(transfer_id: int) -> dict:
    """
    Novo job que:
    1. Watch folder até estável
    2. Executa transfer_file_job()
    """
```

4. **`alembic/versions/xxx_add_watch_mode.py`** (migration)

**Testes:**
- `tests/test_watch_folder.py` - 5 testes

### Task 3: API - Novos Endpoints (30min)

**Arquivos a modificar:**

1. **`app/schemas.py`** (adicionar campos)
```python
class TransferCreate(BaseModel):
    source_path: str
    destination_path: str
    watch_mode_enabled: bool = False  # NOVO
    settle_time_seconds: int = 30     # NOVO

class TransferResponse(BaseModel):
    # ... campos existentes
    is_folder_transfer: bool = False   # NOVO
    file_count: Optional[int] = None   # NOVO
    watch_mode_enabled: bool = False   # NOVO
```

2. **`app/routers/transfers.py`** (lógica)
```python
@router.post("/transfers")
def create_transfer(...):
    # Detectar se é folder
    is_folder = os.path.isdir(source_path)

    # Se watch_mode: usar watch_and_transfer_job
    # Se não: usar transfer_file_job normal
```

### Task 4: Frontend - UI Updates (1-2h)

**Arquivos a modificar:**

1. **`frontend/src/components/FilePicker.jsx`**
```jsx
// Adicionar:
- Checkbox "Watch Mode"
- Input "Settle Time (seconds)"
- Preview de folder contents (se pasta)
```

2. **`frontend/src/components/TransferProgress.jsx`**
```jsx
// Adicionar status:
- "Watching folder..." (amarelo)
- "Zipping folder..." (azul)
- "Unzipping..." (azul)
- Mostrar file_count se folder transfer
```

3. **`frontend/src/services/api.js`**
```javascript
export async function createTransfer(
  sourcePath,
  destPath,
  watchMode = false,
  settleTime = 30
) {
  // Passar novos params
}
```

### Task 5: Testing - Pro Tools Scenario (1h)

**Arquivos a criar:**

1. **`tests/test_protools_scenario.py`** (novo, ~300 lines)
```python
def test_1000_files_zip_smart():
    """Test with 1000 files (1MB each) = 1GB session"""
    # Create 1000 dummy files
    # Trigger transfer
    # Verify ZIP created
    # Verify triple SHA-256
    # Verify unzip at destination

def test_watch_folder_detection():
    """Test watch mode waits for client transfer"""
    # Create folder
    # Start watch mode transfer
    # Simulate client adding files gradually
    # Verify transfer waits
    # Stop adding files
    # Verify transfer starts after settle time
```

2. **`PROTOOLS_TESTING.md`** (documentação)

### Task 6: Documentation (30min)

**Arquivos a criar/modificar:**

1. **`WEEK5_README.md`** - Documentação completa
2. **`state.md`** - Atualizar com Week 5
3. **`PROJECT_README.md`** - Adicionar ZIP Smart + Watch Folder

##  Impacto Esperado

### Performance Comparison:

| Cenário | Sistema Atual | Com ZIP Smart |
|---------|---------------|---------------|
| 1000 files × 1MB |  Não suportado |  ~2-3 minutos |
| Database records | 1000 transfers | 1 transfer |
| Checksums | 3000 hashes | 3 hashes (do .zip) |
| UI entries | 1000 linhas | 1 linha |
| Operator clicks | 1000 clicks | 1 click |

### Sessão Pro Tools Real (1.02 GB, 1000 arquivos):

```
1. Client → Origem: ~30-60s (network)
2. Watch Mode: aguarda 30s (settle time)
3. ZIP Smart: ~5-10s (store mode, sem compress)
4. Triple SHA-256: ~20-30s (1 GB)
5. Transfer: ~50-60s (1 GB network copy)
6. Verification: ~20-30s (dest SHA-256)
7. Unzip: ~5-10s (extract)

Total: ~3-4 minutos (automatic)
vs ~30-60 minutos (1000 transfers individuais)
```

##  Garantias MRC Mantidas

-  **Simplicidade:** ZIP é universal, nada de frameworks complexos
-  **Confiabilidade:** Triple SHA-256 no .zip garante integridade de TODOS os arquivos
-  **Transparência:** Operador vê cada passo (zipping, watching, unzipping)
-  **Testes:** 100% test coverage mantido
-  **Docker:** Tudo containerizado, funciona sem workarounds

##  O Que NÃO Vamos Fazer (Anti-Over-Engineering)

-  Processamento paralelo de múltiplos arquivos
-  File watcher com inotify/fsevents (complexo)
-  Compression algorithms avançados
-  Deduplicação
-  Delta sync / rsync-style
-  Multi-user access control
-  WebSocket real-time (polling continua simples)

##  Timeline

**Total: ~6-8 horas de desenvolvimento**

- Task 1 (ZIP Engine): 2-3h
- Task 2 (Watch Folder): 1-2h
- Task 3 (API): 30min
- Task 4 (Frontend): 1-2h
- Task 5 (Testing): 1h
- Task 6 (Docs): 30min

**Cronograma:**
- Sessão 1 (3h): Tasks 1-2 (Backend core)
- Sessão 2 (2h): Tasks 3-4 (API + Frontend)
- Sessão 3 (2h): Tasks 5-6 (Testing + Docs)

##  Critérios de Sucesso (Week 5)

1.  Copiar pasta com 1000 arquivos em <5 minutos
2.  ZIP Smart (store mode) funciona perfeitamente
3.  Triple SHA-256 do .zip valida integridade de todos os arquivos
4.  Watch folder detecta quando client terminou de copiar
5.  Auto-unzip no destino mantém estrutura original
6.  UI mostra progresso claro (zipping, watching, unzipping)
7.  Todos os testes passam (100%)
8.  Validação scripts updated e passing
9.  Zero over-engineering

##  Resultado Final

**Ketter 3.0 + Week 5** será capaz de:

-  Transferir arquivos únicos (Week 1-4)  DONE
-  Transferir pastas inteiras com ZIP Smart (Week 5)
-  Watch folders aguardando client terminar (Week 5)
-  Pro Tools sessions workflow COMPLETO
-  Manter filosofia MRC rigorosamente

---

**Pronto para implementar?** 

Se você aprovar este plano, eu começo a implementação agora!
