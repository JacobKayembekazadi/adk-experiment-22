"""
Local Multi-Agent Collaborative Intelligence - Streamlit Web Application

A complete Streamlit interface for the local agent collaboration system
with real-time collaboration monitoring and responsive design.
"""

import streamlit as st
import asyncio
import time
import json
from datetime import datetime
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional
import traceback

# Import local modules
try:
    from collaboration.system import LocalAgent2AgentSystem
    from config.settings import load_config
    from utils.ollama_client import OllamaClient, OllamaConfig
    from agents.local_agent import LocalAgent
except ImportError as e:
    st.error(f"Failed to import local modules: {e}")
    st.error("Please ensure all required modules are in the correct locations:")
    st.error("- collaboration/system.py")
    st.error("- config/settings.py") 
    st.error("- utils/ollama_client.py")
    st.error("- agents/local_agent.py")
    st.stop()

# Configure page
st.set_page_config(
    page_title="Local Agent Collaboration", 
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def init_session_state():
    """Initialize Streamlit session state variables."""
    if 'collaboration_system' not in st.session_state:
        st.session_state.collaboration_system = None
    
    if 'collaboration_history' not in st.session_state:
        st.session_state.collaboration_history = []
    
    if 'current_collaboration' not in st.session_state:
        st.session_state.current_collaboration = None
    
    if 'collaboration_in_progress' not in st.session_state:
        st.session_state.collaboration_in_progress = False
    
    if 'available_models' not in st.session_state:
        st.session_state.available_models = ["llama3.2:3b", "llama3.1:8b", "qwen2.5:7b", "gemma3:1b", "deepseek-r1:latest"]
    
    if 'ollama_connected' not in st.session_state:
        st.session_state.ollama_connected = False
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "main"
    
    if 'collaboration_results' not in st.session_state:
        st.session_state.collaboration_results = None

# Async wrapper for Streamlit
def run_async(coro):
    """Run async coroutine in Streamlit context."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    except Exception as e:
        st.error(f"Async execution failed: {e}")
        return None
    finally:
        try:
            loop.close()
        except:
            pass

async def test_ollama_connection(url: str) -> Dict[str, Any]:
    """Test connection to Ollama server."""
    try:
        config = OllamaConfig(base_url=url)
        client = OllamaClient(config)
        
        async with client:
            models = await client.list_models()
            return {
                "success": True,
                "models": models,
                "message": f"Connected successfully! Found {len(models)} models."
            }
    except Exception as e:
        return {
            "success": False,
            "models": [],
            "message": f"Connection failed: {str(e)}"
        }

def render_header():
    """Render the main header."""
    st.title("🤖 Local Multi-Agent Collaborative Intelligence")
    st.markdown("*Powered by local Ollama models - 100% private*")
    st.markdown("---")

def render_sidebar():
    """Render the sidebar configuration."""
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Page Navigation
        st.subheader("📱 Navigation")
        page = st.radio("Select Page", ["Main", "History", "Settings", "About"], key="page_selector")
        if page != st.session_state.current_page:
            st.session_state.current_page = page.lower()
            st.rerun()
        
        if st.session_state.current_page == "main":
            render_main_sidebar()

def render_main_sidebar():
    """Render main page sidebar configuration."""
    # Agent Selection
    st.subheader("🤖 Active Agents")
    agents_config = {}
    
    agent_names = ["DataScientist", "ProductManager", "TechArchitect", "CreativeInnovator", "RiskAnalyst"]
    
    for agent_name in agent_names:
        with st.expander(f"🤖 {agent_name}", expanded=False):
            col1, col2 = st.columns([1, 1])
            with col1:
                enabled = st.checkbox("Enabled", value=True, key=f"{agent_name}_enabled")
            with col2:
                model = st.selectbox(
                    "Model", 
                    st.session_state.available_models, 
                    key=f"{agent_name}_model",
                    index=0
                )
            
            temperature = st.slider(
                "Temperature", 
                0.0, 2.0, 0.7, 0.1, 
                key=f"{agent_name}_temp"
            )
            
            agents_config[agent_name] = {
                "enabled": enabled, 
                "model": model,
                "temperature": temperature
            }
    
    # Store in session state
    st.session_state.agents_config = agents_config
    
    # System Settings
    st.subheader("⚙️ System Settings")
    ollama_url = st.text_input("Ollama URL", value="http://localhost:11434")
    max_concurrent = st.slider("Max Concurrent Agents", 1, 5, 3)
    
    # Store system settings
    st.session_state.system_config = {
        "ollama_url": ollama_url,
        "max_concurrent": max_concurrent
    }
    
    # Connection Status
    st.subheader("🔌 Connection Status")
    connection_status = "🟢 Connected" if st.session_state.ollama_connected else "🔴 Disconnected"
    st.write(f"Ollama: {connection_status}")

def render_main_page():
    """Render the main collaboration page."""
    render_header()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🎯 Problem Definition")
        problem = st.text_area(
            "Describe your complex problem:", 
            height=150,
            placeholder="Enter a complex problem that requires multiple perspectives...",
            key="problem_input"
        )
        
        # Collaboration options
        col1a, col1b = st.columns(2)
        with col1a:
            save_to_history = st.checkbox("💾 Save to History", value=True)
        with col1b:
            verbose_output = st.checkbox("🔍 Verbose Output", value=False)
        
        # Start collaboration button
        if st.button("🚀 Start Collaboration", type="primary", disabled=not problem):
            enabled_agents = [name for name, config in st.session_state.agents_config.items() if config["enabled"]]
            if enabled_agents:
                start_collaboration(problem, save_to_history, verbose_output)
            else:
                st.error("❌ Please enable at least one agent before starting collaboration.")
    
    with col2:
        st.header("📊 System Status")
        
        # Test connection button
        if st.button("🔍 Test Ollama Connection"):
            with st.spinner("Testing connection..."):
                result = run_async(test_ollama_connection(st.session_state.system_config["ollama_url"]))
                if result:
                    if result["success"]:
                        st.session_state.ollama_connected = True
                        st.session_state.available_models = result["models"]
                        st.success(result["message"])
                    else:
                        st.session_state.ollama_connected = False
                        st.error(result["message"])
        
        # Show enabled agents
        st.subheader("🎯 Active Agents")
        enabled_agents = [name for name, config in st.session_state.agents_config.items() if config["enabled"]]
        
        if enabled_agents:
            for agent_name in enabled_agents:
                config = st.session_state.agents_config[agent_name]
                st.write(f"🤖 **{agent_name}**")
                st.write(f"   Model: `{config['model']}`")
                st.write(f"   Temp: `{config['temperature']}`")
                st.write("")
            
            st.metric("Total Active Agents", len(enabled_agents))
        else:
            st.warning("⚠️ No agents enabled")
        
        # Show recent activity
        st.subheader("📈 Recent Activity")
        if st.session_state.collaboration_history:
            recent_count = min(3, len(st.session_state.collaboration_history))
            for i in range(recent_count):
                collab = st.session_state.collaboration_history[-(i+1)]
                st.write(f"• {collab['timestamp'][:16]}")
        else:
            st.write("No recent collaborations")

def start_collaboration(problem: str, save_to_history: bool, verbose: bool):
    """Start the collaboration process."""
    try:
        # Initialize collaboration data
        collaboration_data = {
            'problem': problem,
            'timestamp': datetime.now().isoformat(),
            'agents': [name for name, config in st.session_state.agents_config.items() if config['enabled']],
            'phases': {
                'analysis': {'status': 'pending', 'results': {}, 'progress': 0},
                'critique': {'status': 'pending', 'results': {}, 'progress': 0},
                'synthesis': {'status': 'pending', 'results': {}, 'progress': 0},
                'consensus': {'status': 'pending', 'results': {}, 'progress': 0}
            },
            'verbose': verbose,
            'save_to_history': save_to_history
        }
        
        st.session_state.current_collaboration = collaboration_data
        st.session_state.collaboration_in_progress = True
        
        # Switch to collaboration view
        st.rerun()
        
    except Exception as e:
        st.error(f"Failed to start collaboration: {e}")

def render_collaboration_interface():
    """Render the real-time collaboration interface."""
    st.title("🔄 Live Collaboration in Progress")
    st.markdown("---")
    
    collaboration = st.session_state.current_collaboration
    
    # Phase Progress Bar
    render_phase_progress()
    
    # Agent Status Cards
    render_agent_status_cards()
    
    # Live Response Stream
    render_live_responses()
    
    # Simulate collaboration progress
    simulate_collaboration_progress()
    
    # Control buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⏸️ Pause Collaboration"):
            st.session_state.collaboration_in_progress = False
    with col2:
        if st.button("🛑 Stop Collaboration"):
            stop_collaboration()
    with col3:
        if st.button("📊 View Results", disabled=not is_collaboration_complete()):
            view_results()

def render_phase_progress():
    """Render phase progress indicators."""
    st.subheader("📊 Phase Progress")
    
    phases = st.session_state.current_collaboration['phases']
    phase_names = ['Analysis', 'Critique', 'Synthesis', 'Consensus']
    
    cols = st.columns(4)
    
    for i, (phase_key, phase_name) in enumerate(zip(phases.keys(), phase_names)):
        with cols[i]:
            phase_data = phases[phase_key]
            status = phase_data['status']
            progress = phase_data.get('progress', 0)
            
            if status == 'completed':
                st.success(f"✅ {phase_name}")
                st.progress(1.0)
            elif status == 'running':
                st.warning(f"🔄 {phase_name}")
                st.progress(progress / 100)
            else:
                st.info(f"⏳ {phase_name}")
                st.progress(0.0)

def render_agent_status_cards():
    """Render individual agent status cards."""
    st.subheader("🤖 Agent Status")
    
    enabled_agents = st.session_state.current_collaboration['agents']
    phases = st.session_state.current_collaboration['phases']
    
    for agent_name in enabled_agents:
        with st.expander(f"🤖 {agent_name}", expanded=True):
            cols = st.columns(4)
            
            for i, (phase_key, phase_name) in enumerate(zip(phases.keys(), ['Analysis', 'Critique', 'Synthesis', 'Consensus'])):
                with cols[i]:
                    phase_data = phases[phase_key]
                    
                    if agent_name in phase_data['results']:
                        st.success(f"✅ {phase_name}")
                    elif phase_data['status'] == 'running':
                        st.warning(f"🔄 {phase_name}")
                    else:
                        st.info(f"⏳ {phase_name}")

def render_live_responses():
    """Render live agent responses as they complete."""
    st.subheader("💬 Live Response Stream")
    
    # Create empty container for live updates
    response_container = st.empty()
    
    phases = st.session_state.current_collaboration['phases']
    
    # Display latest responses
    latest_responses = []
    for phase_name, phase_data in phases.items():
        for agent_name, result in phase_data['results'].items():
            latest_responses.append({
                'timestamp': result.get('timestamp', ''),
                'phase': phase_name.title(),
                'agent': agent_name,
                'response': result.get('main_response', '')[:200] + "...",
                'confidence': result.get('confidence_level', 0)
            })
    
    # Sort by timestamp and show latest
    latest_responses.sort(key=lambda x: x['timestamp'], reverse=True)
    
    with response_container.container():
        for response in latest_responses[:5]:  # Show last 5 responses
            st.write(f"**{response['agent']}** - {response['phase']} (Confidence: {response['confidence']:.2%})")
            st.write(f"_{response['response']}_")
            st.write("---")

def simulate_collaboration_progress():
    """Simulate collaboration progress for demonstration."""
    if not st.session_state.collaboration_in_progress:
        return
    
    collaboration = st.session_state.current_collaboration
    phases = collaboration['phases']
    enabled_agents = collaboration['agents']
    
    # Simulate phase progression
    current_phase = None
    for phase_name, phase_data in phases.items():
        if phase_data['status'] == 'pending':
            current_phase = phase_name
            break
    
    if current_phase:
        # Start the phase
        phases[current_phase]['status'] = 'running'
        
        # Simulate agent responses
        import random
        for agent_name in enabled_agents:
            if agent_name not in phases[current_phase]['results']:
                # Generate mock response
                mock_response = generate_mock_response(agent_name, current_phase, collaboration['problem'])
                phases[current_phase]['results'][agent_name] = mock_response
                
                # Update progress
                completed_agents = len(phases[current_phase]['results'])
                total_agents = len(enabled_agents)
                phases[current_phase]['progress'] = (completed_agents / total_agents) * 100
                
                break
        
        # Check if phase is complete
        if len(phases[current_phase]['results']) == len(enabled_agents):
            phases[current_phase]['status'] = 'completed'
            phases[current_phase]['progress'] = 100
    
    # Auto-refresh every 2 seconds during collaboration
    time.sleep(2)
    st.rerun()

def generate_mock_response(agent_name: str, phase: str, problem: str) -> Dict[str, Any]:
    """Generate mock agent response for demonstration."""
    responses = {
        'analysis': f"As {agent_name}, I analyze this problem from my unique perspective. Key insights emerging...",
        'critique': f"{agent_name} provides constructive critique of the previous analysis, identifying strengths and areas for improvement.",
        'synthesis': f"{agent_name} synthesizes insights to propose concrete solutions based on analysis and critique.",
        'consensus': f"Final recommendations from {agent_name} with confidence metrics and consensus building."
    }
    
    import random
    return {
        'agent_id': agent_name,
        'phase': phase,
        'main_response': responses.get(phase, "Mock response") + f" For the problem: {problem[:50]}...",
        'confidence_level': round(random.uniform(0.6, 0.95), 2),
        'key_insights': [f"Insight 1 from {agent_name}", f"Insight 2 from {agent_name}"],
        'questions_raised': [f"Question from {agent_name} perspective"],
        'timestamp': datetime.now().isoformat()
    }

def is_collaboration_complete() -> bool:
    """Check if collaboration is complete."""
    if not st.session_state.current_collaboration:
        return False
    
    phases = st.session_state.current_collaboration['phases']
    return all(phase['status'] == 'completed' for phase in phases.values())

def stop_collaboration():
    """Stop the current collaboration."""
    st.session_state.collaboration_in_progress = False
    if st.session_state.current_collaboration and st.session_state.current_collaboration.get('save_to_history', False):
        st.session_state.collaboration_history.append(st.session_state.current_collaboration)
    st.rerun()

def view_results():
    """Switch to results view."""
    st.session_state.collaboration_in_progress = False
    st.session_state.collaboration_results = st.session_state.current_collaboration
    if st.session_state.current_collaboration.get('save_to_history', False):
        st.session_state.collaboration_history.append(st.session_state.current_collaboration)
    st.rerun()

def render_consensus_dashboard():
    """Render the consensus dashboard with final results."""
    st.title("🤝 Collaboration Results")
    st.markdown("---")
    
    collaboration = st.session_state.collaboration_results or st.session_state.current_collaboration
    
    if not collaboration:
        st.warning("No collaboration results available.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Agents", len(collaboration['agents']))
    with col2:
        st.metric("Phases Completed", sum(1 for p in collaboration['phases'].values() if p['status'] == 'completed'))
    with col3:
        avg_confidence = calculate_average_confidence(collaboration)
        st.metric("Avg Confidence", f"{avg_confidence:.1%}")
    with col4:
        st.metric("Duration", "~5 min")  # Placeholder
    
    # Results tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Summary", "🔍 Analysis", "💬 Critique", "🔧 Synthesis", "🤝 Consensus"])
    
    with tab1:
        render_results_summary(collaboration)
    
    with tab2:
        render_phase_results(collaboration, 'analysis')
    
    with tab3:
        render_phase_results(collaboration, 'critique')
    
    with tab4:
        render_phase_results(collaboration, 'synthesis')
    
    with tab5:
        render_final_consensus(collaboration)
    
    # Export options
    st.markdown("---")
    st.subheader("💾 Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.download_button(
            label="📄 Download JSON",
            data=json.dumps(collaboration, indent=2),
            file_name=f"collaboration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        ):
            st.success("JSON downloaded!")
    
    with col2:
        csv_data = generate_csv_export(collaboration)
        if st.download_button(
            label="📊 Download CSV",
            data=csv_data,
            file_name=f"collaboration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        ):
            st.success("CSV downloaded!")
    
    with col3:
        if st.button("📧 Share Results"):
            st.info("Share functionality coming soon!")
    
    # New collaboration button
    if st.button("🆕 Start New Collaboration", type="primary"):
        reset_collaboration()

def render_results_summary(collaboration: Dict[str, Any]):
    """Render results summary tab."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Problem Statement")
        st.info(collaboration['problem'])
        
        st.subheader("👥 Participating Agents")
        for agent in collaboration['agents']:
            st.write(f"• {agent}")
    
    with col2:
        # Confidence chart
        confidence_data = []
        for phase_name, phase_data in collaboration['phases'].items():
            for agent_name, result in phase_data['results'].items():
                confidence_data.append({
                    'Agent': agent_name,
                    'Phase': phase_name.title(),
                    'Confidence': result['confidence_level']
                })
        
        if confidence_data:
            df = pd.DataFrame(confidence_data)
            fig = px.bar(df, x='Agent', y='Confidence', color='Phase', 
                        title="Agent Confidence by Phase")
            st.plotly_chart(fig, use_container_width=True)

def render_phase_results(collaboration: Dict[str, Any], phase: str):
    """Render results for a specific phase."""
    phase_data = collaboration['phases'][phase]
    
    if not phase_data['results']:
        st.info(f"No {phase} results available")
        return
    
    for agent_name, result in phase_data['results'].items():
        with st.expander(f"🤖 {agent_name}", expanded=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown("**Response:**")
                st.write(result['main_response'])
                
                if result.get('key_insights'):
                    st.markdown("**Key Insights:**")
                    for insight in result['key_insights']:
                        st.write(f"• {insight}")
            
            with col2:
                # Confidence gauge
                confidence = result['confidence_level']
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = confidence * 100,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Confidence"},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "yellow"},
                            {'range': [80, 100], 'color': "green"}
                        ]
                    }
                ))
                fig.update_layout(height=200)
                st.plotly_chart(fig, use_container_width=True)

def render_final_consensus(collaboration: Dict[str, Any]):
    """Render final consensus results."""
    consensus_data = collaboration['phases']['consensus']
    
    if not consensus_data['results']:
        st.info("No consensus results available")
        return
    
    # Find best recommendation
    best_agent = max(consensus_data['results'].items(), key=lambda x: x[1]['confidence_level'])
    
    st.success(f"**🏆 Primary Recommendation from {best_agent[0]}:**")
    st.write(best_agent[1]['main_response'])
    st.write(f"**Confidence Level:** {best_agent[1]['confidence_level']:.2%}")
    
    st.markdown("---")
    st.subheader("📋 All Agent Consensus")
    
    for agent_name, result in consensus_data['results'].items():
        confidence_color = "🟢" if result['confidence_level'] > 0.8 else "🟡" if result['confidence_level'] > 0.6 else "🔴"
        with st.expander(f"{confidence_color} {agent_name} - Confidence: {result['confidence_level']:.2%}"):
            st.write(result['main_response'])

def calculate_average_confidence(collaboration: Dict[str, Any]) -> float:
    """Calculate average confidence across all phases."""
    total_confidence = 0
    total_responses = 0
    
    for phase_data in collaboration['phases'].values():
        for result in phase_data['results'].values():
            total_confidence += result.get('confidence_level', 0)
            total_responses += 1
    
    return total_confidence / total_responses if total_responses > 0 else 0

def generate_csv_export(collaboration: Dict[str, Any]) -> str:
    """Generate CSV export data."""
    csv_data = []
    
    for phase_name, phase_data in collaboration['phases'].items():
        for agent_name, result in phase_data['results'].items():
            csv_data.append({
                'Phase': phase_name,
                'Agent': agent_name,
                'Confidence': result['confidence_level'],
                'Response': result['main_response'].replace('\n', ' '),
                'Timestamp': result['timestamp']
            })
    
    df = pd.DataFrame(csv_data)
    return df.to_csv(index=False)

def reset_collaboration():
    """Reset collaboration state for new session."""
    st.session_state.current_collaboration = None
    st.session_state.collaboration_results = None
    st.session_state.collaboration_in_progress = False
    st.rerun()

def render_history_page():
    """Render collaboration history page."""
    st.title("📚 Collaboration History")
    st.markdown("---")
    
    if not st.session_state.collaboration_history:
        st.info("No collaboration history available. Start your first collaboration to see results here!")
        return
    
    # History list
    for i, collaboration in enumerate(reversed(st.session_state.collaboration_history)):
        with st.expander(f"Collaboration {len(st.session_state.collaboration_history) - i}: {collaboration['timestamp'][:19]}", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Problem:** {collaboration['problem'][:100]}...")
                st.write(f"**Agents:** {len(collaboration['agents'])}")
            
            with col2:
                completed_phases = sum(1 for p in collaboration['phases'].values() if p['status'] == 'completed')
                st.write(f"**Phases Completed:** {completed_phases}/4")
                avg_conf = calculate_average_confidence(collaboration)
                st.write(f"**Avg Confidence:** {avg_conf:.1%}")
            
            with col3:
                if st.button(f"📊 View Results", key=f"view_{i}"):
                    st.session_state.collaboration_results = collaboration
                    st.session_state.current_page = "results"
                    st.rerun()
                
                if st.button(f"🗑️ Delete", key=f"delete_{i}"):
                    st.session_state.collaboration_history.remove(collaboration)
                    st.rerun()

def render_settings_page():
    """Render settings and configuration page."""
    st.title("⚙️ Advanced Settings")
    st.markdown("---")
    
    # Model Management
    st.subheader("🤖 Model Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Available Models:**")
        for model in st.session_state.available_models:
            st.write(f"• {model}")
    
    with col2:
        st.write("**Model Performance:**")
        st.info("Performance metrics coming soon!")
    
    # System Configuration
    st.subheader("🔧 System Configuration")
    
    max_retries = st.slider("Max Retries", 1, 10, 3)
    timeout = st.slider("Timeout (seconds)", 10, 300, 120)
    log_level = st.selectbox("Log Level", ["DEBUG", "INFO", "WARNING", "ERROR"])
    
    # Export/Import Settings
    st.subheader("💾 Configuration Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Export Settings"):
            settings = {
                'agents_config': st.session_state.agents_config,
                'system_config': st.session_state.system_config,
                'available_models': st.session_state.available_models
            }
            st.download_button(
                "Download Settings",
                json.dumps(settings, indent=2),
                "agent_settings.json",
                "application/json"
            )
    
    with col2:
        uploaded_file = st.file_uploader("📤 Import Settings", type="json")
        if uploaded_file:
            try:
                settings = json.load(uploaded_file)
                st.session_state.agents_config = settings.get('agents_config', {})
                st.session_state.system_config = settings.get('system_config', {})
                st.success("Settings imported successfully!")
            except Exception as e:
                st.error(f"Failed to import settings: {e}")

def render_about_page():
    """Render about and system information page."""
    st.title("ℹ️ About Local Agent Collaboration")
    st.markdown("---")
    
    # System Information
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🤖 System Overview")
        st.write("""
        **Local Multi-Agent Collaborative Intelligence** is a privacy-first AI collaboration system 
        that runs entirely on your local machine using Ollama models.
        
        **Key Features:**
        - 🔒 100% Private - No data leaves your machine
        - 🤖 Multi-Agent Collaboration - 5 specialized AI agents
        - 🔄 Real-time Collaboration - Live progress monitoring
        - 📊 Advanced Analytics - Confidence metrics and insights
        - 💾 Session Management - Save and replay collaborations
        """)
    
    with col2:
        st.subheader("🎯 Agent Specializations")
        st.write("""
        **DataScientist** - Analytical and data-driven insights
        
        **ProductManager** - User-focused and strategic thinking
        
        **TechArchitect** - Technical feasibility and system design
        
        **CreativeInnovator** - Out-of-the-box creative solutions
        
        **RiskAnalyst** - Risk assessment and mitigation strategies
        """)
    
    # Technology Stack
    st.subheader("🛠️ Technology Stack")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Frontend:**")
        st.write("• Streamlit")
        st.write("• Plotly")
        st.write("• Pandas")
    
    with col2:
        st.write("**Backend:**")
        st.write("• Python asyncio")
        st.write("• aiohttp")
        st.write("• PyYAML")
    
    with col3:
        st.write("**AI Models:**")
        st.write("• Ollama")
        st.write("• Llama 3.2")
        st.write("• Gemma 3")
        st.write("• DeepSeek")
    
    # Version Information
    st.subheader("📋 Version Information")
    st.info("Local Agent Collaboration System v1.0.0")

# Main Application Logic
def main():
    """Main application entry point."""
    init_session_state()
    render_sidebar()
    
    try:
        if st.session_state.current_page == "main":
            if st.session_state.collaboration_in_progress:
                render_collaboration_interface()
            elif st.session_state.collaboration_results:
                render_consensus_dashboard()
            else:
                render_main_page()
        
        elif st.session_state.current_page == "history":
            render_history_page()
        
        elif st.session_state.current_page == "settings":
            render_settings_page()
        
        elif st.session_state.current_page == "about":
            render_about_page()
        
        elif st.session_state.current_page == "results":
            render_consensus_dashboard()
    
    except Exception as e:
        st.error(f"Application error: {e}")
        st.write("**Traceback:**")
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
