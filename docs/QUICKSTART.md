# SiteGuard AI - Quick Start Guide

Get up and running with SiteGuard AI in 5 minutes!

## 🚀 Quick Installation

### Option 1: Local Development (Recommended for Testing)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/siteguard-ai.git
cd siteguard-ai

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
nano .env  # Add your OPENAI_API_KEY or GEMINI_API_KEY

# 5. Download model
python scripts/download_model.py

# 6. Run the application
streamlit run app/streamlit_app.py
```

**Access**: Open http://localhost:8501 in your browser

### Option 2: Docker (Recommended for Production)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/siteguard-ai.git
cd siteguard-ai

# 2. Configure environment
cp .env.example .env
nano .env  # Add your API keys

# 3. Start with Docker Compose
docker-compose up -d

# 4. Access applications
# Streamlit Dashboard: http://localhost:8501
# API Documentation: http://localhost:8000/docs
```

### Option 3: Using Make (Easiest)

```bash
# Clone and setup everything
git clone https://github.com/yourusername/siteguard-ai.git
cd siteguard-ai
make setup

# Run Streamlit
make run-streamlit

# Or run API
make run-api
```

## 🎯 First Use

### 1. Configure API Keys

You need either OpenAI or Google Gemini API key:

**OpenAI (Recommended)**:
1. Go to https://platform.openai.com/api-keys
2. Create new API key
3. Add to `.env`: `OPENAI_API_KEY=sk-your-key-here`

**Google Gemini (Alternative)**:
1. Go to https://makersuite.google.com/app/apikey
2. Create API key
3. Add to `.env`: `GEMINI_API_KEY=your-key-here`

### 2. Test Detection

1. Open the Streamlit app
2. Click "Initialize System" in the sidebar
3. Upload a test image (construction site photo)
4. Click "Analyze Image"
5. View detection results and generated report

### 3. API Testing

```bash
# Check API health
curl http://localhost:8000/api/v1/health

# Test detection (with image file)
curl -X POST http://localhost:8000/api/v1/detect \
  -F "file=@test_image.jpg" \
  -F "confidence_threshold=0.5"
```

## 📁 Directory Structure Overview

```
siteguard-ai/
├── app/                    # Application code
│   ├── api/               # FastAPI backend
│   ├── core/              # Core business logic
│   │   ├── vision/        # YOLOv8 detection
│   │   └── llm/           # Report generation
│   ├── streamlit_app.py   # Web interface
│   └── utils/             # Utilities
├── data/                  # Data storage
│   ├── models/            # Model weights
│   ├── raw/              # Input images
│   └── processed/        # Processed outputs
├── tests/                 # Test suite
├── scripts/               # Utility scripts
├── docs/                  # Documentation
├── requirements.txt       # Dependencies
├── Dockerfile            # Docker configuration
└── docker-compose.yml    # Multi-container setup
```

## 🔧 Common Tasks

### Change Detection Model
```python
# In .env file
YOLO_MODEL_PATH=path/to/your/model.pt
```

### Adjust Confidence Threshold
```python
# In .env file
CONFIDENCE_THRESHOLD=0.6  # Range: 0.1 - 0.9
```

### Change LLM Provider
```python
# In .env file
LLM_PROVIDER=gemini  # Options: openai, gemini
```

### Run Tests
```bash
# All tests
make test

# Specific test
pytest tests/unit/test_detector.py -v
```

### Format Code
```bash
make format
```

### View Logs
```bash
# Application logs
tail -f logs/siteguard_*.log

# Docker logs
docker-compose logs -f
```

## 🐛 Troubleshooting

### Model Not Found
```bash
# Re-download model
python scripts/download_model.py
```

### API Key Error
```bash
# Verify .env file
cat .env | grep API_KEY

# Test API key
python -c "import openai; print(openai.api_key)"
```

### Port Already in Use
```bash
# Change ports in docker-compose.yml or .env
STREAMLIT_PORT=8502
API_PORT=8001
```

### Memory Issues
```bash
# Use smaller model
YOLO_MODEL_PATH=yolov8n.pt  # Nano (fastest)
# Instead of yolov8m.pt (medium) or yolov8l.pt (large)
```

## 📊 Example Workflow

### Analyze a Construction Site Image

```python
from app.core import create_detector, create_report_generator
from app.core.llm.generator import ReportMetadata
from datetime import datetime
import cv2

# 1. Initialize components
detector = create_detector({"confidence_threshold": 0.5})
reporter = create_report_generator({"provider": "openai"})

# 2. Load and detect
image = cv2.imread("construction_site.jpg")
results = detector.detect(image)

# 3. Generate report if violations found
if results.has_violations:
    metadata = ReportMetadata(
        location="Construction Site A",
        timestamp=datetime.now()
    )
    report = reporter.generate_report(results.violations, metadata)
    
    # 4. Save report
    with open("incident_report.txt", "w") as f:
        f.write(report.text)
    
    print(f"Found {len(results.violations)} violations!")
    print(f"Report saved: {report.report_id}")
else:
    print("No violations detected - site is compliant!")
```

## 🎓 Learning Resources

- **YOLOv8 Documentation**: https://docs.ultralytics.com/
- **Streamlit Docs**: https://docs.streamlit.io/
- **FastAPI Guide**: https://fastapi.tiangolo.com/
- **OpenAI API**: https://platform.openai.com/docs

## 💡 Tips

1. **Use GPU**: Set `DEVICE=cuda` in `.env` for 5-10x faster detection
2. **Batch Processing**: Use the API's batch endpoint for multiple images
3. **Caching**: Enable Redis for faster repeated queries
4. **Custom Models**: Train on your specific PPE dataset for better accuracy
5. **Monitor Usage**: Check API usage to avoid hitting limits

## 🆘 Getting Help

- **Issues**: https://github.com/yourusername/siteguard-ai/issues
- **Discussions**: https://github.com/yourusername/siteguard-ai/discussions
- **Email**: adibcom.as@gmail.com
- **Documentation**: See `docs/` folder

## 🎉 Next Steps

Once you're comfortable with the basics:

1. **Deploy to Production**: See `docs/DEPLOYMENT.md`
2. **Customize Reports**: Modify LLM prompts in `app/core/llm/generator.py`
3. **Train Custom Model**: Use Roboflow to train on your data
4. **Add Features**: Check CONTRIBUTING.md for development guide
5. **Integrate Systems**: Use the REST API to integrate with your tools

---

**Ready to enhance workplace safety?** Start analyzing now! 🦺

For detailed documentation, see the main [README.md](README.md).