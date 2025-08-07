"""
Quick demonstration script for the Local Multi-Agent System
"""
import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

async def quick_demo():
    """Run a quick demonstration of the system"""
    
    print("🎭 Local Multi-Agent Collaboration System Demo")
    print("=" * 50)
    
    try:
        from main import run_collaboration
        
        # Demo problem
        problem = "How can a small startup effectively compete with larger established companies?"
        
        print(f"📝 Demo Problem:")
        print(f"   {problem}")
        print()
        
        # Run collaboration
        result = await run_collaboration(problem, save_result=True, verbose=False)
        
        if result:
            print("\n🎯 Demo completed successfully!")
            print("Check the 'sessions' folder for detailed results.")
        else:
            print("\n❌ Demo failed. Please check your Ollama setup.")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure all dependencies are installed:")
        print("  pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Demo failed: {e}")

if __name__ == "__main__":
    asyncio.run(quick_demo())
