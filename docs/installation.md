# Installation

This guide will help you install and set up the Financial Analysis Toolkit on your system.

## Requirements

- **Python 3.11+** (Python 3.12 recommended)
- **pip** package manager
- **Git** (for development installation)

## Installation Methods

### 1. PyPI Installation (Recommended)

Install the latest stable version from PyPI:

```bash
pip install capstone-finance
```

### 2. Development Installation

For development or to get the latest features:

```bash
# Clone the repository
git clone https://github.com/GGcarlson/Financial-Analysis-Toolkit.git
cd Financial-Analysis-Toolkit

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### 3. Docker Installation

For containerized deployment:

```bash
# Build the Docker image
docker build -t financial-analysis-toolkit .

# Run the container
docker run -it financial-analysis-toolkit finance-cli --help
```

## Optional Dependencies

The toolkit supports several optional features through additional dependencies:

### Documentation Dependencies

For building documentation locally:

```bash
pip install capstone-finance[docs]
```

### Performance Dependencies

For enhanced performance with large simulations:

```bash
pip install capstone-finance[performance]
```

### All Dependencies

To install all optional dependencies:

```bash
pip install capstone-finance[dev,docs,performance]
```

## Verification

Verify your installation by running:

```bash
# Check CLI is available
finance-cli --version

# List available strategies
finance-cli list-strategies

# Run a quick test
finance-cli retire --strategy dummy --years 5 --paths 100
```

Or in Python:

```python
import capstone_finance as cf

print(f"Version: {cf.__version__}")
print("Installation successful!")
```

## Virtual Environment Setup

We strongly recommend using a virtual environment:

### Using venv

```bash
# Create virtual environment
python -m venv financial-toolkit-env

# Activate (Linux/Mac)
source financial-toolkit-env/bin/activate

# Activate (Windows)
financial-toolkit-env\Scripts\activate

# Install the toolkit
pip install capstone-finance

# Deactivate when done
deactivate
```

### Using conda

```bash
# Create conda environment
conda create -n financial-toolkit python=3.11

# Activate environment
conda activate financial-toolkit

# Install the toolkit
pip install capstone-finance

# Deactivate when done
conda deactivate
```

## System-Specific Instructions

### Windows

1. **Install Python**: Download from [python.org](https://www.python.org/downloads/)
2. **Install Git**: Download from [git-scm.com](https://git-scm.com/downloads)
3. **Open Command Prompt or PowerShell**
4. **Follow the standard installation steps above**

### macOS

1. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Python and Git**:
   ```bash
   brew install python git
   ```

3. **Follow the standard installation steps above**

### Linux (Ubuntu/Debian)

1. **Update package manager**:
   ```bash
   sudo apt update
   ```

2. **Install Python and Git**:
   ```bash
   sudo apt install python3 python3-pip python3-venv git
   ```

3. **Follow the standard installation steps above**

### Linux (CentOS/RHEL)

1. **Install Python and Git**:
   ```bash
   sudo yum install python3 python3-pip git
   ```

2. **Follow the standard installation steps above**

## Common Issues and Solutions

### Issue: `command not found: finance-cli`

**Solution**: Make sure the Python Scripts directory is in your PATH:

```bash
# Find where pip installs scripts
python -m site --user-base

# Add to PATH (Linux/Mac)
export PATH="$PATH:$(python -m site --user-base)/bin"

# Add to PATH (Windows)
# Add %APPDATA%\Python\Scripts to your PATH environment variable
```

### Issue: Import errors with `capstone_finance`

**Solution**: Make sure you're in the correct virtual environment:

```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Reinstall in the current environment
pip install --force-reinstall capstone-finance
```

### Issue: Permission denied during installation

**Solution**: Use user installation:

```bash
pip install --user capstone-finance
```

### Issue: `ModuleNotFoundError` for optional dependencies

**Solution**: Install the specific optional dependencies:

```bash
# For documentation
pip install mkdocs-material mkdocstrings[python]

# For performance
pip install numba

# For development
pip install pytest black ruff mypy
```

## Development Setup

For contributing to the project:

```bash
# Clone and setup
git clone https://github.com/GGcarlson/Financial-Analysis-Toolkit.git
cd Financial-Analysis-Toolkit

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
pytest

# Run code formatting
black .
ruff check .
mypy .
```

## Upgrading

To upgrade to the latest version:

```bash
# PyPI installation
pip install --upgrade capstone-finance

# Development installation
cd Financial-Analysis-Toolkit
git pull origin main
pip install -e ".[dev]"
```

## Uninstallation

To remove the toolkit:

```bash
pip uninstall capstone-finance

# Remove development directory
rm -rf Financial-Analysis-Toolkit
```

## Next Steps

Once installed, head over to the [Quick Start](quick-start.md) guide to begin using the toolkit!

## Support

If you encounter installation issues:

1. Check the [troubleshooting section](#common-issues-and-solutions) above
2. Search existing [GitHub issues](https://github.com/GGcarlson/Financial-Analysis-Toolkit/issues)
3. Create a new issue with:
   - Your operating system and Python version
   - The exact error message
   - Steps to reproduce the issue