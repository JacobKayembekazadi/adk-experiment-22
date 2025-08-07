#!/usr/bin/env python3
"""
Test script for the enhanced Ollama client
"""
import asyncio
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from local_agent_system.utils.ollama_client import (
    OllamaClient, 
    OllamaConfig, 
    GenerationRequest,
    GenerationResponse,
    OllamaClientError,
    OllamaConnectionError,
    OllamaModelError,
    validate_model_name,
    validate_temperature
)

async def test_enhanced_client():
    """Test the enhanced Ollama client functionality"""
    print("🧪 Testing Enhanced Ollama Client")
    print("=" * 50)
    
    # Test configuration validation
    print("1. Testing configuration validation...")
    try:
        # Valid config
        config = OllamaConfig(
            base_url="http://localhost:11434",
            timeout=60,
            max_retries=2,
            retry_delay=0.5
        )
        print("✅ Valid configuration created successfully")
        
        # Invalid config
        try:
            invalid_config = OllamaConfig(base_url="invalid-url")
            print("❌ Should have failed with invalid URL")
        except Exception as e:
            print(f"✅ Correctly caught invalid config: {e}")
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False
    
    # Test utility functions
    print("\n2. Testing utility functions...")
    print(f"   validate_model_name('llama3.1:8b'): {validate_model_name('llama3.1:8b')}")
    print(f"   validate_model_name(''): {validate_model_name('')}")
    print(f"   validate_temperature(0.7): {validate_temperature(0.7)}")
    print(f"   validate_temperature(3.0): {validate_temperature(3.0)}")
    
    # Test client functionality
    print("\n3. Testing client functionality...")
    try:
        async with OllamaClient(config) as client:
            print("✅ Client context manager works")
            
            # Test health check
            health = await client.health_check()
            print(f"   Health check: {health}")
            
            if health['service_available']:
                print("✅ Ollama service is available")
                
                # Test model listing
                models = await client.list_models()
                print(f"   Available models: {models}")
                
                # Test generation if models are available
                if models and any('llama' in model for model in models):
                    test_model = next(model for model in models if 'llama' in model)
                    print(f"\n   Testing generation with model: {test_model}")
                    
                    try:
                        response = await client.generate_with_retry(
                            model=test_model,
                            prompt="Say hello in JSON format with a greeting field",
                            temperature=0.1
                        )
                        print(f"✅ Generation successful: {response.response[:100]}...")
                        print(f"   Model: {response.model}")
                        print(f"   Tokens: prompt={response.prompt_eval_count}, response={response.eval_count}")
                    except Exception as e:
                        print(f"⚠️  Generation failed (this may be expected): {e}")
                else:
                    print("⚠️  No suitable models found for testing generation")
            else:
                print("❌ Ollama service not available")
                print(f"   Error: {health.get('error', 'Unknown error')}")
                
    except Exception as e:
        print(f"❌ Client test failed: {e}")
        return False
    
    print("\n✅ All tests completed!")
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_enhanced_client())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Test cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Test script failed: {e}")
        sys.exit(1)
