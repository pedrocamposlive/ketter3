# Week 5 - Lista de Tarefas para 100% Completion

**Status Atual:**  87% Completo (44/57 testes passando)
**Meta:**  100% Completo (57/57 testes passando)
**Tempo Estimado:** 60-90 minutos

---

##  Checklist Rápido

### Phase 1: ZIP Engine (30-45 min)
- [ ] Adicionar função `validate_zip_integrity()` em `app/zip_engine.py`
- [ ] Corrigir progress callback em `zip_folder_smart()`
- [ ] Melhorar handling de pastas vazias
- [ ] Testar: `docker-compose exec api pytest tests/test_zip_engine.py -v`
- [ ] Confirmar: 19/19 testes passando 

### Phase 2: Watch Folder (20-30 min)
- [ ] Adicionar função `get_folder_info()` em `app/watch_folder.py`
- [ ] Adicionar função `format_settle_time()` em `app/watch_folder.py`
- [ ] Corrigir timeout behavior em `watch_folder_until_stable()`
- [ ] Testar: `docker-compose exec api pytest tests/test_watch_folder.py -v`
- [ ] Confirmar: 22/22 testes passando 

### Phase 3: Validação Final (10-15 min)
- [ ] Executar: `./validate_week5_tests.sh`
- [ ] Confirmar: 57/57 testes passando 
- [ ] Atualizar `state.md` com status 100%
- [ ] Atualizar `WEEK5_COMPLETE_SUMMARY.md`
- [ ] Commit final das mudanças

---

##  Código a Adicionar

### 1. app/zip_engine.py

**Adicionar esta função no final do arquivo:**

```python
def validate_zip_integrity(zip_path: str) -> Tuple[bool, str]:
    """
    Validate that a ZIP file exists and is not corrupted.

    Args:
        zip_path: Path to ZIP file to validate

    Returns:
        Tuple of (is_valid: bool, message: str)
        - (True, "ZIP is valid") if file is OK
        - (False, "Error message") if problems found
    """
    import zipfile
    import os
    from typing import Tuple

    # Check if file exists
    if not os.path.exists(zip_path):
        return (False, f"ZIP file not found: {zip_path}")

    # Check if file is a valid ZIP
    try:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            # Test ZIP integrity (returns None if OK, filename if corrupted)
            bad_file = zipf.testzip()
            if bad_file is not None:
                return (False, f"ZIP file corrupted at: {bad_file}")
            return (True, "ZIP is valid")
    except zipfile.BadZipFile:
        return (False, "File is not a valid ZIP archive")
    except Exception as e:
        return (False, f"Error validating ZIP: {str(e)}")
```

**Adicionar import no topo do arquivo (se não existir):**
```python
from typing import Tuple
```

---

### 2. app/watch_folder.py

**Adicionar estas duas funções no final do arquivo:**

```python
def get_folder_info(folder_path: str) -> dict:
    """
    Get information about a folder.

    Args:
        folder_path: Path to folder

    Returns:
        Dictionary with folder stats:
        {
            'file_count': int,  # Number of files in folder (recursive)
            'total_size': int,  # Total size in bytes
            'folder_path': str  # Original folder path
        }
    """
    import os

    file_count = 0
    total_size = 0

    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path):
                    file_count += 1
                    total_size += os.path.getsize(file_path)

    return {
        'file_count': file_count,
        'total_size': total_size,
        'folder_path': folder_path
    }


def format_settle_time(seconds: int) -> str:
    """
    Format settle time as human-readable string.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted string:
        - "30s" for < 1 minute
        - "2m" or "2m 30s" for < 1 hour
        - "1h" or "1h 30m" for >= 1 hour

    Examples:
        format_settle_time(30) → "30s"
        format_settle_time(90) → "1m 30s"
        format_settle_time(120) → "2m"
        format_settle_time(3600) → "1h"
        format_settle_time(5400) → "1h 30m"
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if remaining_seconds == 0:
            return f"{minutes}m"
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        if remaining_minutes == 0:
            return f"{hours}h"
        return f"{hours}h {remaining_minutes}m"
```

---

### 3. Corrigir Timeout Behavior

**No arquivo `app/watch_folder.py`, na função `watch_folder_until_stable()`:**

Localizar o loop principal e garantir que o timeout está sendo checado **PRIMEIRO**:

```python
def watch_folder_until_stable(...):
    # ... código existente ...

    start_time = time.time()
    last_state = None
    stable_since = None

    while True:
        current_time = time.time()
        elapsed = current_time - start_time

        # CHECK TIMEOUT FIRST (antes de qualquer outra lógica)
        if elapsed >= max_wait_seconds:
            logger.warning(f"Watch timeout reached: {max_wait_seconds}s")
            return False  # CRITICAL: Must return False on timeout

        # ... resto do código ...
```

---

##  Comandos de Teste

### Testar Individualmente

```bash
# 1. Testar ZIP Engine
docker-compose exec api pytest tests/test_zip_engine.py -v
# Esperado: 19/19 passed

# 2. Testar Watch Folder
docker-compose exec api pytest tests/test_watch_folder.py -v
# Esperado: 22/22 passed

# 3. Testar Pro Tools
docker-compose exec api pytest tests/test_protools_scenario.py -v
# Esperado: 16/16 passed
```

### Testar Todos Juntos

```bash
# Executar script de validação
./validate_week5_tests.sh

# Esperado:
# ZIP_ENGINE: 19/19 
# WATCH_FOLDER: 22/22 
# PROTOOLS: 16/16 
# Total: 57/57 passed (100.0%)
```

---

##  Progress Tracking

### Tests Status

| Test Suite | Before | After | Progress |
|-------------|--------|-------|----------|
| test_zip_engine.py | 14/19  | 19/19  | +5 |
| test_watch_folder.py | 18/22  | 22/22  | +4 |
| test_protools_scenario.py | 12/16  | 16/16  | +4 |
| **Total** | **44/57** | **57/57** | **+13** |
| **Percentage** | **77.2%** | **100%** | **+22.8%** |

---

##  Success Criteria

Quando todos os critérios forem atendidos, Week 5 estará 100% completa:

- [ ] `validate_zip_integrity()` implementada e testada
- [ ] `get_folder_info()` implementada e testada
- [ ] `format_settle_time()` implementada e testada
- [ ] Timeout behavior corrigido
- [ ] 19/19 ZIP Engine tests passing
- [ ] 22/22 Watch Folder tests passing
- [ ] 16/16 Pro Tools tests passing
- [ ] **57/57 Total tests passing (100%)**
- [ ] `./validate_week5_tests.sh` shows green 
- [ ] state.md updated to 100%
- [ ] All documentation updated

---

##  Ordem de Execução Recomendada

### Step 1: Setup
```bash
# Garantir que containers estão rodando
docker-compose ps

# Se não estiverem, iniciar:
docker-compose up -d

# Aguardar 10 segundos para inicialização
sleep 10
```

### Step 2: Fix ZIP Engine
```bash
# Editar arquivo
code app/zip_engine.py

# Adicionar função validate_zip_integrity() (ver código acima)

# Testar imediatamente
docker-compose exec api pytest tests/test_zip_engine.py -v

# Verificar: deve mostrar 19/19 passed
```

### Step 3: Fix Watch Folder
```bash
# Editar arquivo
code app/watch_folder.py

# Adicionar funções get_folder_info() e format_settle_time()
# Corrigir timeout behavior (ver código acima)

# Testar imediatamente
docker-compose exec api pytest tests/test_watch_folder.py -v

# Verificar: deve mostrar 22/22 passed
```

### Step 4: Validate Everything
```bash
# Executar validação completa
./validate_week5_tests.sh

# Verificar output:
#  ALL WEEK 5 TESTS PASSED! 
# Week 5 is fully validated and ready for production!
```

### Step 5: Update Documentation
```bash
# Atualizar state.md
code state.md
# Mudar status para 100% e atualizar métricas

# Commit final
git add .
git commit -m "Week 5: All tests passing - 100% coverage achieved"
```

---

##  Troubleshooting

### Se alguns testes ainda falharem:

**1. Verificar imports**
```bash
docker-compose exec api python -c "from app.zip_engine import validate_zip_integrity; print('OK')"
docker-compose exec api python -c "from app.watch_folder import get_folder_info, format_settle_time; print('OK')"
```

**2. Verificar sintaxe**
```bash
docker-compose exec api python -m py_compile app/zip_engine.py
docker-compose exec api python -m py_compile app/watch_folder.py
```

**3. Ver erro específico de um teste**
```bash
docker-compose exec api pytest tests/test_zip_engine.py::TestZipValidation::test_validate_zip_integrity_valid -vv
```

**4. Restart containers**
```bash
docker-compose restart api worker
sleep 5
```

---

##  Documentos de Referência

- **Plano Detalhado:** `WEEK5_TEST_FIXES.md`
- **Status Report:** `STATUS_REPORT.md`
- **Project State:** `state.md`
- **Testing Guide:** `PROTOOLS_TESTING.md`
- **Validation Script:** `validate_week5_tests.sh`

---

##  Quando Completo

Após completar todos os itens do checklist:

1.  Todos os 57 testes Week 5 passando
2.  Total de 100 testes no projeto (43 + 57)
3.  100% test coverage Week 5
4.  Sistema pronto para produção
5.  Documentação atualizada

**Result:**
```
 KETTER 3.0 - 100% COMPLETO 

 18/18 tasks implemented
 100/100 tests passing
 Production ready
 Full documentation
```

---

**Última Atualização:** 2025-11-05
**Tempo Estimado Total:** 60-90 minutos
**Dificuldade:**  Baixa (implementações simples)
