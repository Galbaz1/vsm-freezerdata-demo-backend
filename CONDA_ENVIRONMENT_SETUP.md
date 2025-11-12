# Conda Environment Setup - VSM Project

**Last Updated**: November 12, 2025

## Overview

This project uses a **Conda environment** named `vsm-hva` instead of a Python virtual environment (.venv).

## Environment Details

### Activation

**Primary method:**
```bash
conda activate vsm-hva
```

**Alternative method (using provided script):**
```bash
source scripts/activate_env.sh
```

### Environment Information

```
Environment: vsm-hva
Python Version: 3.12.12
Location: /opt/homebrew/anaconda3/envs/vsm-hva
Total Packages: 244
```

### Installed Core Dependencies ✅

All required dependencies are already installed in the `vsm-hva` conda environment:

| Package | Status | Purpose |
|---------|--------|---------|
| pandas | ✅ | Telemetry data analysis |
| weaviate-client | ✅ | Vector database queries |
| dspy-ai | ✅ | Language model framework |
| fastapi | ✅ | Web API framework |
| uvicorn | ✅ | ASGI server |
| elysia | ✅ | Decision tree agent framework |
| litellm | ✅ | Multi-model LLM support |
| spacy | ✅ | NLP processing |
| matplotlib | ✅ | Data visualization |
| pytest | ✅ | Testing framework |
| And 234 more packages... | ✅ | See `conda list` for full list |

## Quick Start Commands

### 1. Activate Environment
```bash
conda activate vsm-hva
```

### 2. Verify Installation
```bash
python --version  # Should be 3.12.12
python -c "import pandas, weaviate, dspy, fastapi; print('✅ All core dependencies found')"
```

### 3. Run Data Analysis
```bash
conda activate vsm-hva
python3 scripts/analyze_telemetry.py
python3 scripts/analyze_manuals.py
```

### 4. Run Tests
```bash
conda activate vsm-hva
pytest
pytest -v tests/test_specific.py
```

### 5. Start Elysia
```bash
conda activate vsm-hva
elysia start
```

## Key Files

### Conda Configuration
- **Script**: `scripts/activate_env.sh` - Bash script to activate Conda environment
- **Location**: Environment stored at `/opt/homebrew/anaconda3/envs/vsm-hva`

### Python Dependencies
- **Configuration**: `pyproject.toml` - Project metadata and dependencies
- **Runtime deps**: 19 core packages + 225 dependencies
- **Dev deps**: pytest, mkdocs, pytest-asyncio, etc.

## Migration from venv to Conda

### Files Updated

The following files have been updated to use `conda activate vsm-hva` instead of `source .venv/bin/activate`:

1. **Agent Rules**
   - `.cursor/rules/always/agent.mdc` - Updated all Python command instructions

2. **Scripts**
   - `scripts/run_all_plan_tests.py` - Updated usage documentation

3. **Documentation**
   - `docs/QUICK_START_BACKEND_ACCESS.md` - Updated quick start instructions
   - `docs/ACCESSING_TREE_SESSION_DATA.md` - Updated script activation
   - `docs/LLM_MODEL_VERIFICATION.md` - Updated test script commands

4. **Other documentation** (to be reviewed)
   - `docs/plans/TEST_RESULTS_SUMMARY.md` - Contains venv references
   - `docs/CONFIG_MISMATCH_INVESTIGATION.md` - Contains venv references
   - `docs/PROMPT_IMPROVEMENTS_SUMMARY.md` - Contains venv references
   - `docs/offical/start_here/adding_data.md` - Contains venv references

## Dependency Verification

To verify that all dependencies are properly installed:

```bash
conda activate vsm-hva

# Check Python version
python --version

# Check key packages
python -c "
import sys
deps = ['pandas', 'weaviate', 'dspy', 'fastapi', 'uvicorn', 'pytest', 'pytest-asyncio']
print('Checking critical dependencies...')
for dep in deps:
    try:
        __import__(dep.replace('-', '_'))
        print(f'  ✅ {dep}')
    except ImportError:
        print(f'  ❌ {dep}')
"

# View all installed packages
conda list
```

## Managing the Environment

### Install Additional Packages
```bash
conda activate vsm-hva
conda install package_name
# or
pip install package_name
```

### Update Packages
```bash
conda activate vsm-hva
conda update --all
```

### Export Environment (for sharing)
```bash
conda env export > vsm-hva-environment.yml
```

### Create Environment from Export
```bash
conda env create -f vsm-hva-environment.yml
```

## Troubleshooting

### "conda: command not found"
If Conda is not in your PATH:
```bash
# Initialize conda
/opt/homebrew/anaconda3/bin/conda init
# Then restart terminal
```

### "No module named X" after activation
The environment might not be properly activated:
```bash
# Verify activation
which python  # Should show /opt/homebrew/anaconda3/envs/vsm-hva/bin/python
python --version  # Should show 3.12.12
```

### Environment not showing in `conda env list`
Try refreshing conda's cache:
```bash
conda clean --all
conda env list
```

## Environment Specifications

### Python
- **Version**: 3.12.12 (Anaconda)
- **Binary**: `/opt/homebrew/anaconda3/envs/vsm-hva/bin/python`

### Core Dependencies (from pyproject.toml)
- apscheduler==3.11.0
- bcrypt>=4.3.0
- dspy-ai>=3.0.0
- fastapi[standard]>=0.115.11
- httpx==0.28.1
- pympler==1.1
- python-multipart==0.0.18
- rich>=13.7.1,<=14.0.0
- blis>=1.2.0,<1.3.0
- spacy==3.8.7
- uvicorn[standard]==0.35.0
- weaviate-client>=4.16.7
- nest_asyncio==1.6.0
- psutil==7.0.0
- cryptography>=44.0.3
- matplotlib>=3.10.3
- litellm>=1.74.15,<1.76.0
- thinc>=8.3.4,<8.4.0
- pip>=25.2

### Development Dependencies (optional)
- accelerate==1.5.2
- deepeval>=3.2.6
- pytest>=7.4.4
- pytest-asyncio>=0.21.2
- setuptools==78.1.0
- mkdocs-material[imaging]==9.6.12
- mkdocstrings[python]==0.29.1
- pillow==10.4.0
- cairosvg==2.7.1
- websocket-client==1.8.0
- pytest-cov>=6.2.1

## Environment Variables

Required environment variables (stored in `.env`):
```bash
# Models
BASE_MODEL=gpt-4.1
COMPLEX_MODEL=gemini-2.5-pro
BASE_PROVIDER=openai
COMPLEX_PROVIDER=gemini

# API Keys
OPENAI_API_KEY=sk-proj-***
GOOGLE_API_KEY=AIzaSy***

# Weaviate
WCD_URL=your-cluster-url.gcp.weaviate.cloud
WCD_API_KEY=***
```

## Next Steps

1. **Activate the environment**: `conda activate vsm-hva`
2. **Verify installation**: Run the dependency check above
3. **Update bookmarks**: Replace `.venv/bin/activate` references with `conda activate vsm-hva`
4. **Review remaining docs**: Check the "Files Updated" section for any references you might still need to update

## Additional Resources

- Conda documentation: https://docs.conda.io/
- VSM Project Agent Rules: `.cursor/rules/always/agent.mdc`
- Elysia Documentation: https://weaviate.github.io/elysia/

