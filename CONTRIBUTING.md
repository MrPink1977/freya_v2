# Contributing to Freya v2.0

Thank you for your interest in contributing to Freya! This document provides guidelines and standards for contributing to the project.

## Code Standards

### Python Style Guide

We follow **PEP 8** with some additional requirements:

- **Line length**: 100 characters maximum
- **Python version**: 3.11+
- **Type hints**: Required for all functions and methods
- **Docstrings**: Required for all modules, classes, and public methods (Google style)

### Code Quality Tools

We use the following tools to maintain code quality:

```bash
# Format code
black src/ --line-length 100

# Lint code
ruff check src/

# Type checking
mypy src/
```

## Documentation Standards

### Module Docstrings

Every Python module must have a docstring at the top:

```python
"""
Module Name - Brief description

Detailed description of what this module does.

Author: Your Name
Version: 0.1.0
Date: 2025-12-03
"""
```

### Class Docstrings

All classes must have comprehensive docstrings:

```python
class MyService(BaseService):
    """
    Brief one-line description.
    
    Longer description explaining the purpose, behavior, and usage
    of this class.
    
    Attributes:
        attr1: Description of attribute1
        attr2: Description of attribute2
        
    Example:
        >>> service = MyService(message_bus)
        >>> await service.initialize()
        >>> await service.start()
    """
```

### Function/Method Docstrings

All public functions and methods must have docstrings:

```python
async def process_data(self, data: Dict[str, Any]) -> str:
    """
    Brief description of what this function does.
    
    Longer description if needed.
    
    Args:
        data: Description of the data parameter
        
    Returns:
        Description of what is returned
        
    Raises:
        ValueError: When data is invalid
        ServiceError: When processing fails
        
    Example:
        >>> result = await service.process_data({"key": "value"})
    """
```

## Error Handling Standards

### Custom Exceptions

Create custom exceptions for your module:

```python
class MyServiceError(ServiceError):
    """Exception raised for MyService specific errors."""
    pass
```

### Error Logging

Use appropriate log levels:

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for recoverable issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical errors that may cause shutdown

```python
logger.debug(f"[{self.name}] Processing {len(items)} items")
logger.info(f"[{self.name}] Service started successfully")
logger.warning(f"[{self.name}] Retrying connection (attempt {attempt})")
logger.error(f"[{self.name}] Failed to process data: {e}")
logger.critical(f"[{self.name}] Fatal error, shutting down: {e}")
```

### Error Handling Pattern

Always handle errors properly:

```python
try:
    result = await some_operation()
    logger.debug(f"[{self.name}] Operation succeeded")
    return result
    
except SpecificError as e:
    logger.error(f"[{self.name}] Specific error occurred: {e}")
    self.increment_error_count()
    raise MyServiceError(f"Operation failed: {e}") from e
    
except Exception as e:
    logger.exception(f"[{self.name}] Unexpected error: {e}")
    self.increment_error_count()
    raise MyServiceError(f"Unexpected error: {e}") from e
```

## Service Development Standards

### Creating a New Service

1. **Inherit from BaseService**:

```python
from src.core.base_service import BaseService, ServiceError

class MyService(BaseService):
    def __init__(self, message_bus: MessageBus) -> None:
        super().__init__("my_service", message_bus)
        # Your initialization
```

2. **Implement Required Methods**:

```python
async def initialize(self) -> None:
    """Initialize resources."""
    try:
        # Setup code
        self._healthy = True
        logger.success(f"[{self.name}] ✓ Initialized")
    except Exception as e:
        logger.error(f"[{self.name}] ❌ Initialization failed: {e}")
        raise ServiceError(f"Failed to initialize: {e}") from e

async def start(self) -> None:
    """Start the service."""
    self._mark_started()
    await self.message_bus.subscribe("my.channel", self._handler)
    await self.publish_status("started")
    
async def stop(self) -> None:
    """Stop the service."""
    await self.message_bus.unsubscribe("my.channel")
    self._mark_stopped()
    await self.publish_status("stopped")
```

3. **Add Health Checks**:

```python
async def health_check(self) -> bool:
    """Check service health."""
    if not await super().health_check():
        return False
    # Your custom health checks
    return self.connection_active and self.model_loaded
```

## Message Bus Standards

### Channel Naming Convention

Use dot-separated hierarchical names:

- **Service status**: `service.{service_name}.status`
- **Service metrics**: `service.{service_name}.metrics`
- **Data flow**: `{source}.{data_type}` (e.g., `stt.transcription`, `llm.response`)

### Message Format

All messages must be dictionaries with at least:

```python
{
    "timestamp": datetime.now().isoformat(),
    # ... your data
}
```

### Publishing Messages

```python
await self.message_bus.publish("my.channel", {
    "timestamp": datetime.now().isoformat(),
    "data": "value",
    "source": self.name
})
```

### Subscribing to Messages

```python
async def _handle_message(self, data: Dict[str, Any]) -> None:
    """Handle incoming message."""
    try:
        # Process message
        logger.debug(f"[{self.name}] Received: {data}")
    except Exception as e:
        logger.error(f"[{self.name}] Error handling message: {e}")
        self.increment_error_count()
```

## Testing Standards

### Unit Tests

Create tests in `tests/` directory:

```python
import pytest
from src.services.my_service import MyService

@pytest.mark.asyncio
async def test_my_service_initialization():
    """Test MyService initializes correctly."""
    service = MyService(mock_message_bus)
    await service.initialize()
    assert service.is_healthy()
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_my_service.py::test_my_service_initialization
```

## Git Commit Standards

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Example**:
```
feat: Add STT service with faster-whisper integration

- Implemented STTService class with BaseService
- Added GPU acceleration support
- Integrated with audio manager via message bus
- Added comprehensive error handling and logging

Closes #42
```

## Pull Request Process

1. **Create a feature branch**: `git checkout -b feature/my-feature`
2. **Make your changes** following the standards above
3. **Test your changes**: Run tests and ensure they pass
4. **Update documentation**: Update relevant docs
5. **Commit your changes**: Follow commit message standards
6. **Push to your fork**: `git push origin feature/my-feature`
7. **Create a Pull Request**: Describe your changes clearly

## File Update Checklist

When making changes, ensure you update all necessary files:

- [ ] Source code files
- [ ] Related test files
- [ ] Documentation (README, docs/)
- [ ] Configuration files if needed
- [ ] CHANGELOG.md (if applicable)
- [ ] Type hints and docstrings
- [ ] Error handling and logging

## Questions?

If you have questions about contributing, please:

1. Check existing documentation
2. Search closed issues
3. Open a new issue with the `question` label

Thank you for contributing to Freya v2.0!
