# 📁 Repository Structure - Complete Overview

## New Organized Structure

```
siteguardAI/
│
├── 📁 app/                          # Main Application Code
│   ├── __init__.py
│   ├── core/                        # Core Functionality
│   │   ├── __init__.py
│   │   ├── vision/                  # Computer Vision
│   │   │   ├── __init__.py
│   │   │   └── detector.py          # PPE Detection (YOLOv8)
│   │   └── llm/                     # LLM Integration
│   │       ├── __init__.py
│   │       └── generator.py         # Report Generation
│   ├── api/                         # FastAPI Backend
│   │   ├── __init__.py
│   │   └── main.py                  # API Endpoints
│   └── web/                         # Streamlit Dashboard
│       ├── __init__.py
│       └── streamlit_app.py         # Web Interface
│
├── 📁 utils/                        # Utility Functions
│   ├── __init__.py
│   └── config.py                    # Configuration Management
│
├── 📁 tests/                        # Test Suite
│   ├── __init__.py
│   ├── test_detector.py             # Vision tests
│   ├── test_generator.py            # LLM tests
│   └── test_integration.py          # Integration tests
│
├── 📁 scripts/                      # Utility Scripts
│   ├── download_model.py            # Download YOLO model
│   ├── run_api.py                   # Start API server
│   ├── run_web.py                   # Start web dashboard
│   └── setup_env.py                 # Environment setup
│
├── 📁 docs/                         # Documentation
│   ├── DEPLOYMENT.md                # Deployment guide
│   ├── PROJECT_OVERVIEW.md          # Technical overview
│   ├── QUICKSTART.md                # Quick reference
│   ├── SETUP_FOR_DEMO.md            # Demo setup
│   └── CONTRIBUTING.md              # Development guidelines
│
├── 📁 data/                         # Data Storage
│   ├── uploads/                     # Uploaded images
│   │   └── .gitkeep
│   └── outputs/                     # Detection results
│       └── .gitkeep
│
├── 📁 models/                       # YOLO Models
│   └── .gitkeep                     # (models downloaded here)
│
├── 📄 requirements.txt              # Python dependencies
├── 📄 config.yaml                   # Application configuration
├── 📄 .env.example                  # Environment template
├── 📄 .gitignore                    # Git ignore rules
├── 📄 docker-compose.yaml           # Docker configuration
├── 📄 Makefile                      # Build automation
├── 📄 pytest.ini                    # Test configuration
├── 📄 .pylintrc                     # Linting rules
├── 📄 LICENSE                       # MIT License
├── 📄 README.md                     # Main documentation
├── 📄 START_HERE.md                 # Getting started guide
└── 📄 __init__.py                   # Package initialization

## Key Improvements

### 1. Separation of Concerns
- **app/core**: Core business logic (detection & reporting)
- **app/api**: REST API layer
- **app/web**: Web interface layer
- **utils**: Shared utilities
- **scripts**: Standalone scripts
- **tests**: Comprehensive test suite

### 2. Better Organization
- All documentation in `docs/`
- All tests in `tests/`
- All utilities in `scripts/`
- Data storage in `data/`
- Models in `models/`

### 3. Configuration Management
- `.env.example` - Environment template
- `config.yaml` - Application settings
- `.gitignore` - Proper ignore rules
- `pytest.ini` - Test configuration

### 4. Professional Structure
- Proper Python package structure with `__init__.py` files
- Clear module separation
- Easy imports and navigation
- CI/CD ready structure

## Module Dependencies

```
app/core/vision/detector.py
    ├── ultralytics (YOLOv8)
    ├── opencv-python
    └── numpy

app/core/llm/generator.py
    ├── openai (GPT-4o)
    ├── google-generativeai (Gemini)
    └── loguru

app/api/main.py
    ├── fastapi
    ├── uvicorn
    └── app.core.*

app/web/streamlit_app.py
    ├── streamlit
    └── app.core.*

utils/config.py
    ├── python-dotenv
    ├── pyyaml
    └── loguru
```

## Import Patterns

### From Root Scripts
```python
from app.core.vision.detector import PPEDetector, create_detector
from app.core.llm.generator import ReportGenerator, create_report_generator
from utils.config import load_config, get_detector_config
```

### From App Modules
```python
from app.core.vision.detector import PPEDetector
from app.core.llm.generator import ReportGenerator
```

## Running the Application

### Setup
```bash
python scripts/setup_env.py          # Create directories
pip install -r requirements.txt      # Install dependencies
python scripts/download_model.py     # Download YOLO model
```

### Run Web Dashboard
```bash
python scripts/run_web.py
# Opens at http://localhost:8501
```

### Run API Server
```bash
python scripts/run_api.py
# API docs at http://localhost:8000/docs
```

### Run Tests
```bash
pytest tests/ -v
```

### Using Docker
```bash
docker-compose up -d
```

## Data Flow

```
Image Input
    ↓
PPEDetector (app/core/vision/detector.py)
    ↓
Detection Results + Violations
    ↓
ReportGenerator (app/core/llm/generator.py)
    ↓
Incident Report
    ↓
Output (Web UI / API Response)
```

## Configuration Flow

```
.env file → Environment Variables
    ↓
config.yaml → Application Config
    ↓
utils/config.py → Config Objects
    ↓
App Modules → Runtime Configuration
```

## File Purposes

### Core Application
- `app/core/vision/detector.py` - YOLOv8 PPE detection engine
- `app/core/llm/generator.py` - LLM-based report generation
- `app/api/main.py` - FastAPI REST endpoints
- `app/web/streamlit_app.py` - Interactive web dashboard

### Configuration
- `utils/config.py` - Configuration management
- `config.yaml` - Default settings
- `.env.example` - Environment template

### Scripts
- `scripts/download_model.py` - Model download utility
- `scripts/run_api.py` - API server launcher
- `scripts/run_web.py` - Web app launcher
- `scripts/setup_env.py` - Environment setup

### Tests
- `tests/test_detector.py` - Vision module tests
- `tests/test_generator.py` - LLM module tests
- `tests/test_integration.py` - Integration tests

### Documentation
- `README.md` - Main project documentation
- `START_HERE.md` - Quick start guide
- `docs/` - Detailed documentation

## Benefits of New Structure

1. **Modularity**: Clear separation of concerns
2. **Scalability**: Easy to add new features
3. **Maintainability**: Organized codebase
4. **Testability**: Comprehensive test structure
5. **Professional**: Industry-standard layout
6. **CI/CD Ready**: Easy to integrate with pipelines
7. **Documentation**: Well-organized docs
8. **Configuration**: Flexible config management

## Next Steps

1. Copy `.env.example` to `.env` and add API keys
2. Run `python scripts/setup_env.py`
3. Install dependencies: `pip install -r requirements.txt`
4. Download model: `python scripts/download_model.py`
5. Run tests: `pytest tests/`
6. Start application: `python scripts/run_web.py` or `python scripts/run_api.py`

---

**Repository fully organized and production-ready! 🚀**
