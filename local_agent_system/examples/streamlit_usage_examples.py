"""
Example usage scripts for the Local Agent Collaboration Streamlit App.

This file provides example code snippets and usage patterns for
integrating with the Streamlit application programmatically.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any

# Example: Programmatic collaboration execution
async def run_example_collaboration():
    """
    Example of how to run a collaboration programmatically.
    This could be useful for automated testing or batch processing.
    """
    
    # Import the collaboration system
    from collaboration.system import LocalAgent2AgentSystem
    from config.settings import load_config
    
    # Load configuration
    config = load_config("config/presets/balanced.yaml")
    
    # Initialize the system
    system = LocalAgent2AgentSystem()
    await system.initialize(config)
    
    # Define the problem
    problem = """
    How can we create a sustainable and profitable business model 
    for a new eco-friendly product line that appeals to both 
    environmentally conscious consumers and cost-sensitive buyers?
    """
    
    # Run the collaboration
    try:
        results = await system.collaborate(problem)
        
        # Process results
        print("Collaboration completed successfully!")
        print(f"Problem: {problem[:100]}...")
        print(f"Agents: {len(results.get('agent_responses', []))}")
        print(f"Consensus: {results.get('consensus', {}).get('recommendation', 'No consensus')}")
        
        return results
    
    except Exception as e:
        print(f"Collaboration failed: {e}")
        return None
    
    finally:
        await system.cleanup()

# Example: Custom agent configuration
def create_custom_agent_config():
    """
    Example of creating a custom agent configuration.
    """
    
    custom_config = {
        "DataScientist_Alpha": {
            "model": "llama3.2:3b",
            "temperature": 0.2,
            "personality": "Highly analytical, focuses on quantitative data and statistical insights. Prefers evidence-based conclusions.",
            "enabled": True
        },
        "ProductManager_Beta": {
            "model": "gemma3:1b", 
            "temperature": 0.6,
            "personality": "Strategic thinker with strong focus on user needs and market opportunities. Balances technical feasibility with user value.",
            "enabled": True
        },
        "TechArchitect_Gamma": {
            "model": "deepseek-r1:latest",
            "temperature": 0.4,
            "personality": "Systems-oriented engineer focused on scalable, maintainable solutions. Considers technical debt and implementation complexity.",
            "enabled": True
        },
        "CreativeInnovator_Delta": {
            "model": "llama3.2:3b",
            "temperature": 0.9,
            "personality": "Bold creative thinker who challenges conventional wisdom. Proposes innovative solutions and thinks outside the box.",
            "enabled": True
        },
        "RiskAnalyst_Epsilon": {
            "model": "llama3.2:3b",
            "temperature": 0.1,
            "personality": "Cautious analyst focused on identifying potential problems and risks. Ensures comprehensive evaluation of downsides.",
            "enabled": True
        }
    }
    
    return custom_config

# Example: Processing collaboration results
def analyze_collaboration_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example of how to analyze and process collaboration results.
    
    Args:
        results: Raw collaboration results from the system
        
    Returns:
        Processed analysis summary
    """
    
    analysis = {
        "summary": {},
        "agent_performance": {},
        "key_insights": [],
        "recommendations": [],
        "confidence_analysis": {}
    }
    
    # Extract basic summary
    analysis["summary"] = {
        "problem": results.get("problem", ""),
        "timestamp": results.get("timestamp", ""),
        "total_agents": len(results.get("agents", [])),
        "completed_phases": sum(1 for phase in results.get("phases", {}).values() 
                               if phase.get("status") == "completed")
    }
    
    # Analyze agent performance
    for phase_name, phase_data in results.get("phases", {}).items():
        for agent_name, agent_result in phase_data.get("results", {}).items():
            if agent_name not in analysis["agent_performance"]:
                analysis["agent_performance"][agent_name] = {
                    "total_responses": 0,
                    "avg_confidence": 0,
                    "phases_participated": []
                }
            
            perf = analysis["agent_performance"][agent_name]
            perf["total_responses"] += 1
            perf["phases_participated"].append(phase_name)
            
            # Update confidence average
            confidence = agent_result.get("confidence_level", 0)
            current_avg = perf["avg_confidence"]
            perf["avg_confidence"] = (current_avg * (perf["total_responses"] - 1) + confidence) / perf["total_responses"]
    
    # Extract key insights
    for phase_data in results.get("phases", {}).values():
        for agent_result in phase_data.get("results", {}).values():
            insights = agent_result.get("key_insights", [])
            analysis["key_insights"].extend(insights)
    
    # Compile recommendations
    consensus_phase = results.get("phases", {}).get("consensus", {})
    for agent_result in consensus_phase.get("results", {}).values():
        recommendation = {
            "agent": agent_result.get("agent_id", "Unknown"),
            "confidence": agent_result.get("confidence_level", 0),
            "recommendation": agent_result.get("main_response", ""),
            "reasoning": agent_result.get("reasoning", "")
        }
        analysis["recommendations"].append(recommendation)
    
    # Sort recommendations by confidence
    analysis["recommendations"].sort(key=lambda x: x["confidence"], reverse=True)
    
    # Confidence analysis
    all_confidences = []
    for phase_data in results.get("phases", {}).values():
        for agent_result in phase_data.get("results", {}).values():
            conf = agent_result.get("confidence_level", 0)
            if conf > 0:
                all_confidences.append(conf)
    
    if all_confidences:
        analysis["confidence_analysis"] = {
            "average": sum(all_confidences) / len(all_confidences),
            "min": min(all_confidences),
            "max": max(all_confidences),
            "count": len(all_confidences)
        }
    
    return analysis

# Example: Export results to different formats
def export_results(results: Dict[str, Any], format: str = "json", filename: str = None) -> str:
    """
    Example of exporting collaboration results to different formats.
    
    Args:
        results: Collaboration results
        format: Export format ('json', 'csv', 'markdown')
        filename: Optional filename
        
    Returns:
        Exported data as string
    """
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"collaboration_export_{timestamp}"
    
    if format == "json":
        return json.dumps(results, indent=2, default=str)
    
    elif format == "csv":
        import pandas as pd
        
        # Flatten results for CSV
        rows = []
        for phase_name, phase_data in results.get("phases", {}).items():
            for agent_name, agent_result in phase_data.get("results", {}).items():
                rows.append({
                    "Phase": phase_name,
                    "Agent": agent_name,
                    "Confidence": agent_result.get("confidence_level", 0),
                    "Response": agent_result.get("main_response", ""),
                    "Timestamp": agent_result.get("timestamp", "")
                })
        
        df = pd.DataFrame(rows)
        return df.to_csv(index=False)
    
    elif format == "markdown":
        lines = []
        lines.append(f"# Collaboration Results")
        lines.append(f"**Problem:** {results.get('problem', 'N/A')}")
        lines.append(f"**Timestamp:** {results.get('timestamp', 'N/A')}")
        lines.append("")
        
        for phase_name, phase_data in results.get("phases", {}).items():
            lines.append(f"## {phase_name.title()} Phase")
            for agent_name, agent_result in phase_data.get("results", {}).items():
                lines.append(f"### {agent_name}")
                lines.append(f"**Confidence:** {agent_result.get('confidence_level', 0):.2%}")
                lines.append(agent_result.get("main_response", "No response"))
                lines.append("")
        
        return "\n".join(lines)
    
    else:
        raise ValueError(f"Unsupported export format: {format}")

# Example: Streamlit integration patterns
def streamlit_integration_example():
    """
    Example patterns for integrating with Streamlit components.
    """
    
    import streamlit as st
    import plotly.express as px
    import pandas as pd
    
    # Example: Dynamic agent configuration in Streamlit
    def render_agent_config():
        """Render dynamic agent configuration UI."""
        
        st.subheader("🤖 Agent Configuration")
        
        available_models = ["llama3.2:3b", "gemma3:1b", "deepseek-r1:latest"]
        agent_names = ["DataScientist", "ProductManager", "TechArchitect", "CreativeInnovator", "RiskAnalyst"]
        
        config = {}
        
        for agent_name in agent_names:
            with st.expander(f"Configure {agent_name}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    enabled = st.checkbox("Enabled", value=True, key=f"{agent_name}_enabled")
                    model = st.selectbox("Model", available_models, key=f"{agent_name}_model")
                
                with col2:
                    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1, key=f"{agent_name}_temp")
                    max_tokens = st.number_input("Max Tokens", 100, 2000, 800, key=f"{agent_name}_tokens")
                
                personality = st.text_area("Personality", key=f"{agent_name}_personality")
                
                config[agent_name] = {
                    "enabled": enabled,
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "personality": personality
                }
        
        return config
    
    # Example: Results visualization
    def render_confidence_chart(results: Dict[str, Any]):
        """Render confidence visualization."""
        
        # Extract confidence data
        data = []
        for phase_name, phase_data in results.get("phases", {}).items():
            for agent_name, agent_result in phase_data.get("results", {}).items():
                data.append({
                    "Phase": phase_name.title(),
                    "Agent": agent_name,
                    "Confidence": agent_result.get("confidence_level", 0) * 100
                })
        
        if data:
            df = pd.DataFrame(data)
            fig = px.bar(df, x="Agent", y="Confidence", color="Phase",
                        title="Agent Confidence by Phase")
            st.plotly_chart(fig, use_container_width=True)
    
    # Example: Progress tracking
    def render_progress_tracking(collaboration_state: Dict[str, Any]):
        """Render real-time progress tracking."""
        
        phases = collaboration_state.get("phases", {})
        
        st.subheader("🔄 Collaboration Progress")
        
        cols = st.columns(len(phases))
        
        for i, (phase_name, phase_data) in enumerate(phases.items()):
            with cols[i]:
                status = phase_data.get("status", "pending")
                progress = phase_data.get("progress", 0)
                
                if status == "completed":
                    st.success(f"✅ {phase_name.title()}")
                    st.progress(1.0)
                elif status == "running":
                    st.warning(f"🔄 {phase_name.title()}")
                    st.progress(progress / 100)
                else:
                    st.info(f"⏳ {phase_name.title()}")
                    st.progress(0.0)

# Example: Testing utilities
def test_collaboration_system():
    """
    Example test function for validating the collaboration system.
    """
    
    test_cases = [
        {
            "name": "Simple Business Problem",
            "problem": "How can we improve customer satisfaction?",
            "expected_agents": 5,
            "expected_phases": 4
        },
        {
            "name": "Technical Challenge",
            "problem": "Design a scalable microservices architecture for a high-traffic web application.",
            "expected_agents": 5,
            "expected_phases": 4
        },
        {
            "name": "Creative Challenge",
            "problem": "Develop an innovative marketing campaign for a sustainable fashion brand.",
            "expected_agents": 5,
            "expected_phases": 4
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"Running test: {test_case['name']}")
        
        # This would be implemented with actual collaboration system
        # result = await run_collaboration(test_case['problem'])
        
        # Mock result for example
        result = {
            "success": True,
            "agents_participated": test_case['expected_agents'],
            "phases_completed": test_case['expected_phases'],
            "duration": "5 minutes",
            "avg_confidence": 0.85
        }
        
        results.append({
            "test_name": test_case['name'],
            "result": result
        })
        
        print(f"✅ Test completed: {result}")
    
    return results

if __name__ == "__main__":
    # Example usage
    print("🤖 Local Agent Collaboration System - Example Usage")
    print("=" * 60)
    
    # Run example collaboration
    print("\n1. Running example collaboration...")
    # results = asyncio.run(run_example_collaboration())
    
    # Create custom configuration
    print("\n2. Creating custom agent configuration...")
    config = create_custom_agent_config()
    print(f"Created configuration for {len(config)} agents")
    
    # Export example
    print("\n3. Export example...")
    example_results = {
        "problem": "Example problem",
        "timestamp": datetime.now().isoformat(),
        "phases": {"analysis": {"results": {"Agent1": {"confidence_level": 0.85, "main_response": "Example response"}}}}
    }
    
    json_export = export_results(example_results, "json")
    print(f"JSON export: {len(json_export)} characters")
    
    # Test system
    print("\n4. Running system tests...")
    test_results = test_collaboration_system()
    print(f"Completed {len(test_results)} tests")
    
    print("\n✅ All examples completed successfully!")
