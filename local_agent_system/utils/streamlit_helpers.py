"""
Streamlit helper utilities for the Local Agent Collaboration System.

This module provides utilities for async handling, data processing,
and visualization within the Streamlit environment.
"""

import asyncio
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import json
import time
import threading
from dataclasses import dataclass

@dataclass
class CollaborationProgress:
    """Track collaboration progress state."""
    phase: str
    agent: str
    status: str
    progress: float
    timestamp: datetime

class StreamlitAsyncRunner:
    """
    Helper class to run async functions within Streamlit.
    
    Streamlit doesn't natively support async/await, so this class
    provides a bridge to execute async operations safely.
    """
    
    @staticmethod
    def run_with_spinner(coro, message: str = "Processing..."):
        """
        Run async coroutine with Streamlit spinner.
        
        Args:
            coro: The coroutine to run
            message: Spinner message
            
        Returns:
            Result of the coroutine
        """
        with st.spinner(message):
            return StreamlitAsyncRunner.run_async(coro)
    
    @staticmethod
    def run_async(coro):
        """
        Run an async coroutine in Streamlit context.
        
        Args:
            coro: The coroutine to run
            
        Returns:
            The result of the coroutine
        """
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, create a new thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result(timeout=30)
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop exists, create a new one
            return asyncio.run(coro)
        except Exception as e:
            st.error(f"Async execution failed: {e}")
            return None

class CollaborationVisualizer:
    """
    Creates visualizations for collaboration data.
    
    Provides methods to generate charts, graphs, and visual representations
    of agent collaboration progress and results.
    """
    
    @staticmethod
    def create_confidence_heatmap(collaboration_data: Dict[str, Any]) -> go.Figure:
        """
        Create a heatmap showing confidence levels across agents and phases.
        
        Args:
            collaboration_data: The collaboration data dictionary
            
        Returns:
            Plotly heatmap figure
        """
        # Extract confidence data
        agents = collaboration_data.get('agents', [])
        phases = list(collaboration_data.get('phases', {}).keys())
        
        # Create confidence matrix
        confidence_matrix = []
        agent_labels = []
        
        for agent in agents:
            agent_confidences = []
            for phase in phases:
                phase_data = collaboration_data['phases'].get(phase, {})
                results = phase_data.get('results', {})
                agent_result = results.get(agent, {})
                confidence = agent_result.get('confidence_level', 0)
                agent_confidences.append(confidence * 100)
            
            confidence_matrix.append(agent_confidences)
            agent_labels.append(agent.replace('_', ' '))
        
        fig = go.Figure(data=go.Heatmap(
            z=confidence_matrix,
            x=[p.title() for p in phases],
            y=agent_labels,
            colorscale='RdYlGn',
            text=[[f"{val:.1f}%" for val in row] for row in confidence_matrix],
            texttemplate="%{text}",
            textfont={"size": 10},
            colorbar=dict(title="Confidence %")
        ))
        
        fig.update_layout(
            title="Agent Confidence Heatmap",
            xaxis_title="Collaboration Phases",
            yaxis_title="Agents",
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_progress_radar(collaboration_data: Dict[str, Any]) -> go.Figure:
        """
        Create a radar chart showing overall progress.
        
        Args:
            collaboration_data: The collaboration data dictionary
            
        Returns:
            Plotly radar chart figure
        """
        phases = collaboration_data.get('phases', {})
        
        # Calculate completion percentages
        phase_completion = []
        phase_names = []
        
        for phase_name, phase_data in phases.items():
            if phase_data.get('status') == 'completed':
                completion = 100
            elif phase_data.get('status') == 'running':
                completion = phase_data.get('progress', 50)
            else:
                completion = 0
            
            phase_completion.append(completion)
            phase_names.append(phase_name.title())
        
        # Add first point again to close the radar
        phase_completion.append(phase_completion[0])
        phase_names.append(phase_names[0])
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=phase_completion,
            theta=phase_names,
            fill='toself',
            name='Progress',
            line_color='blue'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=False,
            title="Collaboration Progress Radar"
        )
        
        return fig
    
    @staticmethod
    def create_timeline_gantt(collaboration_data: Dict[str, Any]) -> go.Figure:
        """
        Create a Gantt chart showing phase timeline.
        
        Args:
            collaboration_data: The collaboration data dictionary
            
        Returns:
            Plotly Gantt chart figure
        """
        timeline_data = []
        
        start_time = datetime.fromisoformat(collaboration_data.get('timestamp', datetime.now().isoformat()))
        
        for i, (phase_name, phase_data) in enumerate(collaboration_data.get('phases', {}).items()):
            status = phase_data.get('status', 'pending')
            
            # Calculate start and end times (simulated)
            phase_start = start_time.replace(minute=start_time.minute + i * 2)
            
            if status == 'completed':
                phase_end = phase_start.replace(minute=phase_start.minute + 2)
                color = 'green'
            elif status == 'running':
                phase_end = datetime.now()
                color = 'orange'
            else:
                phase_end = phase_start
                color = 'gray'
            
            timeline_data.append(dict(
                Task=phase_name.title(),
                Start=phase_start,
                Finish=phase_end,
                Resource=status.title()
            ))
        
        if timeline_data:
            df = pd.DataFrame(timeline_data)
            
            fig = px.timeline(
                df, 
                x_start="Start", 
                x_end="Finish", 
                y="Task", 
                color="Resource",
                title="Collaboration Phase Timeline"
            )
            
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(height=300)
            
            return fig
        
        return go.Figure()

class SessionManager:
    """
    Manages collaboration sessions and persistence.
    
    Handles saving, loading, and managing collaboration history
    within the Streamlit session state.
    """
    
    @staticmethod
    def save_collaboration(collaboration_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Save collaboration data to session history.
        
        Args:
            collaboration_data: The collaboration data to save
            filename: Optional filename for export
            
        Returns:
            Generated filename
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"collaboration_{timestamp}.json"
        
        # Add to session history if not already there
        if collaboration_data not in st.session_state.collaboration_history:
            st.session_state.collaboration_history.append(collaboration_data)
        
        return filename
    
    @staticmethod
    def export_collaboration(collaboration_data: Dict[str, Any], format: str = "json") -> str:
        """
        Export collaboration data in specified format.
        
        Args:
            collaboration_data: The collaboration data to export
            format: Export format ("json", "csv", "txt")
            
        Returns:
            Formatted data string
        """
        if format == "json":
            return json.dumps(collaboration_data, indent=2, default=str)
        
        elif format == "csv":
            return SessionManager._to_csv(collaboration_data)
        
        elif format == "txt":
            return SessionManager._to_text_summary(collaboration_data)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    @staticmethod
    def _to_csv(collaboration_data: Dict[str, Any]) -> str:
        """Convert collaboration data to CSV format."""
        rows = []
        
        for phase_name, phase_data in collaboration_data.get('phases', {}).items():
            for agent_name, result in phase_data.get('results', {}).items():
                rows.append({
                    'Timestamp': result.get('timestamp', ''),
                    'Phase': phase_name,
                    'Agent': agent_name,
                    'Confidence': result.get('confidence_level', 0),
                    'Response_Length': len(result.get('main_response', '')),
                    'Key_Insights_Count': len(result.get('key_insights', [])),
                    'Main_Response': result.get('main_response', '').replace('\n', ' ')[:500]
                })
        
        if rows:
            df = pd.DataFrame(rows)
            return df.to_csv(index=False)
        else:
            return "No data available"
    
    @staticmethod
    def _to_text_summary(collaboration_data: Dict[str, Any]) -> str:
        """Convert collaboration data to text summary."""
        lines = []
        lines.append("COLLABORATION SUMMARY REPORT")
        lines.append("=" * 50)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        lines.append("PROBLEM STATEMENT:")
        lines.append(collaboration_data.get('problem', 'No problem statement'))
        lines.append("")
        
        lines.append("PARTICIPATING AGENTS:")
        for agent in collaboration_data.get('agents', []):
            lines.append(f"• {agent}")
        lines.append("")
        
        lines.append("PHASE RESULTS:")
        for phase_name, phase_data in collaboration_data.get('phases', {}).items():
            lines.append(f"\n{phase_name.upper()} PHASE:")
            lines.append("-" * 30)
            
            for agent_name, result in phase_data.get('results', {}).items():
                lines.append(f"\n{agent_name} (Confidence: {result.get('confidence_level', 0):.1%}):")
                lines.append(result.get('main_response', 'No response')[:300] + "...")
        
        return "\n".join(lines)

class ProgressTracker:
    """
    Tracks and updates collaboration progress in real-time.
    
    Provides utilities for monitoring and displaying live progress
    updates during collaboration execution.
    """
    
    def __init__(self):
        self.progress_history: List[CollaborationProgress] = []
    
    def update_progress(self, phase: str, agent: str, status: str, progress: float):
        """
        Update progress for a specific agent and phase.
        
        Args:
            phase: Current phase name
            agent: Agent name
            status: Current status
            progress: Progress percentage (0-100)
        """
        progress_update = CollaborationProgress(
            phase=phase,
            agent=agent,
            status=status,
            progress=progress,
            timestamp=datetime.now()
        )
        
        self.progress_history.append(progress_update)
    
    def get_latest_progress(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the latest progress state for all agents.
        
        Returns:
            Dictionary of agent progress states
        """
        latest_progress = {}
        
        for progress in reversed(self.progress_history):
            agent_key = f"{progress.agent}_{progress.phase}"
            if agent_key not in latest_progress:
                latest_progress[agent_key] = {
                    'phase': progress.phase,
                    'agent': progress.agent,
                    'status': progress.status,
                    'progress': progress.progress,
                    'timestamp': progress.timestamp
                }
        
        return latest_progress
    
    def render_progress_cards(self, collaboration_data: Dict[str, Any]):
        """
        Render progress cards for each agent.
        
        Args:
            collaboration_data: Current collaboration data
        """
        agents = collaboration_data.get('agents', [])
        phases = collaboration_data.get('phases', {})
        
        cols = st.columns(len(agents))
        
        for i, agent_name in enumerate(agents):
            with cols[i]:
                st.subheader(f"🤖 {agent_name}")
                
                for phase_name, phase_data in phases.items():
                    status = "⏳"
                    if agent_name in phase_data.get('results', {}):
                        status = "✅"
                    elif phase_data.get('status') == 'running':
                        status = "🔄"
                    
                    st.write(f"{status} {phase_name.title()}")

def format_duration(start_time: str, end_time: Optional[str] = None) -> str:
    """
    Format duration between two timestamps.
    
    Args:
        start_time: Start timestamp (ISO format)
        end_time: End timestamp (ISO format), defaults to now
        
    Returns:
        Formatted duration string
    """
    try:
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_time.replace('Z', '+00:00')) if end_time else datetime.now()
        
        duration = end - start
        
        if duration.total_seconds() < 60:
            return f"{int(duration.total_seconds())}s"
        elif duration.total_seconds() < 3600:
            return f"{int(duration.total_seconds() / 60)}m {int(duration.total_seconds() % 60)}s"
        else:
            hours = int(duration.total_seconds() / 3600)
            minutes = int((duration.total_seconds() % 3600) / 60)
            return f"{hours}h {minutes}m"
    
    except Exception:
        return "Unknown"

def create_status_badge(status: str) -> str:
    """
    Create a colored status badge.
    
    Args:
        status: Status string
        
    Returns:
        Formatted status badge
    """
    badge_map = {
        'pending': '⏳ Pending',
        'running': '🔄 Running', 
        'completed': '✅ Completed',
        'failed': '❌ Failed',
        'error': '🚨 Error'
    }
    
    return badge_map.get(status.lower(), f"❓ {status}")

def truncate_response(text: str, max_length: int = 150) -> str:
    """
    Truncate text response with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."

def calculate_collaboration_metrics(collaboration_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate metrics for collaboration data.
    
    Args:
        collaboration_data: The collaboration data
        
    Returns:
        Dictionary of calculated metrics
    """
    phases = collaboration_data.get('phases', {})
    agents = collaboration_data.get('agents', [])
    
    # Count completed phases
    completed_phases = sum(1 for phase in phases.values() if phase.get('status') == 'completed')
    total_phases = len(phases)
    
    # Calculate average confidence
    all_confidences = []
    for phase_data in phases.values():
        for result in phase_data.get('results', {}).values():
            confidence = result.get('confidence_level', 0)
            if confidence > 0:
                all_confidences.append(confidence)
    
    avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
    
    # Count total responses
    total_responses = sum(
        len(phase_data.get('results', {})) 
        for phase_data in phases.values()
    )
    
    # Calculate completion percentage
    completion_percentage = (completed_phases / total_phases * 100) if total_phases > 0 else 0
    
    return {
        'completed_phases': completed_phases,
        'total_phases': total_phases,
        'completion_percentage': completion_percentage,
        'average_confidence': avg_confidence,
        'total_responses': total_responses,
        'active_agents': len(agents),
        'total_insights': sum(
            len(result.get('key_insights', [])) 
            for phase_data in phases.values() 
            for result in phase_data.get('results', {}).values()
        )
    }
