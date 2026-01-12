"""
SiteGuard AI - Enhanced Streamlit Web Application
Interactive dashboard for PPE detection with Live Webcam, Analytics, and Dark Mode
"""

import sys
from pathlib import Path
import streamlit as st
import cv2
import numpy as np
from PIL import Image
from datetime import datetime, timedelta
import json
import io
import time
from collections import defaultdict
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.vision.detector import PPEDetector, create_detector
from app.core.llm.generator import ReportGenerator, ReportMetadata, ReportFormat, create_report_generator
from utils.config import load_config
from loguru import logger


# Page configuration
st.set_page_config(
    page_title="SiteGuard AI - Safety Monitoring Pro",
    page_icon="🦺",
    layout="wide",
    initial_sidebar_state="expanded"
)


def get_custom_css(dark_mode=False):
    """Generate custom CSS based on theme."""
    if dark_mode:
        return """
<style>
    /* Dark Mode Styling */
    .main {
        background-color: #0e1117;
    }
    .main-header {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(120deg, #1f77b4 0%, #ff7f0e 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1.5rem 0;
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #2a5298 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #3a7bd5;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.4);
    }
    .violation-alert {
        background: linear-gradient(135deg, #d32f2f 0%, #f44336 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #ff5252;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(244,67,54,0.3);
        color: white;
    }
    .success-alert {
        background: linear-gradient(135deg, #388e3c 0%, #4caf50 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #66bb6a;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(76,175,80,0.3);
        color: white;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #1f77b4 0%, #3a7bd5 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(31,119,180,0.3);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #3a7bd5 0%, #5a9bd5 100%);
        box-shadow: 0 6px 16px rgba(31,119,180,0.5);
        transform: translateY(-2px);
    }
    .stat-box {
        background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #3949ab;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .webcam-frame {
        border: 3px solid #1f77b4;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
    }
</style>
"""
    else:
        return """
<style>
    /* Light Mode Styling */
    .main-header {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(120deg, #1f77b4 0%, #ff7f0e 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1.5rem 0;
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .metric-card {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #1976d2;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    }
    .violation-alert {
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #d32f2f;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .success-alert {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #388e3c;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #1f77b4 0%, #3a7bd5 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(31,119,180,0.2);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #2980b9 0%, #4a8bd5 100%);
        box-shadow: 0 6px 16px rgba(31,119,180,0.4);
        transform: translateY(-2px);
    }
    .stat-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #1976d2;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .webcam-frame {
        border: 3px solid #1f77b4;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
</style>
"""


def init_session_state():
    """Initialize session state variables."""
    defaults = {
        'detector': None,
        'report_generator': None,
        'results': None,
        'report': None,
        'video_results': None,
        'dark_mode': False,
        'history': [],  # Store detection history
        'total_detections': 0,
        'total_violations': 0,
        'webcam_active': False,
        'webcam_results': []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def load_models():
    """Load detection and report generation models."""
    try:
        with st.spinner("🔄 Loading AI models..."):
            # Load detector
            if st.session_state.detector is None:
                config = {
                    "model_path": "runs/train/ppe-detector4/weights/best.pt",
                    "confidence_threshold": st.session_state.confidence_threshold,
                    "device": "cpu"  # Change to cuda if GPU available
                }
                st.session_state.detector = create_detector(config)

            # Load report generator (optional if API key not available)
            if st.session_state.report_generator is None:
                try:
                    config = {
                        "provider": st.session_state.llm_provider,
                        "temperature": 0.3
                    }
                    if st.session_state.llm_provider == "ollama":
                        config["model"] = st.session_state.get("llm_model", "llama3")
                    st.session_state.report_generator = create_report_generator(config)
                except ValueError as e:
                    st.warning(f"⚠️ Report generator not available: {e}")
                    st.info("💡 Detection will still work. Add API key for report generation.")
                    st.session_state.report_generator = None

        st.success("✅ System ready!")
        return True
    except Exception as e:
        st.error(f"❌ Error loading models: {e}")
        logger.error(f"Model loading failed: {e}")
        return False


def create_analytics_charts():
    """Create analytics dashboard with charts."""
    st.header("📊 Analytics Dashboard")

    # Generate sample data if no history
    if len(st.session_state.history) == 0:
        st.info("📈 No detection history yet. Analyze some images to see statistics!")
        return

    # Prepare data
    timestamps = [h.get('timestamp', datetime.now()) for h in st.session_state.history]
    violations = [len(h.get('violations', [])) for h in st.session_state.history]
    detection_times = [h.get('inference_time_ms', 0) for h in st.session_state.history]

    # Violation types count
    violation_types = defaultdict(int)
    for h in st.session_state.history:
        for v in h.get('violations', []):
            vtype = v.get('type', 'unknown')
            violation_types[vtype] += 1

    # Row 1: Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_analyses = len(st.session_state.history)
        st.metric("🔍 Total Analyses", total_analyses,
                 delta=f"+{total_analyses}" if total_analyses > 0 else None)
    with col2:
        total_viol = sum(violations)
        st.metric("⚠️ Total Violations", total_viol,
                 delta=f"+{total_viol}" if total_viol > 0 else None,
                 delta_color="inverse")
    with col3:
        avg_time = np.mean(detection_times) if detection_times else 0
        st.metric("⚡ Avg Detection Time", f"{avg_time:.1f}ms")
    with col4:
        compliance_rate = ((total_analyses - sum(1 for v in violations if v > 0)) / total_analyses * 100) if total_analyses > 0 else 100
        st.metric("✅ Compliance Rate", f"{compliance_rate:.1f}%",
                 delta=f"{compliance_rate-50:.1f}%" if compliance_rate > 50 else None)

    st.markdown("---")

    # Row 2: Charts
    col_left, col_right = st.columns(2)

    with col_left:
        # Violation Trend Line Chart
        st.subheader("📈 Violation Trend Over Time")
        if len(timestamps) > 1:
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=list(range(len(violations))),
                y=violations,
                mode='lines+markers',
                name='Violations',
                line=dict(color='#f44336', width=3),
                marker=dict(size=8, color='#d32f2f'),
                fill='tozeroy',
                fillcolor='rgba(244, 67, 54, 0.2)'
            ))
            fig_trend.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_title="Analysis #",
                yaxis_title="Violations",
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=12)
            )
            st.plotly_chart(fig_trend, width="stretch")
        else:
            st.info("Need more data points for trend analysis")

    with col_right:
        # Violation Types Pie Chart
        st.subheader("🎯 Violation Types Distribution")
        if violation_types:
            labels = [k.replace('_', ' ').title() for k in violation_types.keys()]
            values = list(violation_types.values())

            fig_pie = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker=dict(colors=px.colors.sequential.RdBu),
                textinfo='label+percent',
                textfont=dict(size=12)
            )])
            fig_pie.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                showlegend=True,
                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_pie, width="stretch")
        else:
            st.success("✅ No violations detected!")

    # Row 3: Performance Chart
    st.subheader("⚡ Detection Performance")
    col_perf1, col_perf2 = st.columns(2)

    with col_perf1:
        # Detection Time Bar Chart
        if detection_times:
            fig_perf = go.Figure()
            fig_perf.add_trace(go.Bar(
                x=list(range(len(detection_times))),
                y=detection_times,
                marker=dict(
                    color=detection_times,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="ms")
                ),
                text=[f"{t:.1f}ms" for t in detection_times],
                textposition='outside'
            ))
            fig_perf.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_title="Analysis #",
                yaxis_title="Time (ms)",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=11)
            )
            st.plotly_chart(fig_perf, width="stretch")

    with col_perf2:
        # Compliance Gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=compliance_rate,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Compliance Rate", 'font': {'size': 20}},
            delta={'reference': 80, 'increasing': {'color': "#4caf50"}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "#1f77b4"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': '#ffcdd2'},
                    {'range': [50, 80], 'color': '#fff9c4'},
                    {'range': [80, 100], 'color': '#c8e6c9'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_gauge.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=60, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12)
        )
        st.plotly_chart(fig_gauge, width="stretch")


def webcam_detection_page():
    """Live webcam detection page."""
    st.header("📹 Live Webcam Detection")

    st.markdown("""
    <div class="metric-card">
    <h3>🎥 Real-Time PPE Monitoring</h3>
    <p>Use your webcam for live safety compliance monitoring. Perfect for demonstrations!</p>
    </div>
    """, unsafe_allow_html=True)

    col_cam1, col_cam2 = st.columns([2, 1])

    with col_cam1:
        # Camera input
        camera_image = st.camera_input("📸 Take a photo from webcam")

        if camera_image is not None:
            # Convert to numpy array
            image = Image.open(camera_image)
            image_np = np.array(image)

            if len(image_np.shape) == 2:  # Grayscale
                image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
            elif image_np.shape[2] == 4:  # RGBA
                image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGR)
            else:  # RGB
                image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

            if st.button("🔍 Analyze Webcam Image", type="primary"):
                if st.session_state.detector is None:
                    st.error("⚠️ Please initialize the system first!")
                else:
                    with st.spinner("🔄 Analyzing..."):
                        start_time = time.time()
                        results = st.session_state.detector.detect(image_np, annotate=True)
                        inference_time = (time.time() - start_time) * 1000

                        # Store results
                        st.session_state.results = results

                        # Add to history
                        st.session_state.history.append({
                            'timestamp': datetime.now(),
                            'violations': results.violations,
                            'detections': len(results.detections),
                            'inference_time_ms': inference_time
                        })

                        st.success(f"✅ Analysis complete! ({inference_time:.1f}ms)")
                        st.rerun()

    with col_cam2:
        st.markdown("### 💡 Tips")
        st.markdown("""
        - Ensure good lighting
        - Position yourself 2-3m from camera
        - Wear/remove PPE to test detection
        - Try different angles
        - Multiple people supported
        """)

        if st.session_state.results:
            results = st.session_state.results
            st.metric("👤 People Detected", len([d for d in results.detections if 'person' in d.class_name.lower()]))
            st.metric("⚠️ Violations", len(results.violations))

            # Generate report button for webcam
            if results.has_violations and st.session_state.report_generator:
                st.markdown("---")
                if st.button("📄 Generate Report", key="webcam_report", type="primary"):
                    with st.spinner("📝 Generating report..."):
                        metadata = ReportMetadata(
                            location=st.session_state.location,
                            timestamp=datetime.now(),
                            site_id=st.session_state.site_id or None,
                            inspector_id=st.session_state.inspector_id or None
                        )
                        report_format = ReportFormat[st.session_state.report_format.upper()]
                        try:
                            report = st.session_state.report_generator.generate_report(
                                violations=results.violations,
                                metadata=metadata,
                                format=report_format
                            )
                            st.session_state.report = report
                            st.success("✅ Report generated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed: {e}")


def main():
    """Main application with tabs."""
    init_session_state()

    # Header with theme toggle
    col_title, col_theme = st.columns([4, 1])
    with col_title:
        st.markdown('<h1 class="main-header">🦺 SiteGuard AI Pro</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; color: #666; font-size: 1.1rem;">Advanced Industrial Safety & Compliance Monitor</p>', unsafe_allow_html=True)

    with col_theme:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🌓 Toggle Theme"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

    # Apply theme
    st.markdown(get_custom_css(st.session_state.dark_mode), unsafe_allow_html=True)

    # Sidebar configuration
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/1f77b4/FFFFFF?text=SiteGuard+AI", width="stretch")
        st.header("⚙️ Configuration")

        # Model settings
        st.subheader("🎯 Detection Settings")
        st.session_state.confidence_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.1,
            max_value=0.9,
            value=0.5,
            step=0.05,
            help="Minimum confidence score for detections"
        )

        # LLM settings
        st.subheader("📝 Report Generation")
        st.session_state.llm_provider = st.selectbox(
            "LLM Provider",
            ["ollama", "openai", "gemini"],
            help="Select the LLM provider"
        )

        if st.session_state.llm_provider == "ollama":
            st.session_state.llm_model = st.selectbox(
                "Ollama Model",
                ["llama3", "llama3.1", "llama3.2", "mistral", "phi3", "gemma2"],
                help="Select Ollama model"
            )

        st.session_state.report_format = st.selectbox(
            "Report Format",
            ["formal", "technical", "executive", "email"],
            help="Select report format"
        )

        # Metadata
        st.subheader("📍 Site Information")
        st.session_state.location = st.text_input(
            "Location/Site Name",
            value="Construction Site A"
        )

        st.session_state.site_id = st.text_input("Site ID (Optional)", value="")
        st.session_state.inspector_id = st.text_input("Inspector ID (Optional)", value="")

        st.markdown("---")

        # Initialize button
        if st.button("🚀 Initialize System", type="primary"):
            load_models()

        # System stats
        if st.session_state.detector:
            st.markdown("---")
            st.markdown("### 📊 System Stats")
            metrics = st.session_state.detector.get_metrics()
            st.metric("Total Analyses", len(st.session_state.history))
            st.metric("Violations Found", sum(len(h.get('violations', [])) for h in st.session_state.history))

            if st.button("🗑️ Clear History"):
                st.session_state.history = []
                st.rerun()

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📸 Image Analysis",
        "📹 Live Webcam",
        "🎥 Video Analysis",
        "📊 Analytics Dashboard"
    ])

    with tab1:
        # Original image upload functionality
        st.header("📸 Image Upload & Analysis")

        uploaded_file = st.file_uploader(
            "Upload CCTV snapshot or workplace photo",
            type=["jpg", "jpeg", "png"],
            help="Supported formats: JPG, PNG"
        )

        col_img1, col_img2 = st.columns(2)

        with col_img1:
            if uploaded_file is not None:
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image", width="stretch")

                # Convert to numpy
                image_np = np.array(image)
                if len(image_np.shape) == 2:
                    image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
                elif image_np.shape[2] == 4:
                    image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGR)
                else:
                    image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

                if st.button("🔍 Analyze Image", type="primary", disabled=st.session_state.detector is None):
                    if st.session_state.detector:
                        with st.spinner("🔄 Detecting PPE violations..."):
                            start_time = time.time()
                            results = st.session_state.detector.detect(image_np, annotate=True)
                            inference_time = (time.time() - start_time) * 1000

                            st.session_state.results = results

                            # Add to history
                            st.session_state.history.append({
                                'timestamp': datetime.now(),
                                'violations': results.violations,
                                'detections': len(results.detections),
                                'inference_time_ms': inference_time
                            })

                            # Generate report if needed
                            if results.has_violations and st.session_state.report_generator:
                                with st.spinner("📝 Generating report..."):
                                    metadata = ReportMetadata(
                                        location=st.session_state.location,
                                        timestamp=datetime.now(),
                                        site_id=st.session_state.site_id or None,
                                        inspector_id=st.session_state.inspector_id or None
                                    )
                                    report_format = ReportFormat[st.session_state.report_format.upper()]
                                    try:
                                        report = st.session_state.report_generator.generate_report(
                                            violations=results.violations,
                                            metadata=metadata,
                                            format=report_format
                                        )
                                        st.session_state.report = report
                                    except Exception as e:
                                        st.warning(f"⚠️ Report generation failed: {e}")

                        st.rerun()

        with col_img2:
            st.header("📊 Detection Results")

            if st.session_state.results:
                results = st.session_state.results

                # Display annotated image
                if hasattr(results, 'annotated_image') and results.annotated_image is not None:
                    annotated_rgb = cv2.cvtColor(results.annotated_image, cv2.COLOR_BGR2RGB)
                    st.image(annotated_rgb, caption="Detection Results", width="stretch")

                # Metrics
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric("👤 Detections", len(results.detections))
                with col_m2:
                    st.metric("⚠️ Violations", len(results.violations))
                with col_m3:
                    st.metric("⚡ Speed", f"{results.inference_time_ms:.0f}ms")

                # Violation alerts
                if results.has_violations:
                    st.markdown('<div class="violation-alert">', unsafe_allow_html=True)
                    st.markdown("### ⚠️ VIOLATIONS DETECTED")
                    for i, violation in enumerate(results.violations, 1):
                        vtype = violation.get('type', 'unknown').replace('_', ' ').title()
                        severity = violation.get('severity', 'medium').upper()
                        st.markdown(f"**{i}. {vtype}** - Severity: {severity}")
                    st.markdown('</div>', unsafe_allow_html=True)

                    # Manual report generation button
                    st.markdown("### 📝 Report Generation")
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("📄 Generate Report", type="primary", disabled=st.session_state.report_generator is None):
                            if st.session_state.report_generator:
                                with st.spinner("📝 Generating incident report..."):
                                    metadata = ReportMetadata(
                                        location=st.session_state.location,
                                        timestamp=datetime.now(),
                                        site_id=st.session_state.site_id or None,
                                        inspector_id=st.session_state.inspector_id or None
                                    )
                                    report_format = ReportFormat[st.session_state.report_format.upper()]
                                    try:
                                        report = st.session_state.report_generator.generate_report(
                                            violations=results.violations,
                                            metadata=metadata,
                                            format=report_format
                                        )
                                        st.session_state.report = report
                                        st.success("✅ Report generated!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Report generation failed: {e}")
                            else:
                                st.error("⚠️ Report generator not initialized. Configure LLM provider in sidebar.")

                    with col_btn2:
                        if st.session_state.report:
                            st.info(f"📄 Report: {st.session_state.report.report_id[:8]}...")
                        else:
                            st.info("💡 No report generated yet")
                else:
                    st.markdown('<div class="success-alert">', unsafe_allow_html=True)
                    st.markdown("### ✅ NO VIOLATIONS")
                    st.markdown("All personnel compliant!")
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("👆 Upload and analyze an image to see results")

    with tab2:
        webcam_detection_page()

    with tab3:
        st.header("🎥 Video Analysis")

        st.markdown("""
        <div class="metric-card">
        <h3>🎬 Video Processing</h3>
        <p>Upload CCTV footage or workplace videos for frame-by-frame PPE detection</p>
        </div>
        """, unsafe_allow_html=True)

        col_vid1, col_vid2 = st.columns([2, 1])

        with col_vid1:
            # Video uploader
            uploaded_video = st.file_uploader(
                "Upload CCTV footage or workplace video",
                type=["mp4", "avi", "mov", "mkv"],
                help="Supported formats: MP4, AVI, MOV, MKV"
            )

            if uploaded_video is not None:
                st.video(uploaded_video)

                # Video processing options
                st.markdown("### 🎬 Video Processing Options")

                col_opt1, col_opt2 = st.columns(2)
                with col_opt1:
                    frame_skip = st.slider(
                        "Process every N frames",
                        min_value=1,
                        max_value=30,
                        value=5,
                        help="Skip frames for faster processing (1 = every frame)"
                    )
                with col_opt2:
                    max_frames = st.number_input(
                        "Max frames to process",
                        min_value=10,
                        max_value=1000,
                        value=100,
                        help="Limit total frames analyzed"
                    )

                # Detection button for video
                if st.button("🔍 Analyze Video", type="primary", disabled=st.session_state.detector is None):
                    if st.session_state.detector is None:
                        st.error("⚠️ Please initialize the system first!")
                    else:
                        # Save uploaded video temporarily
                        import tempfile
                        import os

                        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                            tmp_file.write(uploaded_video.read())
                            video_path = tmp_file.name

                        # Process video
                        with st.spinner("🔄 Processing video frames..."):
                            cap = cv2.VideoCapture(video_path)

                            # Get video properties
                            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                            fps = cap.get(cv2.CAP_PROP_FPS)
                            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                            st.info(f"📹 Video: {total_frames} frames @ {fps:.1f} FPS | {width}x{height}")

                            # Create output video writer with H.264 codec for browser compatibility
                            output_path = video_path.replace('.mp4', '_annotated.mp4')
                            fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264 codec
                            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

                            # Storage for results
                            all_violations = []
                            violation_frames = []
                            frames_processed = 0
                            frame_count = 0

                            # Progress bar
                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            # Store last detection results for frame interpolation
                            last_annotated = None

                            while cap.isOpened():
                                ret, frame = cap.read()
                                if not ret:
                                    break

                                # Process every Nth frame
                                if frame_count % frame_skip == 0:
                                    # Run detection
                                    results = st.session_state.detector.detect(frame, annotate=True)

                                    # Store the annotated frame
                                    if results.annotated_image is not None:
                                        last_annotated = results.annotated_image.copy()
                                        out.write(last_annotated)
                                    else:
                                        last_annotated = frame.copy()
                                        out.write(frame)

                                    if results.has_violations:
                                        # Store violations with timestamp
                                        timestamp = frame_count / fps
                                        for violation in results.violations:
                                            violation['frame'] = frame_count
                                            violation['timestamp'] = f"{int(timestamp//60):02d}:{int(timestamp%60):02d}"
                                            all_violations.append(violation)

                                        # Store annotated frame
                                        violation_frames.append({
                                            'frame_num': frame_count,
                                            'timestamp': f"{int(timestamp//60):02d}:{int(timestamp%60):02d}",
                                            'image': results.annotated_image,
                                            'violation_count': len(results.violations)
                                        })

                                    frames_processed += 1
                                    if frames_processed >= max_frames:
                                        break

                                    progress = min(frames_processed / max_frames, 1.0)
                                    progress_bar.progress(progress)
                                    status_text.text(f"Processed {frames_processed}/{max_frames} frames | Found {len(violation_frames)} violation frames")
                                else:
                                    # Use last annotated frame to prevent blinking
                                    if last_annotated is not None:
                                        out.write(last_annotated)
                                    else:
                                        out.write(frame)

                                frame_count += 1

                            cap.release()
                            out.release()

                            # Read annotated video for display
                            with open(output_path, 'rb') as f:
                                annotated_video_bytes = f.read()

                            # Clean up temp files
                            os.unlink(video_path)
                            os.unlink(output_path)

                            # Store results in session state
                            st.session_state.video_results = {
                                'total_frames': total_frames,
                                'processed_frames': frames_processed,
                                'violation_frames': violation_frames,
                                'all_violations': all_violations,
                                'fps': fps,
                                'annotated_video': annotated_video_bytes
                            }

                            # Add to history for analytics
                            st.session_state.history.append({
                                'timestamp': datetime.now(),
                                'violations': all_violations,
                                'detections': frames_processed,
                                'inference_time_ms': (frames_processed / fps) * 1000 if fps > 0 else 0
                            })

                            progress_bar.progress(1.0)
                            status_text.text(f"✅ Complete! Processed {frames_processed} frames, found {len(violation_frames)} frames with violations")

                        # Generate report for video if violations found
                        if len(all_violations) > 0 and st.session_state.report_generator:
                            with st.spinner("📝 Generating video incident report..."):
                                metadata = ReportMetadata(
                                    location=st.session_state.location,
                                    timestamp=datetime.now(),
                                    site_id=st.session_state.site_id or None,
                                    inspector_id=st.session_state.inspector_id or None
                                )

                                report_format = ReportFormat[st.session_state.report_format.upper()]

                                try:
                                    report = st.session_state.report_generator.generate_report(
                                        violations=all_violations[:10],  # Limit to first 10 unique violations
                                        metadata=metadata,
                                        format=report_format
                                    )
                                    st.session_state.report = report
                                except Exception as e:
                                    st.warning(f"⚠️ Could not generate report: {e}")
                                    st.session_state.report = None
                        elif len(all_violations) > 0 and not st.session_state.report_generator:
                            st.info("💡 Report generation skipped (API key not configured)")

                        st.success("✅ Video analysis complete!")
                        st.rerun()

        with col_vid2:
            st.markdown("### 💡 Video Tips")
            st.markdown("""
            **Best practices:**
            - Use clear, well-lit footage
            - Recommended: 30 FPS
            - Max resolution: 1080p
            - Skip frames for faster processing

            **Processing time:**
            - 100 frames ~10-20 seconds
            - GPU: 3-5x faster

            **Output:**
            - Annotated video with bounding boxes
            - Violation timeline
            - Frame-by-frame analysis
            - Downloadable video
            """)

        # Display video results if available
        if 'video_results' in st.session_state and st.session_state.video_results is not None:
            st.markdown("---")
            video_results = st.session_state.video_results

            col_vres1, col_vres2 = st.columns([2, 1])

            with col_vres1:
                # Display annotated video
                st.markdown("### 🎬 Annotated Video with Detections")
                st.video(video_results['annotated_video'])

                # Download button for annotated video
                st.download_button(
                    label="⬇️ Download Annotated Video",
                    data=video_results['annotated_video'],
                    file_name=f"ppe_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                    mime="video/mp4"
                )

            with col_vres2:
                # Summary metrics
                st.markdown("### 📊 Summary")
                st.metric("Frames Processed", video_results['processed_frames'])
                st.metric("Violation Frames", len(video_results['violation_frames']))

                if video_results['processed_frames'] > 0:
                    violation_rate = len(video_results['violation_frames']) / video_results['processed_frames'] * 100
                    st.metric("Violation Rate", f"{violation_rate:.1f}%")

            # Display violation frames
            if len(video_results['violation_frames']) > 0:
                st.markdown('<div class="violation-alert">', unsafe_allow_html=True)
                st.markdown(f"### ⚠️ {len(video_results['violation_frames'])} FRAMES WITH VIOLATIONS")
                st.markdown('</div>', unsafe_allow_html=True)

                # Frame selector
                st.markdown("### 🎞️ Violation Frames")
                frame_idx = st.selectbox(
                    "Select frame to view",
                    range(len(video_results['violation_frames'])),
                    format_func=lambda i: f"Frame {video_results['violation_frames'][i]['frame_num']} @ {video_results['violation_frames'][i]['timestamp']} ({video_results['violation_frames'][i]['violation_count']} violations)"
                )

                # Display selected frame
                selected_frame = video_results['violation_frames'][frame_idx]
                frame_rgb = cv2.cvtColor(selected_frame['image'], cv2.COLOR_BGR2RGB)
                st.image(frame_rgb, caption=f"Frame {selected_frame['frame_num']} @ {selected_frame['timestamp']}", width="stretch")

                # Violation timeline
                st.markdown("### 📊 Violation Timeline")
                timeline_data = []
                for vf in video_results['violation_frames']:
                    timeline_data.append({
                        'Frame': vf['frame_num'],
                        'Time': vf['timestamp'],
                        'Violations': vf['violation_count']
                    })
                st.dataframe(timeline_data, width="stretch")

                # Detailed violations
                with st.expander("📋 All Violations Detected"):
                    for i, violation in enumerate(video_results['all_violations'][:50], 1):  # Limit display
                        vtype = violation.get('type', 'unknown').replace('_', ' ').title()
                        frame = violation.get('frame', 'N/A')
                        timestamp = violation.get('timestamp', 'N/A')
                        st.markdown(f"**{i}. {vtype}** - Frame {frame} @ {timestamp}")
            else:
                st.markdown('<div class="success-alert">', unsafe_allow_html=True)
                st.markdown("### ✅ NO VIOLATIONS DETECTED IN VIDEO")
                st.markdown("All frames analyzed showed compliance with safety regulations.")
                st.markdown('</div>', unsafe_allow_html=True)

    with tab4:
        create_analytics_charts()

    # Report section (if generated)
    if st.session_state.report is not None:
        st.markdown("---")
        st.header("📄 Generated Incident Report")

        report = st.session_state.report

        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.metric("Report ID", report.report_id[:8] + "...")
        with col_r2:
            st.metric("Violations", len(report.violations))
        with col_r3:
            st.metric("Format", report.format.value.upper())

        st.text_area("Report Content", value=report.text, height=300)

        # Export buttons
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            st.download_button(
                "📥 Download as JSON",
                data=json.dumps(report.to_dict(), indent=2),
                file_name=f"{report.report_id}.json",
                mime="application/json"
            )
        with col_e2:
            st.download_button(
                "📥 Download as TXT",
                data=report.text,
                file_name=f"{report.report_id}.txt",
                mime="text/plain"
            )

    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: {'#999' if st.session_state.dark_mode else '#666'}; padding: 2rem 0;">
        <p><strong>SiteGuard AI Pro</strong> - Enhanced Edition with Live Detection & Analytics</p>
        <p>Powered by YOLOv8, LLMs & Plotly | CAIE Final Project 2024</p>
        <p style="font-size: 0.9rem;">© 2024 Muhamad Adib bin Suid</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
