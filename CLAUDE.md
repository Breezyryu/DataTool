# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DataTool is a battery lifecycle testing data analysis project that processes charge/discharge test data from multiple battery testing equipment manufacturers (PNE, Toyo1, Toyo2). The project handles battery performance evaluation data for LGES lithium-ion pouch cells with different chemistries and capacities.

**Important Context**: The actual test data is NOT stored locally. It resides on external PC environments. Code validation should be performed on those systems. The Reference folder contains only sample data structures and documentation.

## Development Commands

### Environment Management
- `python -m venv venv` - Create virtual environment
- `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows) - Activate virtual environment
- `deactivate` - Deactivate virtual environment
- `pip install -r requirements.txt` - Install dependencies
- `pip install -r requirements-dev.txt` - Install development dependencies

### Package Management
- `pip install <package>` - Install a package
- `pip install -e .` - Install project in development mode
- `pip freeze > requirements.txt` - Generate requirements file
- `pip-tools compile requirements.in` - Compile requirements with pip-tools

### Testing Commands
- `pytest` - Run all tests
- `pytest -v` - Run tests with verbose output
- `pytest --cov` - Run tests with coverage report
- `pytest --cov-report=html` - Generate HTML coverage report
- `pytest -x` - Stop on first failure
- `pytest -k "test_name"` - Run specific test by name
- `python -m unittest` - Run tests with unittest

### Code Quality Commands
- `black .` - Format code with Black
- `black --check .` - Check code formatting without changes
- `isort .` - Sort imports
- `isort --check-only .` - Check import sorting
- `flake8` - Run linting with Flake8
- `pylint src/` - Run linting with Pylint
- `mypy src/` - Run type checking with MyPy

### Development Tools
- `python -m pip install --upgrade pip` - Upgrade pip
- `python -c "import sys; print(sys.version)"` - Check Python version
- `python -m site` - Show Python site information
- `python -m pdb script.py` - Debug with pdb

## Technology Stack

### Core Technologies
- **Python** - Primary programming language (3.8+)
- **pip** - Package management
- **venv** - Virtual environment management

### Common Frameworks
- **Django** - High-level web framework
- **Flask** - Micro web framework
- **FastAPI** - Modern API framework with automatic documentation
- **SQLAlchemy** - SQL toolkit and ORM
- **Pydantic** - Data validation using Python type hints

### Data Science & ML
- **NumPy** - Numerical computing
- **Pandas** - Data manipulation and analysis
- **Matplotlib/Seaborn** - Data visualization
- **Scikit-learn** - Machine learning library
- **TensorFlow/PyTorch** - Deep learning frameworks

### Testing Frameworks
- **pytest** - Testing framework
- **unittest** - Built-in testing framework
- **pytest-cov** - Coverage plugin for pytest
- **factory-boy** - Test fixtures
- **responses** - Mock HTTP requests

### Code Quality Tools
- **Black** - Code formatter
- **isort** - Import sorter
- **flake8** - Style guide enforcement
- **pylint** - Code analysis
- **mypy** - Static type checker
- **pre-commit** - Git hooks framework

## Project Structure Guidelines

### File Organization
```
src/
├── package_name/
│   ├── __init__.py
│   ├── main.py          # Application entry point
│   ├── models/          # Data models
│   ├── views/           # Web views (Django/Flask)
│   ├── api/             # API endpoints
│   ├── services/        # Business logic
│   ├── utils/           # Utility functions
│   └── config/          # Configuration files
tests/
├── __init__.py
├── conftest.py          # pytest configuration
├── test_models.py
├── test_views.py
└── test_utils.py
requirements/
├── base.txt            # Base requirements
├── dev.txt             # Development requirements
└── prod.txt            # Production requirements
```

### Naming Conventions
- **Files/Modules**: Use snake_case (`user_profile.py`)
- **Classes**: Use PascalCase (`UserProfile`)
- **Functions/Variables**: Use snake_case (`get_user_data`)
- **Constants**: Use UPPER_SNAKE_CASE (`API_BASE_URL`)
- **Private methods**: Prefix with underscore (`_private_method`)

## Python Guidelines

### Type Hints
- Use type hints for function parameters and return values
- Import types from `typing` module when needed
- Use `Optional` for nullable values
- Use `Union` for multiple possible types
- Document complex types with comments

### Code Style
- Follow PEP 8 style guide
- Use meaningful variable and function names
- Keep functions focused and single-purpose
- Use docstrings for modules, classes, and functions
- Limit line length to 88 characters (Black default)

### Best Practices
- Use list comprehensions for simple transformations
- Prefer `pathlib` over `os.path` for file operations
- Use context managers (`with` statements) for resource management
- Handle exceptions appropriately with try/except blocks
- Use `logging` module instead of print statements

## Testing Standards

### Test Structure
- Organize tests to mirror source code structure
- Use descriptive test names that explain the behavior
- Follow AAA pattern (Arrange, Act, Assert)
- Use fixtures for common test data
- Group related tests in classes

### Coverage Goals
- Aim for 90%+ test coverage
- Write unit tests for business logic
- Use integration tests for external dependencies
- Mock external services in tests
- Test error conditions and edge cases

### pytest Configuration
```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=term-missing"
```

## Virtual Environment Setup

### Creation and Activation
```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Requirements Management
- Use `requirements.txt` for production dependencies
- Use `requirements-dev.txt` for development dependencies
- Consider using `pip-tools` for dependency resolution
- Pin versions for reproducible builds

## Django-Specific Guidelines

### Project Structure
```
project_name/
├── manage.py
├── project_name/
│   ├── __init__.py
│   ├── settings/
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── users/
│   ├── products/
│   └── orders/
└── requirements/
```

### Common Commands
- `python manage.py runserver` - Start development server
- `python manage.py migrate` - Apply database migrations
- `python manage.py makemigrations` - Create new migrations
- `python manage.py createsuperuser` - Create admin user
- `python manage.py collectstatic` - Collect static files
- `python manage.py test` - Run Django tests

## FastAPI-Specific Guidelines

### Project Structure
```
src/
├── main.py              # FastAPI application
├── api/
│   ├── __init__.py
│   ├── dependencies.py  # Dependency injection
│   └── v1/
│       ├── __init__.py
│       └── endpoints/
├── core/
│   ├── __init__.py
│   ├── config.py       # Settings
│   └── security.py    # Authentication
├── models/
├── schemas/            # Pydantic models
└── services/
```

### Common Commands
- `uvicorn main:app --reload` - Start development server
- `uvicorn main:app --host 0.0.0.0 --port 8000` - Start production server

## Security Guidelines

### Dependencies
- Regularly update dependencies with `pip list --outdated`
- Use `safety` package to check for known vulnerabilities
- Pin dependency versions in requirements files
- Use virtual environments to isolate dependencies

### Code Security
- Validate input data with Pydantic or similar
- Use environment variables for sensitive configuration
- Implement proper authentication and authorization
- Sanitize data before database operations
- Use HTTPS for production deployments

## Battery Data Processing Architecture

### Equipment-Specific Data Formats

1. **PNE Equipment**
   - Channel folders: `M01Ch003[003]`, `M01Ch004[004]`, etc.
   - Data in `Restore/` subfolder
   - Files: `ch03_SaveData0001.csv` through `ch03_SaveEndData.csv`
   - Index files: `savingFileIndex_start.csv`, `savingFileIndex_last.csv`
   - 46 columns of detailed test parameters including voltage (µV), current (µA), capacity, temperature

2. **Toyo1/Toyo2 Equipment**
   - Channel folders: `86/`, `93/`, etc.
   - Raw data files: `000001`, `000002`, etc. (no extension)
   - Summary file: `CAPACITY.LOG`
   - Different column structure from PNE data (voltage in V, current in mA)

### Key Data Processing Requirements

- **Dynamic Path Handling**: Always accept `data_path` as input parameter
- **Battery Info Extraction**: Parse battery information from path names (e.g., "LGES_G3_MP1_4352mAh_상온수명")
- **Multi-Format Support**: Handle different CSV structures from PNE vs Toyo equipment
- **Large File Management**: Process sequential data files that can span hundreds of files
- **Unit Conversions**: PNE uses µV/µA units, Toyo uses V/mA units

### Battery Testing Patterns

1. **Capacity Verification** (보증용량): 0.2C charge/discharge cycles
2. **Life Pattern** (수명패턴): Multi-step charge (up to 4 steps) and discharge patterns
3. **RSS Pattern**: State-of-charge resistance measurements at 30%, 50%, 70% SOC

### Voltage Ranges and Protection
- Operating range: 3.0V - 4.53V (typical)
- Protection algorithm adjusts voltage limits after specific cycle counts (201, 251, 301, 1001+)
- Silicon anode cells require voltage adjustment strategies

## Development Workflow

### Data Loading Strategy
```python
def load_battery_data(data_path: str, equipment_type: str):
    """
    Load battery test data from specified path.
    
    Args:
        data_path: Path to battery test data (e.g., "D:\\pne\\LGES_G3_MP1_4352mAh_상온수명")
        equipment_type: One of "PNE", "Toyo1", "Toyo2"
    """
    # Parse battery info from path
    # Load appropriate format based on equipment_type
    # Handle unit conversions
    # Merge multi-file datasets
    pass
```

### Critical Considerations

1. **Memory Management**: Implement chunked reading for large datasets spanning multiple files
2. **Encoding**: Korean text in filenames and documentation - use UTF-8 encoding
3. **Path Flexibility**: Support both forward and backslash path separators
4. **File Processing Order**:
   - For PNE: Load index files first to understand data span
   - For Toyo: Load CAPACITY.LOG for summary, then raw files as needed
5. **Error Handling**: Comprehensive handling for missing/corrupted files

### Before Starting
1. Check Python version compatibility (3.8+)
2. Create and activate virtual environment
3. Install dependencies from requirements files
4. Install data science packages: `pandas`, `numpy`, `matplotlib`

### During Development
1. Use type hints for better code documentation
2. Create mock data generators matching the Reference folder structures
3. Test with small sample datasets before full-scale processing
4. Implement progress tracking for long-running operations

### Before Committing
1. Run full test suite: `pytest`
2. Check code formatting: `black --check .`
3. Sort imports: `isort --check-only .`
4. Run linting: `flake8`
5. Run type checking: `mypy src/`

# Answer in Korean