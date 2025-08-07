"""
Simple test for Streamlit imports
"""
import streamlit as st

st.title("🤖 Import Test")

# Test imports one by one
st.write("Testing imports...")

try:
    from collaboration.system import LocalAgent2AgentSystem
    st.success("✅ LocalAgent2AgentSystem imported successfully")
except ImportError as e:
    st.error(f"❌ Failed to import LocalAgent2AgentSystem: {e}")

try:
    from config.settings import load_config
    st.success("✅ load_config imported successfully")
except ImportError as e:
    st.error(f"❌ Failed to import load_config: {e}")

try:
    from utils.ollama_client import OllamaClient, OllamaConfig
    st.success("✅ OllamaClient and OllamaConfig imported successfully")
except ImportError as e:
    st.error(f"❌ Failed to import OllamaClient: {e}")

try:
    from agents.local_agent import LocalAgent
    st.success("✅ LocalAgent imported successfully")
except ImportError as e:
    st.error(f"❌ Failed to import LocalAgent: {e}")

st.write("All import tests completed!")
