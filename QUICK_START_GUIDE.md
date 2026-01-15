# SiteGuard AI - Quick Start Guide

## 🚀 Getting Started in 3 Minutes

### Step 1: Launch the Application (30 seconds)

```bash
# Navigate to project directory
cd siteguardAI

# Activate virtual environment (if not already active)
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Run the application
streamlit run app/web/streamlit_app_enhanced.py
```

The application will open in your default web browser at `http://localhost:8501`

---

### Step 2: Initialize the System (1 minute)

When you first open the app, you'll see a **Welcome Screen** with a complete guide.

**Option A: Read the Welcome Guide (Recommended for first-time users)**
- Read the 4-step workflow
- Review the features overview
- Check out the pro tips
- Click **"🚀 Get Started - Initialize System Now"**

**Option B: Skip to Dashboard (For experienced users)**
- Click **"📖 Skip Welcome - Go to Dashboard"**
- In the sidebar, click **"🚀 Initialize System"**
- Wait for models to load (~30 seconds)

✅ **System Ready!** You'll see a green banner: "✅ System Ready - AI models loaded and operational"

---

### Step 3: Choose Your Analysis Mode (1 minute)

Select the tab that matches your needs:

#### 📸 Tab 1: Image Analysis
**Best for:** Quick safety checks, single photos, incident documentation

**How to use:**
1. Click the **"Browse files"** button
2. Select a JPG or PNG image
3. Click **"🔍 Analyze Image"**
4. Review detection results
5. Generate OSHA report if violations found

**Use cases:**
- Daily safety inspections
- Incident investigation
- Compliance audits
- Quick spot checks

---

#### 🎥 Tab 2: Video Analysis
**Best for:** CCTV footage review, recorded videos, batch processing

**How to use:**
1. Upload a video file (MP4/AVI/MOV/MKV)
2. Adjust **"Process every N frames"** (5-10 for faster processing)
3. Set **"Max frames to process"** (100-500 recommended)
4. Click **"🚀 Process Video"**
5. Download annotated video with detections

**Use cases:**
- CCTV footage analysis
- Incident reconstruction
- Historical compliance review
- Training material creation

---

#### 📹 Tab 3: Live Webcam
**Best for:** Real-time monitoring, live demonstrations, continuous surveillance

**⚠️ Important:** Only works with local deployment (localhost). Not compatible with Streamlit public URLs or cloud deployment.

**How to use:**
1. Select your webcam from dropdown
2. Adjust **"Target FPS"** (10-15 recommended)
3. Set **"Display Confidence"** threshold (0.5 default)
4. Click **"🎬 START WEBCAM STREAM"** (large blue button)
5. Watch live detection results

**Use cases:**
- Real-time safety monitoring
- Live demonstrations
- Entry point monitoring
- Continuous surveillance

---

#### 🔍 Tab 4: RTSP Cameras
**Best for:** Professional CCTV systems, IP cameras, enterprise monitoring

**⚠️ Important:** Only works with local deployment (localhost). Not compatible with Streamlit public URLs or cloud deployment.

**How to use:**
1. Click **"🔍 Discover ONVIF Cameras"**
2. Enter camera credentials (username/password)
3. Click **"➕ Add Camera"**
4. Select camera from list
5. Click **"🎬 START CAMERA STREAM"** (large blue button)

**Use cases:**
- Enterprise CCTV integration
- Multiple camera monitoring
- Professional security systems
- Remote site monitoring

---

#### 📊 Tab 5: Analytics Dashboard
**Best for:** Tracking trends, compliance reporting, performance monitoring

**What you'll see:**
- Total analyses performed
- Violation trends over time
- Compliance rate gauge
- Violation type distribution
- Detection performance metrics

**Use cases:**
- Monthly safety reports
- Trend analysis
- Compliance tracking
- Performance monitoring

---

## 🎯 Common Workflows

### Workflow 1: Daily Safety Inspection
1. Initialize system (once per day)
2. Go to **Tab 1: Image Analysis**
3. Upload photos from site inspection
4. Analyze each photo
5. Generate reports for violations
6. Check **Tab 5: Analytics** for daily summary

**Time:** 2-3 minutes per photo

---

### Workflow 2: CCTV Footage Review
1. Initialize system
2. Go to **Tab 2: Video Analysis**
3. Upload CCTV footage
4. Set frame skip to 10 (faster processing)
5. Process video
6. Review violation timeline
7. Download annotated video

**Time:** 5-10 minutes per video (depending on length)

---

### Workflow 3: Live Monitoring
1. Initialize system
2. Go to **Tab 3: Live Webcam** or **Tab 4: RTSP Cameras**
3. Configure camera settings
4. Start stream
5. Monitor live detections
6. Violations trigger automatic alerts (if Telegram configured)

**Time:** Continuous monitoring

---

### Workflow 4: Compliance Reporting
1. Perform analyses throughout the week (any tab)
2. Go to **Tab 5: Analytics Dashboard**
3. Review compliance rate and trends
4. Export charts for reports
5. Generate OSHA reports for violations

**Time:** 5-10 minutes for report generation

---

## ⚙️ Configuration Tips

### Sidebar Settings

#### Detection Settings
- **Confidence Threshold:** 
  - Lower (0.3-0.4): More detections, more false positives
  - Medium (0.5): Balanced (recommended)
  - Higher (0.6-0.8): Fewer detections, higher accuracy

#### Report Generation
- **LLM Provider:** Choose based on your setup
  - `ollama`: Local, free, requires Ollama installed
  - `openai`: Cloud, requires API key
  - `gemini`: Cloud, requires API key

- **Report Format:**
  - `formal`: Official OSHA-style reports
  - `technical`: Detailed technical analysis
  - `executive`: High-level summary
  - `email`: Email-friendly format

#### Site Information
- **Location/Site Name:** Appears in all reports
- **Site ID:** Optional identifier for tracking
- **Inspector ID:** Optional for accountability

---

## 💡 Pro Tips

### For Best Detection Results:
✅ Use clear, well-lit images
✅ Ensure workers are visible (not obscured)
✅ Higher resolution = better accuracy
✅ Avoid extreme angles or distances

### For Faster Video Processing:
✅ Set frame skip to 5-10 (processes every 5th-10th frame)
✅ Limit max frames to 100-500 for quick review
✅ Use lower resolution videos if possible
✅ Process during off-peak hours for large files

### For Real-Time Monitoring:
✅ Start with lower FPS (10-15) and adjust up
✅ Use confidence threshold 0.5 to reduce false alarms
✅ Position cameras for clear view of workers
✅ Ensure good lighting conditions

### For Accurate Reports:
✅ Fill in site information in sidebar
✅ Use formal report format for official documents
✅ Review and edit OSHA details before exporting
✅ Save visual evidence (photos/videos) with reports

---

## 🔧 Troubleshooting

### Issue: "System not initialized" warning
**Solution:** Click "🚀 Initialize System" in sidebar and wait for models to load

### Issue: No detections in image
**Solution:** 
- Check image quality and lighting
- Lower confidence threshold in sidebar
- Ensure workers are clearly visible
- Verify system is initialized

### Issue: Video processing is slow
**Solution:**
- Increase frame skip (process every 10th frame)
- Reduce max frames to process
- Use GPU if available (check config.yaml)
- Process smaller video segments

### Issue: Webcam not detected
**Solution:**
- Check webcam is connected and working
- Close other apps using webcam
- Try different camera index in dropdown
- Restart application

### Issue: RTSP camera won't connect
**Solution:**
- Verify camera IP address is correct
- Check username and password
- Ensure camera is on same network
- Try manual RTSP URL entry

### Issue: Report generation fails
**Solution:**
- Check LLM provider is configured
- Verify API keys (if using OpenAI/Gemini)
- Ensure Ollama is running (if using Ollama)
- Check internet connection (for cloud providers)

---

## 📞 Need Help?

### Built-in Help
- Click **"📖 Show Welcome Guide"** in sidebar anytime
- Each tab has instructions at the top
- Hover over settings for tooltips

### Documentation
- `STREAMLIT_UX_IMPROVEMENTS.md` - Detailed feature documentation
- `STREAMLIT_BEFORE_AFTER_GUIDE.md` - UI/UX improvements explained
- `README.md` - Project overview and setup

### Support
- Check logs in `logs/` directory
- Review error messages in app
- Consult project documentation

---

## 🎓 Learning Path

### Beginner (Day 1):
1. Read welcome screen
2. Initialize system
3. Try Tab 1: Image Analysis with sample images
4. Generate your first report

### Intermediate (Week 1):
1. Try Tab 2: Video Analysis with sample videos
2. Experiment with different settings
3. Review Tab 5: Analytics Dashboard
4. Configure Telegram notifications

### Advanced (Month 1):
1. Set up Tab 4: RTSP Cameras
2. Configure multiple camera monitoring
3. Integrate with existing CCTV systems
4. Automate reporting workflows

---

## ✅ Quick Reference

| Task | Tab | Time | Difficulty |
|------|-----|------|------------|
| Analyze single photo | Tab 1 | 1 min | Easy |
| Process video footage | Tab 2 | 5-10 min | Easy |
| Live webcam monitoring | Tab 3 | Setup: 2 min | Medium |
| Connect IP cameras | Tab 4 | Setup: 5 min | Advanced |
| View analytics | Tab 5 | 2 min | Easy |
| Generate OSHA report | Any tab | 1 min | Easy |

---

## 🚀 You're Ready!

You now have everything you need to start using SiteGuard AI effectively. Remember:

1. **Initialize first** (one-time setup)
2. **Choose the right tab** for your task
3. **Follow in-tab instructions** for guidance
4. **Review analytics** to track progress

Happy monitoring! 🦺
