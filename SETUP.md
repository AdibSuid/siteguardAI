# 🚀 Quick Setup Guide

Get SiteGuard AI running in 5 minutes!

## Prerequisites Checklist

- [ ] Python 3.8 or higher installed
- [ ] pip package manager
- [ ] Git (for cloning)
- [ ] OpenAI API key OR Google Gemini API key
- [ ] (Optional) CUDA-capable GPU for faster processing

## Step-by-Step Setup

### 1️⃣ Clone and Navigate

```bash
git clone https://github.com/AdibSuid/siteguardAI.git
cd siteguardAI
```

### 2️⃣ Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- YOLOv8 (ultralytics)
- FastAPI & Uvicorn
- Streamlit
- OpenAI & Google Generative AI
- OpenCV, NumPy, Pillow
- Loguru, python-dotenv
- And more...

### 4️⃣ Setup Environment

```bash
# Run setup script
python scripts/setup_env.py
```

This creates:
- `data/uploads/` - For image uploads
- `data/outputs/` - For detection results
- `models/` - For YOLO models
- `logs/` - For application logs

### 5️⃣ Configure API Keys

```bash
# Copy environment template
cp .env.example .env  # On Windows: copy .env.example .env

# Edit .env file and add your API key
# Use Notepad, VS Code, or any text editor
```

Add ONE of these API keys:
```bash
OPENAI_API_KEY=sk-your-openai-key-here
# OR
GEMINI_API_KEY=your-gemini-key-here
```

**Get API Keys:**
- OpenAI: https://platform.openai.com/api-keys
- Google Gemini: https://makersuite.google.com/app/apikey

### 5️⃣ Setup Telegram Notifications (Optional but Recommended)

```bash
# Run interactive Telegram setup
python scripts/setup_telegram.py
```

This will:
- Guide you through creating a Telegram bot
- Set up a notification channel
- Configure `config.yaml` automatically
- Test the bot connection

**Manual Setup:**
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow instructions
3. Create a channel and add bot as admin
4. Edit `config.yaml`:
   ```yaml
   telegram:
     bot_token: "your_bot_token_here"
     channel_id: "@your_channel"
     enabled: true
   ```

### 6️⃣ Download YOLO Model

```bash
python scripts/download_model.py
```

This downloads the YOLOv8 model to `models/` directory.

### 7️⃣ Run Tests (Optional but Recommended)

```bash
pytest tests/ -v
```

Verify everything works correctly.

### 8️⃣ Launch Application

Choose ONE option:

**Option A: Web Dashboard (Recommended for Demo)**
```bash
python scripts/run_web.py
```
Opens at: http://localhost:8501

**Option B: API Server (For Development)**
```bash
python scripts/run_api.py
```
API docs at: http://localhost:8000/docs

**Option C: Docker (For Production)**
```bash
docker-compose up -d
```

## 🎯 Quick Test

### Using Web Dashboard:
1. Open http://localhost:8501
2. Click "Initialize System" in sidebar
3. Upload a test image (construction site photo)
4. Click "Analyze Image"
5. View detection results and generated report

### Using API:
```bash
# Health check
curl http://localhost:8000/api/v1/health

# View API documentation
# Open http://localhost:8000/docs in browser
```

## 📂 Project Structure Overview

```
siteguardAI/
├── app/              # Main application
│   ├── core/         # Detection & reporting
│   ├── api/          # REST API
│   └── web/          # Web interface
├── tests/            # Test suite
├── scripts/          # Utility scripts
├── utils/            # Helper functions
├── docs/             # Documentation
├── data/             # Data storage
└── models/           # YOLO models
```

## 🔧 Configuration

### Basic Settings (config.yaml)
```yaml
detector:
  confidence_threshold: 0.5
  device: "cpu"  # Change to "cuda" for GPU

llm:
  provider: "openai"  # or "gemini"
  temperature: 0.3
```

### Environment Variables (.env)
```bash
OPENAI_API_KEY=your_key
CONFIDENCE_THRESHOLD=0.5
LOG_LEVEL=INFO
```

## 🐛 Troubleshooting

### "Module not found" errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### "Model not found" errors
```bash
# Download model again
python scripts/download_model.py
```

### "API key not valid" errors
- Check your `.env` file
- Verify API key is correct
- Ensure no extra spaces or quotes

### Import errors
```bash
# Make sure you're in the project root
cd siteguardAI

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### Port already in use
```bash
# For web dashboard (change port)
streamlit run app/web/streamlit_app.py --server.port=8502

# For API (change port in scripts/run_api.py)
# Edit: port=8001
```

## 📚 Next Steps

1. **Read Documentation**
   - `START_HERE.md` - Overview
   - `docs/SETUP_FOR_DEMO.md` - Demo setup
   - `docs/QUICKSTART.md` - Developer guide

2. **Customize Configuration**
   - Edit `config.yaml`
   - Modify `.env` variables
   - Adjust detection thresholds

3. **Add Custom Models**
   - Train custom YOLOv8 model
   - Place in `models/` directory
   - Update `config.yaml`

4. **Extend Functionality**
   - Add new PPE classes
   - Custom report templates
   - Additional endpoints

## 🆘 Getting Help

- **Documentation**: Check `docs/` folder
- **Issues**: Open GitHub issue
- **Structure**: See `STRUCTURE.md`
- **Changes**: Review `CHANGELOG.md`

## ✅ Verification Checklist

After setup, verify:

- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip list`)
- [ ] `.env` file created with API key
- [ ] YOLO model downloaded (`models/yolov8n.pt`)
- [ ] Tests pass (`pytest tests/`)
- [ ] Web dashboard loads (http://localhost:8501)
- [ ] Can upload and analyze image
- [ ] Report generates successfully

## 🎉 Success!

You're ready to use SiteGuard AI!

**Quick Commands:**
```bash
# Start web dashboard
python scripts/run_web.py

# Start API server
python scripts/run_api.py

# Run tests
pytest tests/ -v

# Setup environment
python scripts/setup_env.py
```

---

**Need more help?** See `START_HERE.md` or `docs/SETUP_FOR_DEMO.md`
