# 📄 Report Generation Guide - SiteGuard AI

## Your Question: Where is the Generate Report Button?

**Answer:** I've now added **"📄 Generate Report"** buttons!

Previously, reports were generated **automatically**. Now you have **manual control**!

---

## 🔧 How Report Generation Works

### Before (Automatic Only):
```
1. Analyze image/video
2. If violations found → Report generated automatically
3. Scroll down to see report
```

### Now (Manual Control) ✅:
```
1. Analyze image/video/webcam
2. If violations found → See "📄 Generate Report" button
3. Click button → Report generated
4. Scroll down to see report
```

---

## 📍 Where to Find the Report Buttons

### 1. Image Analysis Tab
```
Upload image → Analyze → Violations detected
↓
"📝 Report Generation" section appears
↓
Click "📄 Generate Report" button
↓
Report appears at bottom of page
```

**Location:** Right side panel, below violation alerts

### 2. Live Webcam Tab
```
Take photo → Analyze → Violations detected
↓
Right sidebar shows report button
↓
Click "📄 Generate Report"
↓
Report appears at bottom
```

**Location:** Right sidebar, below metrics

### 3. Video Analysis Tab
```
Upload video → Analyze → Violations detected
↓
Automatic report generation (for videos)
↓
Report appears after processing
```

**Location:** Automatic for videos (no button needed)

---

## 🎯 Step-by-Step: Generate Your First Report

### Example: Image Analysis

**Step 1:** Initialize System
- Go to sidebar
- Click **"🚀 Initialize System"**
- Wait for "✅ System ready!"

**Step 2:** Configure Report Settings (Sidebar)
```
LLM Provider: ollama (or openai/gemini)
Report Format: formal
Location: "Construction Site A"
```

**Step 3:** Upload Image
- Go to **"📸 Image Analysis"** tab
- Upload construction site photo
- Click **"🔍 Analyze Image"**

**Step 4:** Generate Report
- If violations detected, you'll see:
  ```
  ⚠️ VIOLATIONS DETECTED
  1. No Helmet - Severity: HIGH
  2. No Vest - Severity: MEDIUM

  📝 Report Generation
  [📄 Generate Report] button appears here
  ```
- Click the button!

**Step 5:** View Report
- Scroll to bottom of page
- See **"📄 Generated Incident Report"** section
- Read the report
- Download as JSON or TXT

---

## ⚙️ Report Generation Requirements

### What You Need:

**Essential:**
- ✅ System initialized (click "Initialize System")
- ✅ Violations detected (no violations = no report needed)
- ✅ LLM provider configured (Ollama/OpenAI/Gemini)

**Optional:**
- Site information (location, site ID, inspector ID)
- Report format preference (formal/technical/executive/email)

---

## 🔍 Report Generation Flow

```
┌────────────────────────────────────────┐
│ 1. Analyze Image/Webcam/Video          │
└────────────────┬───────────────────────┘
                 │
                 ▼
        ┌────────────────┐
        │ Violations?    │
        └────┬───────────┘
             │
    YES ◄────┴────► NO (No report needed)
     │
     ▼
┌────────────────────────────┐
│ "📄 Generate Report" Button │
│ appears in UI              │
└────────────┬───────────────┘
             │ (Click button)
             ▼
┌─────────────────────────────┐
│ LLM Generator Configured?   │
└────┬────────────────────────┘
     │
YES ◄┴──► NO (Show error: Configure LLM)
 │
 ▼
┌──────────────────────────────┐
│ Generating report...         │
│ (2-10 seconds)               │
└────────────┬─────────────────┘
             │
             ▼
┌─────────────────────────────┐
│ Report displayed at bottom   │
│ - Report ID                  │
│ - Full text                  │
│ - Recommendations            │
│ - Download options           │
└─────────────────────────────┘
```

---

## 🎨 What the Report Looks Like

### Report Sections:

**1. Header:**
```
Report ID: abc12345
Location: Construction Site A
Violations: 3
Format: FORMAL
```

**2. Report Content:**
```
SAFETY INCIDENT REPORT

Date: January 12, 2026
Location: Construction Site A
Inspector: [Your ID]

VIOLATIONS DETECTED:
1. Worker without hard hat - OSHA 1926.100
2. Worker without safety vest - OSHA 1926.201
3. Worker without gloves - OSHA 1926.95

RISK ASSESSMENT:
High-risk violations detected requiring immediate action...

RECOMMENDATIONS:
1. Immediate suspension of work until PPE compliance achieved
2. Mandatory safety briefing for all personnel
3. Increased supervision and spot checks
4. Review of PPE distribution procedures

REGULATORY COMPLIANCE:
This incident violates OSHA standards 1926.100, 1926.201...
```

**3. Export Options:**
- 📥 Download as JSON
- 📥 Download as TXT

---

## 🐛 Troubleshooting Report Generation

### Issue: Button is Disabled/Greyed Out

**Cause:** Report generator not initialized

**Solution:**
1. Check sidebar: Is LLM Provider selected?
2. For Ollama: Is Ollama running? (`ollama serve`)
3. For OpenAI/Gemini: Is API key in `.env`?
4. Click "🚀 Initialize System" again

---

### Issue: "Report generator not initialized" Error

**Solution A - Use Ollama (Free):**
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Pull model
ollama pull llama3

# In app sidebar:
LLM Provider: ollama
```

**Solution B - Use OpenAI:**
```bash
# Edit .env file
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

---

### Issue: Report Generation Fails

**Possible Causes:**
1. **No internet** (for OpenAI/Gemini)
2. **Ollama not running** (for Ollama)
3. **API key invalid** (for OpenAI/Gemini)
4. **API rate limit** (for OpenAI/Gemini)

**Solution:**
- Check error message
- Verify LLM provider is running/accessible
- Try different provider
- Check API key validity

---

### Issue: Report is Empty or Poor Quality

**Causes:**
- No violations detected (report has nothing to report)
- LLM model too small (use llama3 or bigger)
- Temperature too high

**Solution:**
```python
# In sidebar, try:
LLM Model: llama3 (not phi3)
Report Format: formal (most detailed)
```

---

## 📊 Report Formats Explained

### Available Formats:

**1. Formal (Default)**
- Professional incident report
- OSHA standards cited
- Detailed recommendations
- Suitable for: Official documentation

**2. Technical**
- Technical details emphasized
- Violation codes
- Risk assessment
- Suitable for: Safety engineers

**3. Executive**
- High-level summary
- Key metrics
- Action items
- Suitable for: Management

**4. Email**
- Brief, email-friendly format
- Concise summary
- Quick action items
- Suitable for: Quick notifications

---

## 🎯 Report Generation Best Practices

### For Best Results:

**1. Configure Site Information:**
```
Location: "Construction Site A - Building 3"
Site ID: "CS-2024-001"
Inspector ID: "INSP-12345"
```

**2. Use Appropriate Format:**
- Official records → Formal
- Technical review → Technical
- Management → Executive
- Quick alerts → Email

**3. Ensure Good Detection:**
- Use clear images
- Multiple angles if possible
- Good lighting
- Close enough to detect PPE

---

## 📱 Report Generation in Each Tab

### Image Analysis:
- ✅ Manual button added
- Button appears when violations detected
- Generate on demand

### Live Webcam:
- ✅ Manual button added
- Button in right sidebar
- Generate after each capture

### Video Analysis:
- ⚠️ Automatic generation
- No button needed
- Generated after video processing completes

---

## 💡 Pro Tips

**1. Test Report Generation First:**
```
1. Use a test image with clear violations
2. Click "Generate Report"
3. Verify it works before your demo
```

**2. Prepare Fallback:**
```
If LLM fails during demo:
- Show pre-generated sample report
- Explain: "Report generation uses AI (Ollama/GPT-4)"
```

**3. Speed Up Generation:**
```
Ollama (slow): 5-10 seconds
OpenAI (fast): 2-3 seconds
Gemini (medium): 3-5 seconds
```

**4. Show Report Quality:**
```
Point out in demo:
- OSHA standards automatically cited
- Professional language
- Specific recommendations
- Regulatory compliance section
```

---

## 🎬 Demo Script for Reports

### In Your Presentation:

**After showing detection:**
> "The system detected 3 PPE violations. Now let me generate a formal incident report using AI..."

**Click "📄 Generate Report"**

> "The AI is analyzing the violations and generating a report that cites relevant OSHA standards..."

**Report appears (2-10 seconds later)**

> "Here's the generated report. Notice it:
> - Cites specific OSHA regulations
> - Provides risk assessment
> - Recommends corrective actions
> - Uses professional safety language
> - Can be downloaded as JSON or text for integration with existing systems"

---

## 📥 Report Export Options

### JSON Format:
```json
{
  "report_id": "abc12345-...",
  "title": "Safety Incident Report",
  "text": "SAFETY INCIDENT REPORT\n\n...",
  "violations": [...],
  "recommendations": [...],
  "metadata": {
    "location": "Construction Site A",
    "timestamp": "2026-01-12T10:30:00"
  }
}
```

**Use case:** Integration with other systems

### TXT Format:
```
Plain text version
Ready to email or print
Human-readable
```

**Use case:** Email, printing, documentation

---

## ✅ Quick Reference

### Button Locations:
| Tab | Report Button Location |
|-----|------------------------|
| Image Analysis | Right panel, after violations |
| Live Webcam | Right sidebar, below metrics |
| Video Analysis | Automatic (no button) |

### Requirements:
- ✅ System initialized
- ✅ Violations detected
- ✅ LLM provider configured

### Report Appears:
- 📍 At bottom of page
- 📍 "📄 Generated Incident Report" section
- 📍 With download buttons

---

## 🚀 Start Generating Reports Now!

**Quick Test:**
1. Run: `./run_enhanced.sh`
2. Initialize system
3. Upload test image with violations
4. Click **"📄 Generate Report"**
5. Scroll down to see report!

---

**Summary:**
- ✅ Report generation: WORKING
- ✅ Generate buttons: ADDED
- ✅ Location: After violations detected
- ✅ Requirements: LLM configured
- ✅ Format: Configurable in sidebar
- ✅ Export: JSON & TXT available

**You can now generate professional safety reports with one click!** 🎉

---

*Guide created: January 12, 2026*
*For: SiteGuard AI Enhanced Edition*
