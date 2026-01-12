"""
SiteGuard AI - Streamlit Web Application
Interactive dashboard for PPE detection and incident reporting.
"""

import sys
from pathlib import Path
import streamlit as st
import cv2
import numpy as np
from PIL import Image
from datetime import datetime
import json
import io

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.vision.detector import PPEDetector, create_detector
from app.core.llm.generator import ReportGenerator, ReportMetadata, ReportFormat, create_report_generator
from utils.config import load_config
from loguru import logger


# Page configuration
st.set_page_config(
    page_title="SiteGuard AI - Safety Monitoring",
    page_icon="🦺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .violation-alert {
        background-color: #ffebee;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f44336;
        margin: 1rem 0;
    }
    .success-alert {
        background-color: #e8f5e9;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4caf50;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if 'detector' not in st.session_state:
        st.session_state.detector = None
    if 'report_generator' not in st.session_state:
        st.session_state.report_generator = None
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'report' not in st.session_state:
        st.session_state.report = None
    if 'video_results' not in st.session_state:
        st.session_state.video_results = None


def load_models():
    """Load detection and report generation models."""
    try:
        with st.spinner("🔄 Loading AI models..."):
            # Load detector
            if st.session_state.detector is None:
                config = {
                    "model_path": "runs/train/ppe-detector4/weights/best.pt",  # Custom trained PPE model
                    "confidence_threshold": st.session_state.confidence_threshold,
                    "device": "cuda"  # Using GPU for faster inference
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
                    st.info("💡 Detection will still work. Add API key in .env file to enable report generation.")
                    st.session_state.report_generator = None
            
        st.success("✅ Detector loaded successfully!")
        if st.session_state.report_generator:
            st.success("✅ Report generator loaded successfully!")
        return True
    except Exception as e:
        st.error(f"❌ Error loading models: {e}")
        logger.error(f"Model loading failed: {e}")
        return False


def main():
    """Main application."""
    init_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🦺 SiteGuard AI</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">Automated Industrial Safety & Compliance Monitor</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Model settings
        st.subheader("Detection Settings")
        st.session_state.confidence_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.1,
            max_value=0.9,
            value=0.5,
            step=0.05,
            help="Minimum confidence score for detections"
        )
        
        # LLM settings
        st.subheader("Report Generation")
        st.session_state.llm_provider = st.selectbox(
            "LLM Provider",
            ["ollama", "openai", "gemini"],
            help="Select the LLM provider for report generation"
        )
        
        if st.session_state.llm_provider == "ollama":
            st.session_state.llm_model = st.selectbox(
                "Ollama Model",
                ["llama3", "llama3.1", "llama3.2", "mistral", "phi3", "gemma2"],
                help="Select the Ollama model (must be installed locally)"
            )
        else:
            st.session_state.llm_model = None
        
        st.session_state.report_format = st.selectbox(
            "Report Format",
            ["formal", "technical", "executive", "email"],
            help="Select the format for incident reports"
        )
        
        # Metadata
        st.subheader("Site Information")
        st.session_state.location = st.text_input(
            "Location/Site Name",
            value="Construction Site A",
            help="Name or identifier of the inspection location"
        )
        
        st.session_state.site_id = st.text_input(
            "Site ID (Optional)",
            value="",
            help="Internal site identification number"
        )
        
        st.session_state.inspector_id = st.text_input(
            "Inspector ID (Optional)",
            value="",
            help="Inspector or operator identification"
        )
        
        st.markdown("---")
        
        # Load models button
        if st.button("🚀 Initialize System", type="primary"):
            load_models()
        
        # System info
        st.markdown("---")
        st.markdown("### 📊 System Info")
        if st.session_state.detector:
            metrics = st.session_state.detector.get_metrics()
            st.metric("Total Inferences", metrics["total_inferences"])
            st.metric("Violations Detected", metrics["violations_detected"])
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Media type selector
        media_type = st.radio(
            "Select Input Type",
            ["📸 Image", "🎥 Video"],
            horizontal=True
        )
        
        if media_type == "📸 Image":
            st.header("📸 Image Upload")
            
            # File uploader
            uploaded_file = st.file_uploader(
                "Upload CCTV snapshot or workplace photo",
                type=["jpg", "jpeg", "png"],
                help="Supported formats: JPG, PNG"
            )
        else:
            st.header("🎥 Video Upload")
            
            # Video uploader
            uploaded_file = st.file_uploader(
                "Upload CCTV footage or workplace video",
                type=["mp4", "avi", "mov", "mkv"],
                help="Supported formats: MP4, AVI, MOV, MKV"
            )
        
        if uploaded_file is not None and media_type == "📸 Image":
            # Display uploaded image
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", width="stretch")
            
            # Convert to numpy array
            image_np = np.array(image)
            if len(image_np.shape) == 2:  # Grayscale
                image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
            elif image_np.shape[2] == 4:  # RGBA
                image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGR)
            else:  # RGB
                image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
            
            # Detection button
            if st.button("🔍 Analyze Image", type="primary", disabled=st.session_state.detector is None):
                if st.session_state.detector is None:
                    st.error("⚠️ Please initialize the system first!")
                else:
                    with st.spinner("🔄 Detecting PPE violations..."):
                        # Run detection
                        results = st.session_state.detector.detect(
                            image_np,
                            annotate=True
                        )
                        st.session_state.results = results
                        
                        # Generate report if violations found and generator available
                        if results.has_violations and st.session_state.report_generator:
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
                                except Exception as e:
                                    st.warning(f"⚠️ Could not generate report: {e}")
        
        elif uploaded_file is not None and media_type == "🎥 Video":
            # Display video info
            st.video(uploaded_file)
            
            # Video processing options
            st.markdown("### 🎬 Video Processing Options")
            
            col_a, col_b = st.columns(2)
            with col_a:
                frame_skip = st.slider(
                    "Process every N frames",
                    min_value=1,
                    max_value=30,
                    value=5,
                    help="Skip frames for faster processing (1 = every frame)"
                )
            with col_b:
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
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                        tmp_file.write(uploaded_file.read())
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
                        import os
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
    
    with col2:
        st.header("📊 Detection Results")
        
        # Display video results if available
        if 'video_results' in st.session_state and st.session_state.video_results is not None:
            video_results = st.session_state.video_results
            
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
            
            st.markdown("---")
            
            # Summary metrics
            st.markdown("### 📹 Video Analysis Summary")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Frames Processed", video_results['processed_frames'])
            with col_b:
                st.metric("Violation Frames", len(video_results['violation_frames']))
            with col_c:
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
                st.dataframe(timeline_data, use_container_width=True)
                
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
        
        elif st.session_state.results is not None:
            results = st.session_state.results
            
            # Display annotated image
            if hasattr(results, 'annotated_image'):
                annotated_rgb = cv2.cvtColor(results.annotated_image, cv2.COLOR_BGR2RGB)
                st.image(annotated_rgb, caption="Detection Results", width="stretch")
            
            # Display metrics
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Detections", len(results.detections))
            with col_b:
                st.metric("Violations", len(results.violations))
            with col_c:
                st.metric("Inference Time", f"{results.inference_time_ms:.1f}ms")
            
            # Violation alerts
            if results.has_violations:
                st.markdown('<div class="violation-alert">', unsafe_allow_html=True)
                st.markdown("### ⚠️ VIOLATIONS DETECTED")
                
                for i, violation in enumerate(results.violations, 1):
                    vtype = violation.get('type', 'unknown').replace('_', ' ').title()
                    severity = violation.get('severity', 'medium').upper()
                    osha = violation.get('osha_standard', 'N/A')
                    conf = violation.get('confidence', 1.0)
                    desc = violation.get('description', '')
                    
                    st.markdown(f"""
                    **Violation #{i}**: {vtype}
                    - **Severity**: {severity}
                    - **OSHA Standard**: {osha}
                    - **Confidence**: {conf:.1%}
                    - **Description**: {desc}
                    """)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="success-alert">', unsafe_allow_html=True)
                st.markdown("### ✅ NO VIOLATIONS DETECTED")
                st.markdown("All personnel are in compliance with safety regulations.")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Detection details
            with st.expander("📋 Detailed Detection Data"):
                detection_data = []
                for det in results.detections:
                    detection_data.append({
                        "Class": det.class_name,
                        "Confidence": f"{det.confidence:.2%}",
                        "BBox": f"{det.bbox}"
                    })
                st.json(detection_data)
    
    # Report section
    if st.session_state.report is not None:
        st.markdown("---")
        st.header("📄 Incident Report")
        
        report = st.session_state.report
        
        # Report metadata
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric("Report ID", report.report_id)
        with col_b:
            st.metric("Location", report.metadata.location)
        with col_c:
            st.metric("Violations", len(report.violations))
        with col_d:
            st.metric("Format", report.format.value.upper())
        
        # Report text
        st.markdown("### 📝 Report Content")
        st.text_area(
            "Generated Report",
            value=report.text,
            height=400,
            label_visibility="collapsed"
        )
        
        # Recommendations
        if report.recommendations:
            st.markdown("### 💡 Recommendations")
            for i, rec in enumerate(report.recommendations[:5], 1):
                st.markdown(f"{i}. {rec}")
        
        # Export options
        st.markdown("### 💾 Export Options")
        col_x, col_y = st.columns(2)
        
        with col_x:
            # JSON export
            report_json = json.dumps(report.to_dict(), indent=2)
            st.download_button(
                label="📥 Download as JSON",
                data=report_json,
                file_name=f"{report.report_id}.json",
                mime="application/json"
            )
        
        with col_y:
            # Text export
            st.download_button(
                label="📥 Download as TXT",
                data=report.text,
                file_name=f"{report.report_id}.txt",
                mime="text/plain"
            )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem 0;">
        <p><strong>SiteGuard AI</strong> - CAIE Final Project</p>
        <p>Powered by YOLOv8 & Large Language Models</p>
        <p style="font-size: 0.8rem;">© 2024 Muhamad Adib bin Suid</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()