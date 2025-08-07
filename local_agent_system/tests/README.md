# Testing Suite

Comprehensive testing suite for the local multi-agent collaboration system.

## Overview

This testing suite includes:
- **Unit Tests**: Fast tests for individual components
- **Integration Tests**: End-to-end tests with real Ollama integration  
- **Mock Tests**: Tests using mocked dependencies (no Ollama required)
- **Performance Benchmarks**: Performance and scalability tests

## Quick Start

### Prerequisites
```bash
pip install -r test_requirements.txt
```

### Run Tests
```bash
# Run all fast tests (unit + mock)
python tests/run_tests.py --fast

# Run specific test types
python tests/run_tests.py --unit        # Unit tests only
python tests/run_tests.py --mock        # Mock tests only
python tests/run_tests.py --integration # Integration tests (requires Ollama)
python tests/run_tests.py --benchmark   # Performance benchmarks

# Run with coverage
python tests/run_tests.py --fast --coverage
```

## Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_response_parser.py      # Response parsing tests
│   └── test_config_system.py        # Configuration system tests
├── mock/                    # Mock tests (no external dependencies)
│   ├── test_mock_agents.py          # Agent functionality with mocks
│   └── test_mock_collaboration.py   # Collaboration flow with mocks
├── integration/             # Integration tests (require Ollama)
│   └── test_collaboration_flow.py   # End-to-end collaboration tests
├── benchmarks/              # Performance benchmarks
│   └── test_performance.py          # Performance and scalability tests
├── conftest.py             # Shared fixtures and configuration
├── pytest.ini             # Pytest configuration
├── run_tests.py           # Test runner script
└── test_requirements.txt  # Test dependencies
```

## Test Categories

### Unit Tests (`-m unit`)
- Test individual components in isolation
- No external dependencies (no Ollama required)
- Fast execution (< 1s per test)
- Examples: Response parsing, configuration validation, utility functions

### Mock Tests (`-m mock`)
- Test system components with mocked dependencies
- No external dependencies (no Ollama required)
- Moderate execution time
- Examples: Agent behavior, collaboration flow, error handling

### Integration Tests (`-m integration`)
- End-to-end tests with real Ollama integration
- **Requires Ollama to be running**
- Slower execution (several seconds per test)
- Examples: Full collaboration workflows, configuration presets, real model interaction

### Performance Benchmarks (`-m benchmark`)
- Performance and scalability testing
- Memory usage analysis
- Concurrent request handling
- Response time measurements

## Running Tests

### Using the Test Runner

The `run_tests.py` script provides convenient test execution:

```bash
# Basic usage
python tests/run_tests.py --unit                    # Unit tests only
python tests/run_tests.py --integration             # Integration tests
python tests/run_tests.py --fast                    # Unit + Mock tests
python tests/run_tests.py --all                     # All tests

# With options
python tests/run_tests.py --fast --coverage         # With coverage report
python tests/run_tests.py --unit --parallel         # Parallel execution
python tests/run_tests.py --integration --verbose   # Verbose output

# Environment checks
python tests/run_tests.py --check-ollama           # Check Ollama availability
python tests/run_tests.py --install-deps           # Install test dependencies
```

### Using Pytest Directly

```bash
cd local_agent_system

# Run specific test types
pytest tests/ -m "unit"                    # Unit tests
pytest tests/ -m "mock"                    # Mock tests  
pytest tests/ -m "integration"             # Integration tests
pytest tests/ -m "benchmark"               # Benchmarks

# Run specific test files
pytest tests/unit/test_response_parser.py  # Specific file
pytest tests/mock/ -v                      # Specific directory

# With coverage
pytest tests/ -m "unit or mock" --cov=. --cov-report=html

# Parallel execution
pytest tests/ -m "unit" -n auto
```

## Test Configuration

### Pytest Configuration (`pytest.ini`)

Key settings:
- Coverage reporting with 80% minimum
- Test timeout of 300 seconds
- Strict marker enforcement
- HTML and XML coverage reports

### Environment Variables

Tests support environment variable overrides:
```bash
export AGENT_SYSTEM_OLLAMA_URL="http://localhost:11434"
export AGENT_SYSTEM_LOG_LEVEL="DEBUG"
export AGENT_SYSTEM_MAX_RETRIES="2"
```

### Fixtures and Configuration

Common fixtures in `conftest.py`:
- `temp_config_dir`: Temporary configuration directory
- `sample_agent_config`: Sample agent configuration
- `mock_ollama_client`: Mocked Ollama client
- `benchmark_config`: Benchmark test settings

## Integration Test Requirements

### Ollama Setup

Integration tests require Ollama to be running:

1. Install Ollama: https://ollama.ai/
2. Start Ollama: `ollama serve`
3. Pull test models:
   ```bash
   ollama pull llama3.2:3b
   ```
4. Verify: `curl http://localhost:11434/api/tags`

### Test Models

Integration tests use smaller models for faster execution:
- `llama3.2:3b` - Primary test model
- Tests automatically detect available models

## Performance Benchmarks

### What's Measured

- Response parsing performance
- Configuration loading speed
- Collaboration workflow timing
- Memory usage patterns
- Concurrent request handling
- Scalability with agent count

### Running Benchmarks

```bash
# Basic benchmarks
python tests/run_tests.py --benchmark

# With specific configuration
pytest tests/benchmarks/ -m benchmark -v --tb=short

# Memory profiling
python -m memory_profiler tests/benchmarks/test_performance.py
```

### Benchmark Thresholds

Default performance expectations:
- Response parsing: < 2ms average
- Configuration loading: < 1s for 50 agents  
- Memory usage: < 500MB for standard tests
- Response time: < 2s for most operations

## Continuous Integration

### GitHub Actions

The `.github/workflows/tests.yml` workflow runs:

1. **Unit Tests** - All Python versions (3.8-3.11)
2. **Mock Tests** - With coverage reporting
3. **Integration Tests** - With Ollama setup
4. **Benchmark Tests** - Performance validation
5. **Security Scan** - Bandit and Safety checks
6. **Code Quality** - Black, isort, flake8, mypy

### Coverage Requirements

- Minimum 70% overall coverage
- Reports generated in HTML and XML formats
- Uploaded to Codecov for tracking

## Development Workflow

### Before Committing
```bash
# Run fast tests
python tests/run_tests.py --fast --coverage

# Check code quality
black .
isort .
flake8 . --max-line-length=100
```

### Before Releases
```bash
# Full test suite
python tests/run_tests.py --all --coverage

# Performance validation  
python tests/run_tests.py --benchmark
```

## Troubleshooting

### Common Issues

**"Ollama not available"**
- Start Ollama: `ollama serve`
- Check connectivity: `curl http://localhost:11434/api/tags`
- Use mock tests instead: `--mock`

**"Model not found"**
- Pull required models: `ollama pull llama3.2:3b`
- Check available models: `ollama list`

**Slow integration tests**
- Integration tests are slower by design
- Use `--fast` for development
- Consider smaller test model

**Memory issues in benchmarks**
- Reduce benchmark iterations
- Check for memory leaks with `--benchmark -v`

### Test Data Cleanup

Tests create temporary files that are automatically cleaned up:
- Temporary configuration directories
- Mock session files
- Coverage reports

### Debug Mode

For detailed test debugging:
```bash
pytest tests/ -vv --tb=long --no-cov
```

## Contributing

### Adding New Tests

1. **Unit tests**: Add to `tests/unit/`
2. **Mock tests**: Add to `tests/mock/` 
3. **Integration tests**: Add to `tests/integration/`
4. **Benchmarks**: Add to `tests/benchmarks/`

### Test Conventions

- Use descriptive test names: `test_response_parsing_handles_malformed_json`
- Group related tests in classes: `TestResponseParser`
- Use fixtures for common setup
- Add appropriate markers: `@pytest.mark.unit`
- Include docstrings for complex tests

### Performance Test Guidelines

- Use `PerformanceMonitor` for consistent timing
- Set reasonable thresholds for assertions
- Test with different data sizes
- Monitor memory usage
- Use mocks for external dependencies in benchmarks