"""
Startup script for the Local Multi-Agent Collaboration Streamlit App.

This script provides easy startup with system checks and configuration.
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'streamlit',
        'aiohttp',
        'plotly', 
        'pandas',
        'pyyaml'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        
        install = input("\n🤔 Install missing packages now? (y/N): ")
        if install.lower() in ['y', 'yes']:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
                print("✅ Dependencies installed successfully!")
                return True
            except subprocess.CalledProcessError:
                print("❌ Failed to install dependencies")
                return False
        else:
            print("💡 Install with: pip install -r requirements.txt")
            return False
    
    print("✅ All required packages are installed")
    return True

def check_ollama():
    """Check if Ollama is running."""
    try:
        import urllib.request
        urllib.request.urlopen('http://localhost:11434/api/tags', timeout=5)
        print("✅ Ollama server is running")
        return True
    except Exception:
        print("⚠️  Ollama server is not responding")
        print("💡 Start Ollama with: ollama serve")
        
        continue_anyway = input("🤔 Continue without Ollama? (y/N): ")
        return continue_anyway.lower() in ['y', 'yes']

def start_streamlit(port=8501, host="localhost", debug=False):
    """Start the Streamlit application."""
    
    # Change to the directory containing this script
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Build the command
    cmd = [
        sys.executable, 
        '-m', 
        'streamlit', 
        'run', 
        'streamlit_app.py',
        '--server.port', str(port),
        '--server.address', host
    ]
    
    if debug:
        cmd.extend(['--logger.level', 'debug'])
    
    print(f"\n🚀 Starting Local Agent Collaboration System...")
    print(f"   URL: http://{host}:{port}")
    print(f"   Directory: {script_dir}")
    print("   Press Ctrl+C to stop the application")
    print("=" * 60)
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\n👋 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to start application: {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Local Multi-Agent Collaboration System - Streamlit Interface"
    )
    parser.add_argument(
        '--port', '-p', 
        type=int, 
        default=8501, 
        help='Port to run Streamlit on (default: 8501)'
    )
    parser.add_argument(
        '--host', 
        default='localhost', 
        help='Host to bind to (default: localhost)'
    )
    parser.add_argument(
        '--debug', '-d', 
        action='store_true', 
        help='Enable debug mode'
    )
    parser.add_argument(
        '--skip-checks', '-s', 
        action='store_true', 
        help='Skip system checks'
    )
    
    args = parser.parse_args()
    
    print("🤖 Local Multi-Agent Collaborative Intelligence")
    print("=" * 60)
    
    if not args.skip_checks:
        print("\n🔍 Running system checks...")
        
        if not check_python_version():
            sys.exit(1)
        
        if not check_dependencies():
            sys.exit(1)
        
        if not check_ollama():
            print("⚠️  Continuing without Ollama connection")
    
    start_streamlit(port=args.port, host=args.host, debug=args.debug)

if __name__ == "__main__":
    main()
