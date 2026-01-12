#!/bin/bash
# Quick launch script for SiteGuard AI Enhanced Edition

echo "🦺 SiteGuard AI Pro - Enhanced Edition"
echo "======================================"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv venv"
    exit 1
fi

# Activate venv and run with Python 3.10
echo "🚀 Launching SiteGuard AI Pro..."
echo ""
echo "📝 Note: Using Python 3.10 from venv"
echo "🌐 Dashboard will open at: http://localhost:8501"
echo ""
echo "💡 Features:"
echo "   ✅ Live Webcam Detection"
echo "   ✅ Analytics Dashboard with Charts"
echo "   ✅ Dark Mode Toggle"
echo "   ✅ Enhanced UI"
echo ""

# Run with Python 3.10
venv/bin/python3.10 -m streamlit run app/web/streamlit_app_enhanced.py

# Alternative: Use regular streamlit command
# source venv/bin/activate && streamlit run app/web/streamlit_app_enhanced.py
