"""
Main application entry point with CLI interface
"""
import asyncio
import argparse
import logging
import json
import sys
import os
from pathlib import Path
from typing import Optional

# Windows console compatibility
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from collaboration.system import LocalAgent2AgentSystem

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_connectivity():
    """Test Ollama connectivity and list available models"""
    print("[*] Testing Ollama connectivity...")
    
    system = LocalAgent2AgentSystem()
    
    try:
        success = await system.initialize_system()
        if success:
            print("[+] Successfully connected to Ollama!")
            status = system.get_system_status()
            
            print(f"\n[i] System Status:")
            print(f"  - Agents initialized: {status['agent_count']}")
            print(f"  - Ollama URL: {status['config']['ollama_url']}")
            
            print(f"\n[*] Agent Status:")
            for agent_id, agent_status in status['agents'].items():
                print(f"  - {agent_id}: {agent_status['model_name']} (temp: {agent_status['temperature']})")
            
            return True
        else:
            print("[-] Failed to connect to Ollama")
            print("Please ensure Ollama is running with: ollama serve")
            return False
            
    except Exception as e:
        print(f"[-] Connection test failed: {e}")
        return False
    finally:
        await system.cleanup()

async def run_collaboration(problem: str, save_result: bool = True, verbose: bool = False, 
                           preset: str = None, config_file: str = None):
    """Run collaborative problem solving"""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print(f"[>] Starting collaborative problem solving...")
    if preset:
        print(f"[*] Using preset: {preset}")
    if config_file:
        print(f"[*] Using config file: {config_file}")
    print(f"[?] Problem: {problem}")
    
    system = LocalAgent2AgentSystem(preset=preset, config_file=config_file)
    
    try:
        # Initialize system
        print("[*] Initializing agents...")
        success = await system.initialize_system()
        if not success:
            print("[-] Failed to initialize system")
            return None
        
        enabled_agents = len([a for a in system.agents.values() if getattr(a, 'enabled', True)])
        print(f"[+] Initialized {enabled_agents} enabled agents out of {len(system.agents)} total")
        
        # Run collaboration
        print("[>] Running 4-phase collaboration...")
        result = await system.run_collaborative_problem_solving(problem)
        
        # Display results
        print("\n" + "="*80)
        print("[*] COLLABORATION RESULTS")
        print("="*80)
        
        # Phase summaries
        phases = result['results']
        metrics = result['metrics']
        
        print(f"\n[i] Performance Metrics:")
        print(f"  - Total Duration: {metrics['total_duration']}s")
        print(f"  - Success Rate: {metrics['success_rate']:.1%}")
        print(f"  - Phase Durations: {metrics['phase_durations']}")
        
        # Final consensus
        consensus = phases['phase4_consensus']
        print(f"\n[+] FINAL CONSENSUS (Confidence: {consensus['confidence_level']:.2f}):")
        print(f"{consensus['main_response']}")
        
        if consensus.get('key_insights'):
            print(f"\n[!] Key Insights:")
            for insight in consensus['key_insights']:
                print(f"  * {insight}")
        
        if consensus.get('next_action'):
            print(f"\n[>] Next Action: {consensus['next_action']}")
        
        print(f"\n[*] Contributing Agents: {', '.join(consensus.get('contributing_agents', []))}")
        
        if save_result:
            session_id = result['session_id']
            print(f"\n[*] Session saved as: session_{session_id}.json")
        
        return result
        
    except Exception as e:
        logger.error(f"Collaboration failed: {e}")
        print(f"[-] Collaboration failed: {e}")
        return None
    finally:
        await system.cleanup()

async def interactive_mode(preset: str = None, config_file: str = None):
    """Run in interactive mode for multiple problems"""
    print("🎮 Interactive Mode - Enter problems to solve")
    if preset:
        print(f"🎛️  Using preset: {preset}")
    if config_file:
        print(f"⚙️  Using config file: {config_file}")
    print("Type 'exit' to quit, 'status' for system status")
    
    system = LocalAgent2AgentSystem(preset=preset, config_file=config_file)
    
    try:
        print("⚙️  Initializing system...")
        success = await system.initialize_system()
        if not success:
            print("❌ Failed to initialize system")
            return
        
        enabled_agents = len([a for a in system.agents.values() if getattr(a, 'enabled', True)])
        print(f"✅ System ready! {enabled_agents} agents initialized. Enter your problems:")
        
        while True:
            try:
                problem = input("\n🤔 Problem: ").strip()
                
                if problem.lower() == 'exit':
                    break
                elif problem.lower() == 'status':
                    status = system.get_system_status()
                    print(f"📊 System Status: {status['agent_count']} agents ready")
                    continue
                elif not problem:
                    continue
                
                print("🔄 Solving...")
                result = await system.run_collaborative_problem_solving(problem)
                
                if result:
                    consensus = result['results']['phase4_consensus']
                    print(f"\n🎯 Solution (Confidence: {consensus['confidence_level']:.2f}):")
                    print(f"{consensus['main_response']}")
                    
                    if consensus.get('key_insights'):
                        print(f"\n💡 Key Insights:")
                        for insight in consensus['key_insights'][:3]:  # Top 3
                            print(f"  • {insight}")
                
            except KeyboardInterrupt:
                print("\n👋 Exiting...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                
    finally:
        await system.cleanup()

def load_example_problems() -> list:
    """Load example problems for demonstration"""
    return [
        "How can we improve customer retention for a SaaS product?",
        "What are the key considerations for implementing AI in healthcare?",
        "Design a strategy for reducing carbon emissions in urban transportation",
        "How should a startup approach scaling from 10 to 100 employees?",
        "What are the ethical implications of autonomous vehicle decision-making?"
    ]

async def run_examples(preset: str = None, config_file: str = None):
    """Run example problems to demonstrate the system"""
    examples = load_example_problems()
    
    print("🧪 Running example problems...")
    if preset:
        print(f"🎛️  Using preset: {preset}")
    if config_file:
        print(f"⚙️  Using config file: {config_file}")
    print("This will demonstrate the multi-agent collaboration system.")
    
    for i, problem in enumerate(examples, 1):
        print(f"\n{'='*60}")
        print(f"📝 Example {i}/{len(examples)}: {problem}")
        print('='*60)
        
        result = await run_collaboration(problem, save_result=True, verbose=False, 
                                       preset=preset, config_file=config_file)
        
        if result:
            print("✅ Example completed successfully")
        else:
            print("❌ Example failed")
        
        if i < len(examples):
            print("⏳ Continuing to next example...")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Local Multi-Agent Collaborative Problem Solving System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --test                           # Test Ollama connectivity
  python main.py --interactive                    # Interactive mode
  python main.py --examples                       # Run example problems
  python main.py --problem "Your problem here"    # Solve specific problem
  python main.py --problem "Your problem" --verbose  # Verbose output
  python main.py --preset light                   # Use light configuration
  python main.py --preset premium --problem "..."  # Use premium config
  python main.py --config custom.yaml             # Use custom config file
        """
    )
    
    parser.add_argument('--test', '-t', action='store_true',
                       help='Test Ollama connectivity and system status')
    
    parser.add_argument('--problem', '-p', type=str,
                       help='Problem to solve collaboratively')
    
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Run in interactive mode')
    
    parser.add_argument('--examples', '-e', action='store_true',
                       help='Run example problems')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    parser.add_argument('--no-save', action='store_true',
                       help='Do not save session results')
    
    parser.add_argument('--preset', type=str, choices=['light', 'balanced', 'premium'],
                       help='Configuration preset to use (default: balanced)')
    
    parser.add_argument('--config', type=str,
                       help='Custom configuration file path')
    
    parser.add_argument('--list-presets', action='store_true',
                       help='List available configuration presets')
    
    parser.add_argument('--config-info', action='store_true',
                       help='Show current configuration information')
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle configuration commands
    if args.list_presets:
        from config.config_manager import ConfigManager
        presets = ConfigManager.list_available_presets()
        print("📋 Available configuration presets:")
        for preset in presets:
            print(f"  • {preset}")
        if not presets:
            print("  No presets found")
        sys.exit(0)
    
    if args.config_info:
        from config.settings import get_config_manager
        config_manager = get_config_manager(preset=args.preset)
        summary = config_manager.get_config_summary()
        
        print("ℹ️  Configuration Information:")
        print(f"  • Preset: {summary['preset']}")
        print(f"  • Ollama URL: {summary['system_config']['ollama_url']}")
        print(f"  • Timeout: {summary['system_config']['timeout']}s")
        print(f"  • Log Level: {summary['system_config']['log_level']}")
        print(f"  • Max Concurrent: {summary['system_config']['max_concurrent']}")
        print(f"  • Total Agents: {summary['agents']['total']}")
        print(f"  • Enabled Agents: {summary['agents']['enabled']}")
        print(f"  • Models: {', '.join(summary['agents']['models'])}")
        
        if summary['validation_errors'] > 0:
            print(f"  ⚠️  Validation Errors: {summary['validation_errors']}")
        
        sys.exit(0)
    
    try:
        if args.test:
            success = asyncio.run(test_connectivity())
            sys.exit(0 if success else 1)
        
        elif args.interactive:
            asyncio.run(interactive_mode(preset=args.preset, config_file=args.config))
        
        elif args.examples:
            asyncio.run(run_examples(preset=args.preset, config_file=args.config))
        
        elif args.problem:
            result = asyncio.run(run_collaboration(
                args.problem, 
                save_result=not args.no_save,
                verbose=args.verbose,
                preset=args.preset,
                config_file=args.config
            ))
            sys.exit(0 if result else 1)
        
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
