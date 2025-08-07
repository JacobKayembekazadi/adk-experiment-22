# Installation & Setup Guide

Complete installation guide for the Local Multi-Agent Collaborative System.

## Quick Start

```bash
# 1. Install the system
python install.py

# 2. Start Ollama (if not already running)
ollama serve

# 3. Test the system
python main.py --test

# 4. Run your first collaboration
python main.py "How can I optimize my web application's performance?"
```

## Prerequisites

### Required
- **Python 3.8+** - The system requires Python 3.8 or newer
- **Ollama** - Download from [ollama.com](https://ollama.com)

### Recommended
- **8GB+ RAM** - For running multiple LLM models
- **Good internet connection** - For downloading models (several GB)

## Installation Methods

### Method 1: Automated Installation (Recommended)

```bash
# Run the automated installer
python install.py
```

This will:
- ✅ Check Python version compatibility
- ✅ Install all Python dependencies  
- ✅ Install the package in development mode
- ✅ Check Ollama installation and connectivity
- ✅ Download required AI models
- ✅ Create necessary directories
- ✅ Test system functionality

### Method 2: Manual Installation

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install package in development mode
pip install -e .

# 3. Create directories
mkdir sessions logs

# 4. Install and start Ollama
# Download from https://ollama.com
ollama serve

# 5. Download AI models
ollama pull llama3.1:8b
ollama pull qwen2.5:7b
ollama pull deepseek-coder
ollama pull llama3.2:3b

# 6. Test system
python main.py --test
```

### Method 3: Package Installation

```bash
# Install as a package (for production use)
pip install .

# Or install from source
pip install git+https://github.com/yourusername/local-agent-system.git
```

## Dependencies

### Core Dependencies (automatically installed)
- **aiohttp** - Async HTTP client for Ollama API
- **asyncio-throttle** - Rate limiting for API requests  
- **PyYAML** - Configuration file parsing
- **psutil** - System resource monitoring

### Optional Dependencies
```bash
# Enhanced output and performance
pip install ".[enhanced]"

# Development tools
pip install ".[dev]"

# Testing framework  
pip install ".[test]"

# Performance profiling
pip install ".[performance]"
```

## Ollama Configuration

### Installation
1. Download Ollama from [ollama.com](https://ollama.com)
2. Install following platform-specific instructions
3. Start Ollama service: `ollama serve`

### Required Models
The system needs these AI models (downloaded automatically):

| Model | Size | Purpose | Command |
|-------|------|---------|---------|
| llama3.1:8b | ~4.7GB | General analysis | `ollama pull llama3.1:8b` |
| qwen2.5:7b | ~4.4GB | Technical expertise | `ollama pull qwen2.5:7b` |
| deepseek-coder | ~6.4GB | Code analysis | `ollama pull deepseek-coder` |
| llama3.2:3b | ~2.0GB | Fast responses | `ollama pull llama3.2:3b` |

### Verification
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# List available models
ollama list

# Test model interaction
ollama run llama3.2:3b "Hello, test message"
```

## Configuration

### Preset Configurations
The system includes 3 preset configurations:

```bash
# Light configuration (2-3 agents, smaller models)
python main.py --preset light "your problem"

# Balanced configuration (5 agents, mixed models) - DEFAULT
python main.py --preset balanced "your problem"  

# Premium configuration (6 agents, larger models)
python main.py --preset premium "your problem"
```

### Environment Variables
Override default settings with environment variables:

```bash
export AGENT_SYSTEM_OLLAMA_URL="http://localhost:11434"
export AGENT_SYSTEM_LOG_LEVEL="INFO"
export AGENT_SYSTEM_MAX_RETRIES="3"
export AGENT_SYSTEM_TIMEOUT="60"
```

### Custom Configuration
Edit configuration files in `config/presets/` or create your own:

```yaml
# config/custom.yaml
agents:
  MyAgent_Alpha:
    enabled: true
    model_name: "llama3.1:8b"
    role: "Technical Analyst"
    personality: "detail-oriented and systematic"
    temperature: 0.3
```

## Testing

### Run Tests
```bash
# Fast tests (no Ollama required)
python tests/run_tests.py --fast

# Full test suite (requires Ollama)
python tests/run_tests.py --all

# Integration tests only
python tests/run_tests.py --integration

# Performance benchmarks
python tests/run_tests.py --benchmark
```

### System Verification
```bash
# Test connectivity and configuration
python main.py --test

# Check system status
python main.py --status

# Verify all components
python -c "from main import test_connectivity; import asyncio; print(asyncio.run(test_connectivity()))"
```

## Usage Examples

### Basic Usage
```bash
# Start a collaboration session
python main.py "How should I architect a scalable microservices system?"

# Use specific preset
python main.py --preset light "Quick analysis needed"

# Save session results
python main.py --save "detailed-analysis.json" "Complex problem here"
```

### Advanced Usage
```bash
# Custom configuration
python main.py --config config/custom.yaml "Your problem"

# Debug mode with verbose logging
python main.py --debug "Problem to debug"

# Specify output format
python main.py --format json "Problem here" > results.json
```

### Command-Line Interface
After installation, these commands are available globally:

```bash
# Primary interface
local-agent-system "Your problem statement"

# Alternative command
agent-system --help

# Test runner
run-agent-tests --fast
```

## Troubleshooting

### Common Issues

**"Ollama not found"**
```bash
# Install Ollama from https://ollama.com
# Start the service
ollama serve
```

**"Model not available"**  
```bash
# Download missing models
ollama pull llama3.1:8b
ollama pull llama3.2:3b
```

**"Permission denied"**
```bash
# Install with user permissions
pip install --user -e .
```

**"Import errors"**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### System Requirements Check
```bash
# Check Python version
python --version

# Check available memory
python -c "import psutil; print(f'RAM: {psutil.virtual_memory().total/1024**3:.1f}GB')"

# Check disk space  
python -c "import shutil; print(f'Free space: {shutil.disk_usage(\".\").free/1024**3:.1f}GB')"
```

### Debug Mode
```bash
# Enable debug logging
export AGENT_SYSTEM_LOG_LEVEL="DEBUG"
python main.py --debug "your problem"

# Check system logs
tail -f sessions/collaboration.log
```

### Performance Optimization
```bash
# Monitor system resources during execution
python -m psutil.main

# Profile memory usage
python -m memory_profiler main.py "test problem"

# Run performance benchmarks
python tests/run_tests.py --benchmark
```

## Development Setup

### For Contributors
```bash
# Clone repository
git clone https://github.com/yourusername/local-agent-system.git
cd local-agent-system

# Install in development mode with all extras
pip install -e ".[dev,test,performance,enhanced]"

# Install pre-commit hooks
pre-commit install

# Run development tests
python tests/run_tests.py --fast --coverage
```

### Code Quality Tools
```bash
# Format code
black .
isort .

# Check code quality  
flake8 . --max-line-length=100
mypy .

# Security scan
bandit -r .
safety check
```

## System Architecture

The system implements a 4-phase collaboration workflow:

1. **Phase 1: Individual Analysis** - Each agent analyzes the problem independently
2. **Phase 2: Cross-Agent Critique** - Agents critique each other's analyses  
3. **Phase 3: Solution Synthesis** - Agents synthesize insights into solutions
4. **Phase 4: Consensus Building** - Algorithmic consensus with confidence weighting

### Agent Roles
- **Researcher_Alpha**: Research and analysis specialist
- **Strategist_Beta**: Strategic planning and high-level thinking
- **Analyst_Gamma**: Data analysis and technical evaluation  
- **Designer_Delta**: Creative and user experience focus
- **Critic_Epsilon**: Critical evaluation and risk assessment
- **QualityAssurance_Zeta**: Quality control and validation (premium only)

## Support

### Getting Help
- **Documentation**: Check the `README.md` and configuration files
- **Tests**: Run `python tests/run_tests.py --help` for testing options
- **Logs**: Check `sessions/collaboration.log` for detailed logs
- **Status**: Use `python main.py --status` to check system health

### Configuration Reference
- **Agent Configuration**: `config/presets/*.yaml`
- **System Settings**: `config/settings.py`  
- **Environment Variables**: All settings support `AGENT_SYSTEM_*` env vars
- **Test Configuration**: `tests/conftest.py`

### Performance Expectations
- **Light preset**: 30-60 seconds for typical problems
- **Balanced preset**: 60-120 seconds for typical problems  
- **Premium preset**: 90-180 seconds for typical problems
- **Memory usage**: 1-4GB depending on models and concurrency
- **Disk space**: 500MB-2GB for models and session data