# Local Multi-Agent Collaborative System

A production-ready implementation of a local multi-agent collaboration system using Ollama for LLM inference. This system implements a 4-phase collaborative workflow where AI agents with different specializations work together to solve complex problems.

## Features

### 🤖 Multi-Agent Architecture
- **5 Specialized Agents** with distinct roles and personalities:
  - `DataScientist_Alpha`: Analytical and methodical (llama3.1:8b, temp=0.3)
  - `ProductManager_Beta`: User-focused and strategic (qwen2.5:7b, temp=0.5)
  - `TechArchitect_Gamma`: System-oriented and technical (deepseek-coder, temp=0.4)
  - `CreativeInnovator_Delta`: Bold and unconventional (llama3.2:3b, temp=0.8)
  - `RiskAnalyst_Epsilon`: Cautious and thorough (llama3.2:3b, temp=0.2)

### 🔄 4-Phase Collaboration Workflow
1. **Individual Analysis**: All agents analyze the problem concurrently
2. **Cross-Agent Critique**: Round-robin critique of each other's work
3. **Solution Synthesis**: Agents synthesize insights from all perspectives
4. **Consensus Building**: Algorithmic consensus with confidence weighting

### 🛠 Production Features
- **Async Processing**: Full asyncio implementation for concurrent operations
- **Robust Error Handling**: Multiple fallback strategies for parsing and recovery
- **JSON Response Parsing**: Handles malformed responses with fallback strategies
- **Performance Metrics**: Comprehensive timing and success rate tracking
- **Session Persistence**: Automatic saving of collaboration history
- **Configuration Management**: YAML-based configuration system
- **CLI Interface**: Command-line interface with multiple operation modes

## Prerequisites

### 1. Install Ollama
Download and install Ollama from [https://ollama.com](https://ollama.com)

### 2. Download Required Models
```bash
# Download the required models
ollama pull llama3.1:8b
ollama pull qwen2.5:7b
ollama pull deepseek-coder
ollama pull llama3.2:3b

# Start Ollama service
ollama serve
```

### 3. Verify Ollama Installation
```bash
# Test that Ollama is running
curl http://localhost:11434/api/tags
```

## Installation

### 1. Clone/Download the Project
```bash
cd local_agent_system
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Test System Connectivity
```bash
python main.py --test
```

## Usage

### Command Line Interface

#### Test Connectivity
```bash
python main.py --test
```
Tests Ollama connection and verifies all agents can communicate with their assigned models.

#### Solve a Specific Problem
```bash
python main.py --problem "How can we improve customer retention for a SaaS product?"
```

#### Interactive Mode
```bash
python main.py --interactive
```
Allows you to enter multiple problems in a conversational interface.

#### Run Example Problems
```bash
python main.py --examples
```
Demonstrates the system with pre-defined example problems.

#### Verbose Output
```bash
python main.py --problem "Your problem" --verbose
```
Enables detailed logging for debugging and analysis.

### Example Usage

```bash
# Quick test
python main.py --test

# Solve a business problem
python main.py --problem "What are the key considerations for implementing AI in healthcare?"

# Interactive session
python main.py --interactive

# Run examples with detailed output
python main.py --examples --verbose
```

## Configuration

### Agent Configuration (`config/agent_config.yaml`)
Customize agent properties:
- Model assignments
- Temperature settings
- System prompts
- Personality descriptions

### System Configuration
Modify system settings in the YAML file:
```yaml
system:
  ollama_base_url: "http://localhost:11434"
  ollama_timeout: 120
  max_retries: 3
  retry_delay: 1.0
  log_level: "INFO"
  session_save_dir: "./sessions"
  enable_metrics: true
```

## Project Structure

```
local_agent_system/
├── agents/
│   ├── base_agent.py          # Abstract base agent class
│   └── local_agent.py         # Ollama agent implementation
├── collaboration/
│   └── system.py              # Main collaboration orchestrator
├── config/
│   ├── agent_config.yaml      # Agent configurations
│   └── settings.py            # Configuration management
├── utils/
│   ├── ollama_client.py       # Async Ollama client
│   └── response_parser.py     # Response parsing with fallbacks
├── sessions/                  # Session history (auto-created)
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Output Format

Each collaboration session produces:

### Console Output
- Real-time progress updates
- Phase completion summaries
- Final consensus with confidence scores
- Performance metrics

### Session Files
Detailed JSON files saved to `sessions/` containing:
- Complete agent responses for all phases
- Performance metrics and timing
- Agent status and configuration
- Consensus building details

### Example Output
```
🎯 FINAL CONSENSUS (Confidence: 0.85):
Based on multi-agent analysis, the recommended approach for improving 
SaaS customer retention focuses on three key areas:

1. Data-driven personalization using customer behavior analytics
2. Proactive customer success management with predictive churn modeling  
3. Product development aligned with user feedback loops

💡 Key Insights:
• Implement cohort analysis to identify at-risk customer segments
• Create automated onboarding workflows to reduce time-to-value
• Establish customer health scoring based on usage patterns

➡️ Next Action: Develop a comprehensive customer success framework

👥 Contributing Agents: DataScientist_Alpha, ProductManager_Beta, TechArchitect_Gamma, CreativeInnovator_Delta, RiskAnalyst_Epsilon
```

## Performance Optimization

### Model Selection
- Agents use different models optimized for their roles
- Temperature settings tuned for each agent's personality
- Concurrent processing for maximum throughput

### Error Handling
- Automatic retry logic with exponential backoff
- Multiple JSON parsing fallback strategies
- Graceful degradation for failed agents

### Resource Management
- Async context managers for proper cleanup
- Session pooling for Ollama connections
- Memory-efficient streaming responses

## Troubleshooting

### Common Issues

#### "Failed to connect to Ollama"
- Ensure Ollama is running: `ollama serve`
- Check if the service is accessible: `curl http://localhost:11434/api/tags`
- Verify firewall settings

#### "Model not found" errors
- Download missing models: `ollama pull <model-name>`
- Check available models: `ollama list`
- Update `agent_config.yaml` with available models

#### JSON parsing errors
- The system includes multiple fallback parsers
- Check agent system prompts in configuration
- Enable verbose logging: `--verbose`

#### Performance issues
- Reduce concurrent operations in configuration
- Use smaller models for faster responses
- Increase timeout values for slower systems

### Debug Mode
```bash
python main.py --problem "test problem" --verbose
```
Enables detailed logging for troubleshooting.

## Extending the System

### Adding New Agents
1. Add agent configuration to `agent_config.yaml`
2. Agents are automatically loaded from configuration
3. Customize system prompts and parameters

### Custom Collaboration Phases
Modify the `LocalAgent2AgentSystem` class to implement custom workflows:
- Add new phases to the collaboration pipeline
- Implement custom consensus algorithms
- Create specialized agent interactions

### Integration with Other LLMs
The system is designed to be model-agnostic:
- Implement new client classes in `utils/`
- Update agent configuration for different backends
- Maintain the same response format schema

## License

This project is provided as-is for educational and research purposes.

## Contributing

Feel free to submit issues, feature requests, and improvements to enhance the multi-agent collaboration capabilities.
