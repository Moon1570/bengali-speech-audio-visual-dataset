# Linting Guide

This project uses [Ruff](https://docs.astral.sh/ruff/) for fast Python linting and code formatting.

## Configuration

The linting configuration is defined in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
select = ["E", "F"]  # E = pycodestyle errors, F = pyflakes
ignore = ["E501"]    # Ignore line-length errors (optional)
exclude = ["resources_from_sir"]
```

### Configuration Details

- **Line Length**: Maximum line length is set to 100 characters
- **Selected Rules**:
  - `E`: pycodestyle errors (PEP 8 style violations)
  - `F`: pyflakes (logical errors like unused imports, undefined variables)
- **Ignored Rules**:
  - `E501`: Line too long errors (since we handle this with line-length setting)
- **Excluded Directories**:
  - `resources_from_sir`: Contains external resources that don't need to follow our linting rules

## Installation

Install Ruff using pip:

```bash
pip install ruff
```

Or if you're using the project's requirements:

```bash
pip install -r requirements.txt
```

## Usage

### Check for Linting Issues

```bash
# Lint all Python files in the project
ruff check .

# Lint specific files or directories
ruff check utils/
ruff check run_pipeline.py
```

### Auto-fix Issues

```bash
# Automatically fix fixable issues
ruff check --fix .

# Fix specific files
ruff check --fix utils/ run_pipeline.py
```

### Format Code

```bash
# Format all Python files
ruff format .

# Format specific files
ruff format utils/ run_pipeline.py
```

### Show Specific Rule Information

```bash
# Show details about a specific rule
ruff rule E402
ruff rule F401
```

## Common Issues and Fixes

### Unused Imports (F401)
```python
# ❌ Bad: Unused import
import os
import sys  # This import is not used

def main():
    print(os.getcwd())

# ✅ Good: Remove unused import
import os

def main():
    print(os.getcwd())
```

### Undefined Variables (F821)
```python
# ❌ Bad: Using undefined variable
def process_video():
    return video_path  # video_path is not defined

# ✅ Good: Define the variable
def process_video(video_path):
    return video_path
```

### Import Order (E402)
```python
# ❌ Bad: Imports after code
print("Starting script...")
import os

# ✅ Good: Imports at the top
import os

print("Starting script...")
```

## IDE Integration

### VS Code

1. Install the Ruff extension
2. Add to your VS Code settings.json:

```json
{
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "ruff"
}
```

### PyCharm

1. Install the Ruff plugin
2. Configure Ruff as the external tool in PyCharm settings

## Pre-commit Hook (Optional)

To automatically run linting before commits, add this to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
```

## Continuous Integration

For CI/CD pipelines, add this to your workflow:

```bash
# Install dependencies
pip install ruff

# Check linting
ruff check .

# Check formatting
ruff format --check .
```

## Troubleshooting

### Ignoring Specific Lines

Use `# noqa` comments to ignore specific rules on individual lines:

```python
import sys  # noqa: F401 (intentionally unused for debugging)
long_variable_name = "this is a very long string that exceeds the line limit"  # noqa: E501
```

### Ignoring Entire Files

Add files to the `exclude` list in `pyproject.toml`:

```toml
[tool.ruff]
exclude = ["resources_from_sir", "legacy_code.py"]
```

## Additional Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Ruff Rules Reference](https://docs.astral.sh/ruff/rules/)
- [PEP 8 Style Guide](https://pep8.org/)
