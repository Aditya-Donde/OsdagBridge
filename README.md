# OsdagBridge

OsdagBridge is a modular, shared-core software plugin for the analysis and design of steel bridges within the Osdag ecosystem.  
It supports desktop (PySide6), web (Django + React), and CLI interfaces through a unified Python core.

The system currently supports:
- Plate Girder Bridges  
 

Additional bridge types can be added through the plugin architecture.

---

## Key Features

### Shared Core Architecture
All numerical logic and I/O are implemented once in `osdagbridge.core`.  
The desktop GUI, web app, and CLI all reuse the same core for consistent behavior.

### Modular Bridge-Type System
Each bridge type includes:
- DTO (input model schema)
- Initial sizing routines
- Structural analysis configuration
- Design and code-check modules
- CAD geometry generation
- Report generation utilities

### Reusable Bridge Components
Common structural elements are defined in `bridge_components/`:
- Girders  
- Decks  
- Crash barriers  
- Pedestals  
- Piers  
- Foundations  
- Piles and pile caps  

Components are shared across multiple bridge types.

### Multi-Solver Analysis Support
Multiple analysis backends are supported:
- Native lightweight FEM solver  
- OpenSeesPy  
- OspGrillage  

Solvers are switchable at runtime via adapters.

### Integrated Indian Standards
Included under `core/utils/codes/`:
- IRC:6–2017  
- IRC:22–2015  
- IRC:24–2010  

These modules provide load models, combinations, material factors, and code checks.

---

## Project Structure

```
OsdagBridge/
├── docs/
├── examples/
├── tests/
└── src/
    └── osdagbridge/
        ├── core/              # Analysis, design, IO, solvers, codes
        ├── bridge_types/      # Plate girder, box girder, truss
        ├── bridge_components/ # Reusable components
        ├── cli/               # Command-line interface
        ├── desktop/           # PySide6 GUI
        └── web/               # Django + React web stack
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/osdag-admin/OsdagBridge.git
cd OsdagBridge
```

Install in editable mode:

```bash
pip install -e .
```

---

## Usage

### Command-Line Interface

Run an analysis:

```bash
osdagbridge analyze project.yaml --solver native
```

Generate a report:

```bash
osdagbridge report project.yaml report.pdf
```

### Desktop Application

```bash
python -m osdagbridge.desktop
```

### Web Application

Backend:

```bash
python src/osdagbridge/web/backend/manage.py runserver
```

Frontend:

```bash
cd src/osdagbridge/web/frontend
npm install
npm start
```

---

## Testing

Run the complete test suite:

```bash
pytest -q
```

Continuous integration runs automatically through GitHub Actions (`.github/workflows/ci.yml`).

---

## Development Guidelines

### Key Code Locations
- Core logic: `src/osdagbridge/core/`
- Codes & standards: `src/osdagbridge/core/utils/codes/`
- Bridge types: `src/osdagbridge/bridge_types/`
- Components: `src/osdagbridge/bridge_components/`
- CLI: `src/osdagbridge/cli/`
- Desktop GUI: `src/osdagbridge/desktop/`
- Web backend/frontend: `src/osdagbridge/web/`

### Contribution Workflow
1. Fork the repository  
2. Create a feature branch  
3. Ensure all tests pass (`pytest`)  
4. Submit a pull request

---

## Acknowledgements

OsdagBridge is part of the Osdag project, promoting open-source tools for steel design education, research, and practice.

---

## License

This project is licensed under the MIT License.  
See the `LICENSE` file for full details.
