#!/usr/bin/env python3
"""
Installation script for Local Multi-Agent Collaboration System
Handles system setup, Ollama configuration, and model downloads.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def check_ollama():
    """Check if Ollama is installed and running"""
    print("🔍 Checking Ollama installation...")
    
    # Check if ollama command exists
    try:
        result = subprocess.run("ollama version", shell=True, check=True, capture_output=True, text=True)
        print(f"✅ Ollama is installed: {result.stdout.strip()}")
    except subprocess.CalledProcessError:
        print("❌ Ollama not found. Please install from https://ollama.com")
        return False
    
    # Check if Ollama service is running
    try:
        import aiohttp
        import asyncio
        
        async def test_connection():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://localhost:11434/api/tags") as response:
                        return response.status == 200
            except:
                return False
        
        if asyncio.run(test_connection()):
            print("✅ Ollama service is running")
            return True
        else:
            print("⚠️  Ollama service not running. Start with: ollama serve")
            return False
    except ImportError:
        print("⚠️  Cannot test Ollama service (aiohttp not installed yet)")
        return True

def install_requirements():
    """Install Python requirements"""
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    return run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing Python dependencies"
    )

def install_package():
    """Install the package in development mode"""
    return run_command(
        f"{sys.executable} -m pip install -e .",
        "Installing package in development mode"
    )

def download_models():
    """Download required Ollama models"""
    models = [
        "llama3.1:8b",
        "qwen2.5:7b", 
        "deepseek-coder",
        "llama3.2:3b"
    ]
    
    print("📥 Downloading required Ollama models...")
    print("This may take several minutes depending on your internet connection.")
    
    for model in models:
        success = run_command(f"ollama pull {model}", f"Downloading {model}")
        if not success:
            print(f"⚠️  Failed to download {model}. You can download it later with: ollama pull {model}")
    
    return True

def create_directories():
    """Create necessary directories"""
    directories = ["sessions", "logs"]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    return True

def test_system():
    """Test the system setup"""
    print("🧪 Testing system setup...")
    
    try:
        # Import to test all dependencies
        sys.path.append('.')
        from main import test_connectivity
        import asyncio
        
        success = asyncio.run(test_connectivity())
        
        if success:
            print("🎉 System setup completed successfully!")
            print("\nNext steps:")
            print("1. Ensure Ollama is running: ollama serve")
            print("2. Test the system: python main.py --test")
            print("3. Try an example: python main.py --examples")
            return True
        else:
            print("❌ System test failed. Check the logs above.")
            return False
            
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

def main():
    """Main installation process"""
    print("🚀 Local Multi-Agent Collaboration System Installation")
    print("=" * 55)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    # Install package and dependencies
    if not install_package():
        print("❌ Failed to install package")
        sys.exit(1)
    
    # Check Ollama
    ollama_ok = check_ollama()
    
    # Create directories
    create_directories()
    
    # Download models if Ollama is working
    if ollama_ok:
        download_models()
    else:
        print("⚠️  Skipping model download. Please install and start Ollama first.")
        print("   1. Install Ollama from https://ollama.com")
        print("   2. Start Ollama: ollama serve")
        print("   3. Run this installation again")
    
    print("\n" + "=" * 55)
    print("✅ Installation completed!")
    
    if ollama_ok:
        # Test system
        test_system()
    else:
        print("\n⚠️  Complete the Ollama setup, then run:")
        print("   python main.py --test")
        
    print("\nUsage:")
    print("  local-agent-system --help          # Show help")
    print("  local-agent-system --test          # Test connectivity")
    print("  python main.py \"your problem\"      # Start collaboration")
    print("  python tests/run_tests.py --fast   # Run tests")

if __name__ == "__main__":
    main()