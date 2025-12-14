# MultiDefault - Multi-Source Configuration Loader

**Data**: 2025-11-27
**Origine**: genro-asgi Block 04-01 (config module)
**Status**: 🟡 APPROVATO (architettura)

---

## Decisioni Prese

1. **MultiDefault**: Nuova classe che carica da varie sorgenti e appiattisce
2. **SmartOptions invariato**: Resta piatto, nessuna modifica
3. **Appiattimento con `_`**: `{'server': {'host': 'x'}}` → `{'server_host': 'x'}`
4. **dictExtract per raggruppare**: Se serve, già esiste

---

## Architettura

```
MultiDefault(*sources)
    ↓ resolve() + flatten
dict PIATTO
    ↓
SmartOptions(incoming, defaults)  ← invariato
    ↓
opts.server_host, opts.server_port, ...
```

---

## MultiDefault

### Signature

```python
class MultiDefault:
    def __init__(self, *sources, skip_missing: bool = False):
        """
        Carica configurazione da multiple sorgenti e appiattisce.

        Args:
            *sources: Sorgenti in ordine di priorità crescente.
                - dict: usato direttamente
                - str path: file .ini/.toml/.yaml/.json (auto-detect)
                - 'ENV:PREFIX': env vars con prefisso
                - Path: file come pathlib.Path
            skip_missing: Se True, ignora file mancanti invece di errore.
        """
```

### Sorgenti Supportate

| Tipo | Esempio | Significato |
|------|---------|-------------|
| `dict` | `{'a': 1}` | Dict literal (già piatto o annidato) |
| `str` file | `'config.ini'` | File (auto-detect da estensione) |
| `str` ENV | `'ENV:PREFIX'` | Env vars con prefisso |
| `Path` | `Path('config.ini')` | File come pathlib.Path |

### Formati File

| Estensione | Parser | Dipendenza |
|------------|--------|------------|
| `.ini` | `configparser` | stdlib |
| `.json` | `json` | stdlib |
| `.toml` | `tomllib` / `tomli` | stdlib 3.11+ / opzionale |
| `.yaml`, `.yml` | `pyyaml` | opzionale |

### Appiattimento

```python
# Input (da .ini o dict annidato)
{
    'server': {'host': 'localhost', 'port': 8000},
    'logging': {'level': 'INFO'},
    'debug': True,
}

# Output (appiattito con _)
{
    'server_host': 'localhost',
    'server_port': 8000,
    'logging_level': 'INFO',
    'debug': True,
}
```

### Env Vars Pattern

Pattern: `{PREFIX}_{KEY}` o `{PREFIX}_{SECTION}_{KEY}`

```bash
export MYAPP_SERVER_HOST=localhost
export MYAPP_SERVER_PORT=9000
export MYAPP_DEBUG=true
```

Diventa (appiattito):
```python
{
    'server_host': 'localhost',
    'server_port': 9000,
    'debug': True,
}
```

### Conversione Tipi Automatica

Per valori stringa (da .ini e env):

| Stringa | Tipo Python |
|---------|-------------|
| `"123"` | `int` |
| `"12.5"` | `float` |
| `"true"`, `"false"`, `"yes"`, `"no"`, `"on"`, `"off"` | `bool` |
| `"none"`, `"null"` | `None` |
| tutto il resto | `str` |

### API

```python
class MultiDefault:
    def __init__(self, *sources, skip_missing: bool = False): ...

    def resolve(self) -> dict[str, Any]:
        """Risolve tutte le sorgenti, appiattisce, ritorna dict."""

    # Mapping protocol (per compatibilità con SmartOptions defaults)
    def __iter__(self) -> Iterator[str]: ...
    def __getitem__(self, key: str) -> Any: ...
    def __len__(self) -> int: ...
    def items(self) -> ItemsView[str, Any]: ...
    def keys(self) -> KeysView[str]: ...
    def values(self) -> ValuesView[Any]: ...
```

---

## Esempio Uso Completo

```python
from genro_toolbox import SmartOptions, MultiDefault

# Definizione sorgenti (priorità crescente)
defaults = MultiDefault(
    {'server_host': '0.0.0.0', 'server_port': 8000},  # base
    'config/base.ini',                                  # file
    'config/local.ini',                                 # override locale
    'ENV:MYAPP',                                        # env vars
    skip_missing=True,
)

# SmartOptions con incoming che override tutto
opts = SmartOptions(
    incoming={'server_port': 9999},  # override finale
    defaults=defaults,
)

# Accesso
opts.server_host    # da file o env
opts.server_port    # 9999 (da incoming)

# Se serve raggruppare
from genro_toolbox import dictExtract

server_config = dictExtract(opts.as_dict(), 'server_')
# {'host': '...', 'port': 9999}
```

---

## Struttura File

```
src/genro_toolbox/
├── dict_utils.py          # SmartOptions, dictExtract (invariato)
├── multi_default.py       # MultiDefault (nuovo)
└── __init__.py            # esporta MultiDefault
```

---

## Test Cases

### MultiDefault

1. Singola sorgente dict piatto
2. Singola sorgente dict annidato → appiattito
3. Singola sorgente file .ini → appiattito
4. Singola sorgente file .json
5. Singola sorgente ENV:PREFIX
6. Catena di sorgenti (priorità)
7. File mancante con skip_missing=False → FileNotFoundError
8. File mancante con skip_missing=True → skip
9. Formato non supportato → ValueError
10. Mapping protocol funziona con SmartOptions

### Conversione Tipi

1. "123" → int
2. "12.5" → float
3. "true"/"false"/"yes"/"no" → bool
4. "none"/"null" → None
5. stringa normale → str

### Integrazione

1. MultiDefault + SmartOptions funziona
2. incoming override su MultiDefault
3. dictExtract per raggruppare

---

## Uso in genro-asgi

```python
from genro_toolbox import SmartOptions, MultiDefault

DEFAULTS = {
    'server_host': '127.0.0.1',
    'server_port': 8000,
    'server_debug': False,
    'logging_level': 'INFO',
}

class AsgiServer:
    def __init__(self, config_path: str | None = None):
        sources = [DEFAULTS]
        if config_path:
            sources.append(config_path)
        sources.append('ENV:GENRO_ASGI')

        self.config = SmartOptions(
            defaults=MultiDefault(*sources, skip_missing=True)
        )

        # Uso
        self.host = self.config.server_host
        self.port = self.config.server_port
```

---

## Prossimi Passi

1. ✅ Discussione preliminare completata
2. ✅ Architettura approvata
3. ⬜ Docstring modulo multi_default.py
4. ⬜ Test
5. ⬜ Implementazione
6. ⬜ Export in __init__.py
7. ⬜ Commit
8. ⬜ Torna a genro-asgi

---

**Ultima modifica**: 2025-11-27
