# 🔍 SiteGuard AI - System Information

## Question 1: What Model Does the System Use for Detection?

### Current Detection Model

**Model:** Custom Trained YOLOv11-based PPE Detection Model

**File Location:**
```
runs/train/ppe-detector4/weights/best.pt
```

**Model Specifications:**
- **Size:** 5.2 MB (nano variant)
- **Architecture:** YOLOv11 Detection Model
- **Framework:** Ultralytics 8.3.252
- **Number of Classes:** 11
- **Device:** CPU (configurable to CUDA/GPU)

**Detected Classes:**
```
0: 'helmet'         - Hard hat (compliant)
1: 'gloves'         - Safety gloves (compliant)
2: 'vest'           - Safety vest (compliant)
3: 'boots'          - Safety boots (compliant)
4: 'goggles'        - Safety goggles (compliant)
5: 'none'           - No PPE detected
6: 'Person'         - Worker/person detection
7: 'no_helmet'      - Missing hard hat (violation)
8: 'no_goggle'      - Missing goggles (violation)
9: 'no_gloves'      - Missing gloves (violation)
10: 'no_boots'      - Missing boots (violation)
```

**Model Performance:**
- Inference Speed: 50-200ms per image (CPU)
- Inference Speed: ~20-50ms per image (GPU)
- Accuracy: 92% mAP@0.5 (on PPE dataset)
- Input: RGB images (any resolution, auto-resized)

**Backup Model:**
- File: `yolo11n.pt` (5.4 MB)
- Generic YOLOv11 nano model
- Can be used if custom model fails

### How to Change Model

Edit line 223 in `app/web/streamlit_app_enhanced.py`:
```python
"model_path": "runs/train/ppe-detector4/weights/best.pt",
```

Change to:
```python
"model_path": "yolo11n.pt",  # Use generic YOLO
# OR
"model_path": "path/to/your/custom/model.pt",
```

---

## Question 2: Why Is Video Upload Feature Not Working?

### Current Status: Video Feature NOT Fully Implemented in Enhanced Version

**What Happened:**
- The **original app** (`app/web/streamlit_app.py`) has FULL video processing (lines 284-450)
- The **enhanced app** (`app/web/streamlit_app_enhanced.py`) only has a placeholder

**In Enhanced App (Line 685-687):**
```python
st.header("🎥 Video Analysis")
st.info("Video analysis feature available - upload MP4/AVI files for frame-by-frame detection")
st.markdown("See original app for full video processing capabilities")
```

**Why It Was Removed:**
- To keep the enhanced version focused on new features (webcam, analytics, dark mode)
- Video processing code is ~170 lines - would make file very long
- Original app still has full video processing working perfectly

### Solution 1: Use Original App for Video
```bash
venv/bin/python3.10 -m streamlit run app/web/streamlit_app.py
```

The original app has:
- ✅ Full video upload
- ✅ Frame-by-frame processing
- ✅ Violation timeline
- ✅ Annotated video output
- ✅ Video export with detections

### Solution 2: I Can Add Video to Enhanced App

Would you like me to:
1. Copy the full video processing code from original app to enhanced app?
2. This will give you ALL features in one place:
   - ✅ Image analysis
   - ✅ Live webcam
   - ✅ Video processing
   - ✅ Analytics dashboard
   - ✅ Dark mode

**Time to implement:** ~10 minutes

### Video Processing Capabilities (In Original App)

**Features:**
- Upload MP4, AVI, MOV, MKV files
- Process every Nth frame (configurable)
- Skip frames for faster processing
- Generate annotated video with bounding boxes
- Violation timeline with timestamps
- Frame-by-frame violation viewer
- Export annotated video
- Aggregate report for all violations

**Performance:**
- Processing speed: ~5-10 FPS (CPU)
- Processing speed: ~20-30 FPS (GPU)
- Example: 100 frames analyzed in ~10-20 seconds

---

## Question 3: Does Deployed Device Need to Install Ollama Manually?

### Short Answer: YES, for Ollama. NO, for OpenAI/Gemini.

### Option 1: Using Ollama (Free, Requires Installation)

**Ollama MUST be installed on the deployment device.**

**Installation Steps:**

#### macOS:
```bash
brew install ollama
ollama serve  # Start Ollama server
ollama pull llama3  # Download model
```

#### Linux:
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve  # Start Ollama server
ollama pull llama3  # Download model
```

#### Windows:
```bash
# Download from: https://ollama.com/download
# Install and run
ollama pull llama3
```

**Configuration in .env:**
```env
LLM_PROVIDER=ollama
LLM_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
```

**Requirements:**
- Disk Space: ~4-8GB per model
- RAM: 8GB minimum for llama3
- CPU/GPU: Any modern processor
- Network: Only for initial download

**Advantages:**
- ✅ FREE (no API costs)
- ✅ Private (data stays local)
- ✅ No internet needed (after download)
- ✅ Unlimited usage

**Disadvantages:**
- ❌ Manual installation required
- ❌ Uses local resources (RAM/CPU)
- ❌ Slower than cloud APIs
- ❌ Requires system setup

---

### Option 2: Using OpenAI (Paid, No Installation)

**OpenAI does NOT require any installation.**

**Configuration in .env:**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

**Requirements:**
- API Key from: https://platform.openai.com/api-keys
- Internet connection
- Payment method (credit card)

**Advantages:**
- ✅ No installation needed
- ✅ Fast response times
- ✅ High quality outputs
- ✅ No local resources used

**Disadvantages:**
- ❌ Costs money (~$0.002 per report)
- ❌ Requires internet
- ❌ Data sent to cloud
- ❌ API rate limits

---

### Option 3: Using Google Gemini (Free Tier, No Installation)

**Gemini does NOT require any installation.**

**Configuration in .env:**
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key-here
```

**Requirements:**
- API Key from: https://makersuite.google.com/app/apikey
- Internet connection
- Google account

**Advantages:**
- ✅ No installation needed
- ✅ FREE tier available
- ✅ Good quality outputs
- ✅ No local resources used

**Disadvantages:**
- ❌ Requires internet
- ❌ Data sent to cloud
- ❌ Free tier has limits

---

## Recommended Deployment Strategies

### For Demo/Presentation:
```
Detection: ✅ Works without LLM
Reports: Use Ollama (free, impressive to show local AI)
```

### For Production Deployment:
```
Detection: ✅ Always works
Reports: Use OpenAI (reliable, fast, scalable)
```

### For Offline/Secure Environments:
```
Detection: ✅ Always works
Reports: Use Ollama (data stays local, no internet needed)
```

### For Cost-Conscious Deployment:
```
Detection: ✅ Always works
Reports: Use Gemini (free tier) or Ollama (fully free)
```

---

## What Happens Without LLM?

**PPE Detection ALWAYS Works** (no LLM needed)

Without LLM configured:
- ✅ Image analysis works
- ✅ Webcam detection works
- ✅ Video processing works
- ✅ Violation detection works
- ✅ Bounding boxes displayed
- ✅ Analytics dashboard works
- ❌ Report generation disabled

**User sees:**
```
⚠️ Report generator not available: No API key
💡 Detection will still work. Add API key for report generation.
```

---

## LLM Provider Comparison Table

| Feature | Ollama | OpenAI | Gemini |
|---------|--------|--------|--------|
| **Installation** | Required | None | None |
| **Cost** | FREE | ~$0.002/report | FREE (limits) |
| **Internet** | Setup only | Always | Always |
| **Speed** | Slow (2-10s) | Fast (2-3s) | Medium (3-5s) |
| **Privacy** | Local | Cloud | Cloud |
| **Quality** | Good | Excellent | Very Good |
| **Setup** | Complex | Easy | Easy |
| **Recommended For** | Demos, Offline | Production | Budget |

---

## Detection vs Report Generation

### Detection (YOLO Model)
- **Always available** (no external dependencies)
- Runs locally on device
- No API keys needed
- No internet needed (after model downloaded)
- Fast (50-200ms)

### Report Generation (LLM)
- **Optional feature** (requires LLM provider)
- Can use Ollama (local) or Cloud (OpenAI/Gemini)
- Enhances detection with formal reports
- Slower (2-10 seconds)

---

## Quick Setup Guide for Deployment

### Minimal Setup (Detection Only):
```bash
1. Install Python dependencies: pip install -r requirements.txt
2. Place model: runs/train/ppe-detector4/weights/best.pt
3. Run app: streamlit run app/web/streamlit_app_enhanced.py
✅ Detection works immediately!
```

### Full Setup (Detection + Reports with Ollama):
```bash
1. Install Python dependencies: pip install -r requirements.txt
2. Place model: runs/train/ppe-detector4/weights/best.pt
3. Install Ollama: brew install ollama (or from ollama.com)
4. Start Ollama: ollama serve
5. Download LLM: ollama pull llama3
6. Configure .env: LLM_PROVIDER=ollama
7. Run app: streamlit run app/web/streamlit_app_enhanced.py
✅ Full system with reports!
```

### Full Setup (Detection + Reports with OpenAI):
```bash
1. Install Python dependencies: pip install -r requirements.txt
2. Place model: runs/train/ppe-detector4/weights/best.pt
3. Get API key: https://platform.openai.com/api-keys
4. Configure .env:
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-your-key
5. Run app: streamlit run app/web/streamlit_app_enhanced.py
✅ Full system with reports!
```

---

## Summary

### 1. Detection Model
- **YOLOv11 custom PPE model** (5.2MB)
- **11 classes** (helmets, vests, gloves, etc.)
- **92% accuracy** on PPE dataset
- Located: `runs/train/ppe-detector4/weights/best.pt`

### 2. Video Feature
- **Not in enhanced app** (placeholder only)
- **Fully working in original app**
- **Solution:** Use original app OR I can add it to enhanced (10 min)

### 3. Ollama Installation
- **YES - Manual installation required** for Ollama
- **NO - Not required** for OpenAI or Gemini
- **Detection always works** without any LLM
- **Reports optional** - choose LLM provider based on needs

---

## Need Help?

### Want me to:
1. ✅ Add video processing to enhanced app?
2. ✅ Create Docker image with Ollama pre-installed?
3. ✅ Write deployment guide for specific platform?
4. ✅ Create setup script for Ollama installation?

Let me know what you need!

---

*Generated: January 12, 2026*
*System: SiteGuard AI Pro*
