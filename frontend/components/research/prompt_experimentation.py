"""
Prompt Experimentation Framework
Research-grade framework for testing and comparing different prompt strategies
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional, Union, Tuple
import time
from datetime import datetime
import json
import uuid
import os
import itertools
import re
from pydantic import BaseModel, Field
from collections import defaultdict

# Try to import AI pipeline components
try:
    from ai_pipeline.agents.analysis_agent import AnalysisAgent
    from ai_pipeline.agents.query_agent import QueryAgent
    from ai_pipeline.memory.shared_memory import SharedMemory
    from ai_pipeline.security.metrics_collector import SecurityMetricsCollector
    PIPELINE_COMPONENTS_AVAILABLE = True
except ImportError:
    PIPELINE_COMPONENTS_AVAILABLE = False


class ExperimentVariable(BaseModel):
    """Model for experiment variable"""
    name: str
    values: List[str]
    description: Optional[str] = None


class ExperimentResult(BaseModel):
    """Model for experiment result"""
    variable_values: Dict[str, str]
    prompt: str
    response: str
    metrics: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class Experiment(BaseModel):
    """Model for prompt experiment"""
    id: str
    name: str
    description: Optional[str] = None
    variables: List[ExperimentVariable]
    template: str
    results: List[ExperimentResult] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class PromptExperimentationFramework:
    """
    Research-grade framework for prompt experimentation
    
    Features:
    - A/B testing of prompt variations
    - Factorial design experiments
    - Prompt template management
    - Result visualization and comparison
    - Metric collection and analysis
    - Export and sharing capabilities
    """
    
    def __init__(self, experiments_dir: str = "prompt_experiments"):
        """
        Initialize the prompt experimentation framework
        
        Args:
            experiments_dir: Directory to store experiment data
        """
        self.experiments_dir = experiments_dir
        os.makedirs(self.experiments_dir, exist_ok=True)
        
        # Load existing experiments
        self.experiments: Dict[str, Experiment] = {}
        self._load_experiments()
        
        # Initialize metrics collector if available
        self.metrics_collector = None
        if PIPELINE_COMPONENTS_AVAILABLE:
            self.metrics_collector = SecurityMetricsCollector(
                metrics_dir="security_metrics",
                enable_persistence=True
            )
        
        # Initialize session state for experiment settings
        if "current_experiment_id" not in st.session_state:
            st.session_state.current_experiment_id = None
    
    def _load_experiments(self):
        """Load existing experiments from disk"""
        if not os.path.exists(self.experiments_dir):
            return
        
        experiment_files = [f for f in os.listdir(self.experiments_dir) if f.endswith(".json")]
        
        for file_name in experiment_files:
            try:
                with open(os.path.join(self.experiments_dir, file_name), "r") as f:
                    experiment_data = json.load(f)
                    experiment = Experiment(**experiment_data)
                    self.experiments[experiment.id] = experiment
            except Exception as e:
                st.error(f"Error loading experiment {file_name}: {str(e)}")
    
    def _save_experiment(self, experiment: Experiment):
        """Save experiment to disk"""
        experiment_path = os.path.join(self.experiments_dir, f"{experiment.id}.json")
        
        with open(experiment_path, "w") as f:
            json.dump(experiment.dict(), f, indent=2, default=str)
    
    def create_experiment(self, 
                         name: str, 
                         description: str, 
                         variables: Dict[str, List[str]], 
                         template: str) -> str:
        """
        Create a new experiment
        
        Args:
            name: Name of the experiment
            description: Description of the experiment
            variables: Dictionary of variable names and their possible values
            template: Prompt template with variable placeholders
            
        Returns:
            ID of the created experiment
        """
        # Create experiment ID
        experiment_id = str(uuid.uuid4())
        
        # Create experiment variables
        experiment_variables = []
        for var_name, var_values in variables.items():
            experiment_variables.append(
                ExperimentVariable(
                    name=var_name,
                    values=var_values
                )
            )
        
        # Create experiment
        experiment = Experiment(
            id=experiment_id,
            name=name,
            description=description,
            variables=experiment_variables,
            template=template
        )
        
        # Save experiment
        self.experiments[experiment_id] = experiment
        self._save_experiment(experiment)
        
        return experiment_id
    
    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """
        Get experiment by ID
        
        Args:
            experiment_id: ID of the experiment
            
        Returns:
            Experiment if found, None otherwise
        """
        return self.experiments.get(experiment_id)
    
    def list_experiments(self) -> List[Dict[str, Any]]:
        """
        List all experiments
        
        Returns:
            List of experiment summaries
        """
        return [
            {
                "id": exp.id,
                "name": exp.name,
                "description": exp.description,
                "variables": len(exp.variables),
                "combinations": self._count_combinations(exp),
                "results": len(exp.results),
                "created_at": exp.created_at
            }
            for exp in self.experiments.values()
        ]
    
    def _count_combinations(self, experiment: Experiment) -> int:
        """
        Count the number of variable combinations in an experiment
        
        Args:
            experiment: Experiment to count combinations for
            
        Returns:
            Number of combinations
        """
        return np.prod([len(var.values) for var in experiment.variables])
    
    def _generate_combinations(self, experiment: Experiment) -> List[Dict[str, str]]:
        """
        Generate all variable combinations for an experiment
        
        Args:
            experiment: Experiment to generate combinations for
            
        Returns:
            List of variable combinations
        """
        var_names = [var.name for var in experiment.variables]
        var_values = [var.values for var in experiment.variables]
        
        combinations = []
        for values in itertools.product(*var_values):
            combination = dict(zip(var_names, values))
            combinations.append(combination)
        
        return combinations
    
    def _format_prompt(self, template: str, variables: Dict[str, str]) -> str:
        """
        Format prompt template with variable values
        
        Args:
            template: Prompt template
            variables: Variable values
            
        Returns:
            Formatted prompt
        """
        prompt = template
        for var_name, var_value in variables.items():
            prompt = prompt.replace(f"{{{var_name}}}", var_value)
        
        return prompt
    
    def run_experiment(self, 
                      experiment_id: str, 
                      context_ids: Optional[List[str]] = None,
                      max_combinations: int = 10) -> List[Dict[str, Any]]:
        """
        Run an experiment with all variable combinations
        
        Args:
            experiment_id: ID of the experiment to run
            context_ids: List of context IDs for the query
            max_combinations: Maximum number of combinations to run
            
        Returns:
            List of experiment results
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return []
        
        # Generate combinations
        combinations = self._generate_combinations(experiment)
        
        # Limit combinations if needed
        if len(combinations) > max_combinations:
            st.warning(f"Limiting to {max_combinations} combinations out of {len(combinations)} possible combinations")
            combinations = combinations[:max_combinations]
        
        results = []
        
        # Run each combination
        for i, combination in enumerate(combinations):
            with st.spinner(f"Running combination {i+1}/{len(combinations)}: {combination}"):
                # Format prompt
                prompt = self._format_prompt(experiment.template, combination)
                
                # Run query
                start_time = time.time()
                
                if PIPELINE_COMPONENTS_AVAILABLE:
                    # Use direct agent access
                    try:
                        # Initialize shared memory
                        memory = SharedMemory()
                        
                        # Initialize query agent
                        query_agent = QueryAgent(
                            shared_memory=memory,
                            verbose=True
                        )
                        
                        # Run query
                        response = query_agent.run(
                            query=prompt,
                            context_ids=context_ids or []
                        )
                        
                        # Get metrics
                        metrics = {
                            "latency_ms": (time.time() - start_time) * 1000,
                            "token_count": query_agent.get_token_count(),
                            "security_score": 1.0  # Default value
                        }
                        
                        # Get security metrics if available
                        if self.metrics_collector:
                            security_metrics = self.metrics_collector.get_metrics()
                            if security_metrics:
                                metrics["security_events"] = security_metrics.get("total_events", 0)
                                metrics["security_blocked"] = security_metrics.get("blocked_events", 0)
                                
                                # Calculate security score
                                total = metrics["security_events"]
                                if total > 0:
                                    blocked = metrics["security_blocked"]
                                    metrics["security_score"] = 1.0 - (blocked / total)
                    
                    except Exception as e:
                        # Fallback to mock response
                        response = f"Error running query: {str(e)}"
                        metrics = {
                            "latency_ms": (time.time() - start_time) * 1000,
                            "error": str(e)
                        }
                
                else:
                    # Mock response for testing
                    time.sleep(0.5)  # Simulate processing time
                    response = f"Mock response for prompt: {prompt}"
                    metrics = {
                        "latency_ms": (time.time() - start_time) * 1000,
                        "token_count": len(prompt.split()),
                        "security_score": 0.95
                    }
                
                # Create result
                result = ExperimentResult(
                    variable_values=combination,
                    prompt=prompt,
                    response=response,
                    metrics=metrics
                )
                
                # Add to experiment
                experiment.results.append(result)
                results.append(result.dict())
        
        # Update experiment
        experiment.updated_at = datetime.now()
        self._save_experiment(experiment)
        
        return results
    
    def analyze_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """
        Analyze experiment results
        
        Args:
            experiment_id: ID of the experiment to analyze
            
        Returns:
            Analysis results
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment or not experiment.results:
            return {}
        
        # Convert results to DataFrame
        results_data = []
        for result in experiment.results:
            data = {
                "prompt": result.prompt,
                "response": result.response,
                "response_length": len(result.response),
                "timestamp": result.timestamp
            }
            
            # Add metrics
            for metric_name, metric_value in result.metrics.items():
                data[f"metric_{metric_name}"] = metric_value
            
            # Add variable values
            for var_name, var_value in result.variable_values.items():
                data[f"var_{var_name}"] = var_value
            
            results_data.append(data)
        
        df = pd.DataFrame(results_data)
        
        # Calculate metrics by variable
        analysis = {}
        
        for var in experiment.variables:
            var_name = var.name
            var_column = f"var_{var_name}"
            
            if var_column in df.columns:
                # Calculate metrics by variable value
                var_metrics = {}
                
                for var_value in var.values:
                    value_df = df[df[var_column] == var_value]
                    
                    if not value_df.empty:
                        var_metrics[var_value] = {
                            "count": len(value_df),
                            "avg_response_length": value_df["response_length"].mean(),
                            "avg_latency_ms": value_df["metric_latency_ms"].mean() if "metric_latency_ms" in value_df.columns else None,
                            "avg_token_count": value_df["metric_token_count"].mean() if "metric_token_count" in value_df.columns else None,
                            "avg_security_score": value_df["metric_security_score"].mean() if "metric_security_score" in value_df.columns else None
                        }
                
                analysis[var_name] = var_metrics
        
        return {
            "experiment": {
                "id": experiment.id,
                "name": experiment.name,
                "description": experiment.description,
                "created_at": experiment.created_at,
                "updated_at": experiment.updated_at
            },
            "summary": {
                "total_combinations": self._count_combinations(experiment),
                "completed_combinations": len(experiment.results),
                "avg_latency_ms": df["metric_latency_ms"].mean() if "metric_latency_ms" in df.columns else None,
                "avg_response_length": df["response_length"].mean()
            },
            "variable_analysis": analysis,
            "raw_data": df.to_dict(orient="records")
        }
    
    def delete_experiment(self, experiment_id: str) -> bool:
        """
        Delete an experiment
        
        Args:
            experiment_id: ID of the experiment to delete
            
        Returns:
            True if deleted, False otherwise
        """
        if experiment_id in self.experiments:
            # Delete from memory
            del self.experiments[experiment_id]
            
            # Delete from disk
            experiment_path = os.path.join(self.experiments_dir, f"{experiment_id}.json")
            if os.path.exists(experiment_path):
                os.remove(experiment_path)
            
            return True
        
        return False
    
    def render_experiment_creator(self):
        """Render experiment creator UI"""
        st.subheader("Create New Experiment")
        
        with st.form("experiment_creator"):
            name = st.text_input("Experiment Name", "Test Experiment")
            description = st.text_area("Description", "Testing different prompt formats")
            
            # Template
            st.markdown("### Prompt Template")
            st.markdown("Use `{variable_name}` as placeholders for variables")
            template = st.text_area(
                "Template", 
                "Analyze the politician's voting record with a {tone} tone and {detail_level} detail level."
            )
            
            # Variables
            st.markdown("### Variables")
            
            # Variable 1
            col1, col2 = st.columns([1, 2])
            with col1:
                var1_name = st.text_input("Variable 1 Name", "tone")
            with col2:
                var1_values = st.text_input("Variable 1 Values (comma separated)", "formal,casual,academic")
            
            # Variable 2
            col1, col2 = st.columns([1, 2])
            with col1:
                var2_name = st.text_input("Variable 2 Name", "detail_level")
            with col2:
                var2_values = st.text_input("Variable 2 Values (comma separated)", "high,medium,low")
            
            # Optional Variable 3
            add_var3 = st.checkbox("Add another variable")
            var3_name = ""
            var3_values = ""
            
            if add_var3:
                col1, col2 = st.columns([1, 2])
                with col1:
                    var3_name = st.text_input("Variable 3 Name", "perspective")
                with col2:
                    var3_values = st.text_input("Variable 3 Values (comma separated)", "neutral,critical,supportive")
            
            # Submit button
            submitted = st.form_submit_button("Create Experiment")
            
            if submitted:
                # Validate inputs
                if not name or not template:
                    st.error("Name and template are required")
                    return
                
                # Parse variables
                variables = {}
                
                if var1_name and var1_values:
                    variables[var1_name] = [v.strip() for v in var1_values.split(",")]
                
                if var2_name and var2_values:
                    variables[var2_name] = [v.strip() for v in var2_values.split(",")]
                
                if add_var3 and var3_name and var3_values:
                    variables[var3_name] = [v.strip() for v in var3_values.split(",")]
                
                # Validate variables
                if not variables:
                    st.error("At least one variable is required")
                    return
                
                # Check if all variables in template
                for var_name in variables.keys():
                    if f"{{{var_name}}}" not in template:
                        st.warning(f"Variable '{var_name}' is not used in the template")
                
                # Create experiment
                experiment_id = self.create_experiment(
                    name=name,
                    description=description,
                    variables=variables,
                    template=template
                )
                
                st.success(f"Experiment created with ID: {experiment_id}")
                st.session_state.current_experiment_id = experiment_id
    
    def render_experiment_runner(self, experiment_id: str):
        """
        Render experiment runner UI
        
        Args:
            experiment_id: ID of the experiment to run
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            st.error(f"Experiment {experiment_id} not found")
            return
        
        st.subheader(f"Run Experiment: {experiment.name}")
        st.markdown(experiment.description)
        
        with st.form("experiment_runner"):
            # Context
            st.markdown("### Context")
            context_ids = st.text_input("Context IDs (comma separated)", "Sanna Marin")
            
            # Combinations limit
            combinations_count = self._count_combinations(experiment)
            max_combinations = st.slider(
                "Maximum Combinations to Run",
                min_value=1,
                max_value=min(20, combinations_count),
                value=min(10, combinations_count)
            )
            
            # Submit button
            submitted = st.form_submit_button("Run Experiment")
            
            if submitted:
                # Parse context IDs
                context_id_list = [c.strip() for c in context_ids.split(",")] if context_ids else []
                
                # Run experiment
                results = self.run_experiment(
                    experiment_id=experiment_id,
                    context_ids=context_id_list,
                    max_combinations=max_combinations
                )
                
                st.success(f"Experiment completed with {len(results)} combinations")
                
                # Show results summary
                if results:
                    st.markdown("### Results Summary")
                    
                    # Calculate average metrics
                    avg_latency = np.mean([r["metrics"].get("latency_ms", 0) for r in results])
                    avg_tokens = np.mean([r["metrics"].get("token_count", 0) for r in results if "token_count" in r["metrics"]])
                    avg_security = np.mean([r["metrics"].get("security_score", 1.0) for r in results if "security_score" in r["metrics"]])
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Avg. Latency", f"{avg_latency:.1f} ms")
                    with col2:
                        st.metric("Avg. Tokens", f"{avg_tokens:.1f}")
                    with col3:
                        st.metric("Avg. Security Score", f"{avg_security:.2f}")
    
    def render_experiment_results(self, experiment_id: str):
        """
        Render experiment results UI
        
        Args:
            experiment_id: ID of the experiment to show results for
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            st.error(f"Experiment {experiment_id} not found")
            return
        
        if not experiment.results:
            st.info("No results available for this experiment yet")
            return
        
        st.subheader(f"Results: {experiment.name}")
        
        # Get analysis
        analysis = self.analyze_experiment(experiment_id)
        
        # Show summary metrics
        summary = analysis.get("summary", {})
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Combinations Run", f"{summary.get('completed_combinations', 0)}/{summary.get('total_combinations', 0)}")
        with col2:
            st.metric("Avg. Latency", f"{summary.get('avg_latency_ms', 0):.1f} ms")
        with col3:
            st.metric("Avg. Response Length", f"{summary.get('avg_response_length', 0):.1f} chars")
        
        # Show variable analysis
        st.markdown("### Variable Analysis")
        
        variable_analysis = analysis.get("variable_analysis", {})
        
        tabs = st.tabs([var_name for var_name in variable_analysis.keys()])
        
        for i, (var_name, tab) in enumerate(zip(variable_analysis.keys(), tabs)):
            with tab:
                var_metrics = variable_analysis[var_name]
                
                # Prepare data for charts
                values = list(var_metrics.keys())
                response_lengths = [metrics.get("avg_response_length", 0) for metrics in var_metrics.values()]
                latencies = [metrics.get("avg_latency_ms", 0) for metrics in var_metrics.values()]
                security_scores = [metrics.get("avg_security_score", 0) for metrics in var_metrics.values() if metrics.get("avg_security_score") is not None]
                
                # Create charts
                col1, col2 = st.columns(2)
                
                with col1:
                    # Response length chart
                    fig = px.bar(
                        x=values,
                        y=response_lengths,
                        labels={"x": var_name, "y": "Avg. Response Length"},
                        title=f"Response Length by {var_name}"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Latency chart
                    fig = px.bar(
                        x=values,
                        y=latencies,
                        labels={"x": var_name, "y": "Avg. Latency (ms)"},
                        title=f"Latency by {var_name}"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                if security_scores:
                    # Security score chart
                    fig = px.bar(
                        x=values,
                        y=security_scores,
                        labels={"x": var_name, "y": "Avg. Security Score"},
                        title=f"Security Score by {var_name}"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # Show individual results
        st.markdown("### Individual Results")
        
        raw_data = analysis.get("raw_data", [])
        if raw_data:
            # Convert to DataFrame for display
            df = pd.DataFrame(raw_data)
            
            # Extract variable columns
            var_columns = [col for col in df.columns if col.startswith("var_")]
            
            # Create expandable sections for each result
            for i, result in enumerate(raw_data):
                # Create title from variables
                title_parts = []
                for var_col in var_columns:
                    var_name = var_col[4:]  # Remove "var_" prefix
                    var_value = result[var_col]
                    title_parts.append(f"{var_name}={var_value}")
                
                title = ", ".join(title_parts)
                
                with st.expander(f"Result {i+1}: {title}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Prompt")
                        st.text_area("", result["prompt"], height=150, key=f"prompt_{i}")
                    
                    with col2:
                        st.markdown("#### Response")
                        st.text_area("", result["response"], height=150, key=f"response_{i}")
                    
                    # Metrics
                    st.markdown("#### Metrics")
                    metric_cols = st.columns(4)
                    
                    with metric_cols[0]:
                        st.metric("Latency", f"{result.get('metric_latency_ms', 0):.1f} ms")
                    
                    with metric_cols[1]:
                        st.metric("Response Length", len(result["response"]))
                    
                    with metric_cols[2]:
                        if "metric_token_count" in result:
                            st.metric("Token Count", result["metric_token_count"])
                    
                    with metric_cols[3]:
                        if "metric_security_score" in result:
                            st.metric("Security Score", f"{result['metric_security_score']:.2f}")
    
    def render_experiment_list(self):
        """Render experiment list UI"""
        st.subheader("Experiments")
        
        experiments = self.list_experiments()
        
        if not experiments:
            st.info("No experiments created yet")
            return
        
        # Convert to DataFrame for display
        df = pd.DataFrame(experiments)
        df["created_at"] = pd.to_datetime(df["created_at"])
        df["created_at"] = df["created_at"].dt.strftime("%Y-%m-%d %H:%M")
        
        # Rename columns
        df.columns = ["ID", "Name", "Description", "Variables", "Combinations", "Results", "Created"]
        
        # Display as table
        st.dataframe(df, use_container_width=True)
        
        # Select experiment
        selected_id = st.selectbox(
            "Select Experiment",
            options=[exp["id"] for exp in experiments],
            format_func=lambda x: next((exp["name"] for exp in experiments if exp["id"] == x), x)
        )
        
        if selected_id:
            st.session_state.current_experiment_id = selected_id
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("View Results"):
                    st.session_state.experiment_action = "results"
            
            with col2:
                if st.button("Run Experiment"):
                    st.session_state.experiment_action = "run"
            
            with col3:
                if st.button("Delete Experiment"):
                    if self.delete_experiment(selected_id):
                        st.success(f"Experiment deleted")
                        st.session_state.current_experiment_id = None
                        st.rerun()
                    else:
                        st.error("Failed to delete experiment")
    
    def render(self):
        """Render the prompt experimentation framework UI"""
        st.title("Prompt Experimentation Framework")
        
        # Initialize session state
        if "experiment_action" not in st.session_state:
            st.session_state.experiment_action = None
        
        # Create tabs
        tab1, tab2, tab3 = st.tabs(["Experiments", "Create New", "Documentation"])
        
        with tab1:
            self.render_experiment_list()
            
            # Handle experiment actions
            if st.session_state.current_experiment_id:
                if st.session_state.experiment_action == "results":
                    self.render_experiment_results(st.session_state.current_experiment_id)
                elif st.session_state.experiment_action == "run":
                    self.render_experiment_runner(st.session_state.current_experiment_id)
        
        with tab2:
            self.render_experiment_creator()
        
        with tab3:
            st.markdown("""
            ## Prompt Experimentation Framework Documentation
            
            This research-grade framework allows you to systematically test different prompt variations and analyze their impact on AI responses.
            
            ### Key Features
            
            - **A/B Testing**: Compare different prompt formulations to see which produces better results
            - **Factorial Design**: Test multiple variables simultaneously to understand interactions
            - **Metrics Collection**: Analyze response quality, latency, token usage, and security scores
            - **Visualization**: Compare results visually with interactive charts
            
            ### How to Use
            
            1. **Create an Experiment**:
               - Define a prompt template with variable placeholders like `{variable_name}`
               - Add variables and their possible values
               - Each variable will be substituted into the template
            
            2. **Run the Experiment**:
               - Provide context IDs (e.g., politician names)
               - Set the maximum number of combinations to run
               - The system will test all combinations and collect results
            
            3. **Analyze Results**:
               - View metrics for each variable value
               - Compare response lengths, latency, and security scores
               - Examine individual responses
            
            ### Best Practices
            
            - Start with a small number of variables and values to keep combinations manageable
            - Use clear, descriptive variable names
            - Test one aspect of prompting at a time for clearer insights
            - Consider security implications of different prompt strategies
            """)


# For standalone testing
if __name__ == "__main__":
    framework = PromptExperimentationFramework()
    framework.render()
