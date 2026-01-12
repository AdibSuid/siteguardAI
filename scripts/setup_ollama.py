"""
Quick setup script for Ollama on Windows
"""

import subprocess
import sys
import time
import requests
from pathlib import Path


def check_ollama_installed():
    """Check if Ollama is installed."""
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ Ollama is installed:", result.stdout.strip())
            return True
    except:
        pass
    return False


def check_ollama_running():
    """Check if Ollama service is running."""
    try:
        response = requests.get("http://localhost:11434", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama service is running")
            return True
    except:
        pass
    return False


def list_models():
    """List installed Ollama models."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("\n📦 Installed models:")
            print(result.stdout)
            return result.stdout
    except Exception as e:
        print(f"❌ Error listing models: {e}")
    return ""


def pull_model(model_name="llama3"):
    """Download an Ollama model."""
    print(f"\n⬇️  Downloading {model_name}...")
    print("This may take a few minutes depending on your connection...")
    
    try:
        process = subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        for line in process.stdout:
            print(line.strip())
        
        process.wait()
        
        if process.returncode == 0:
            print(f"✅ {model_name} downloaded successfully!")
            return True
        else:
            print(f"❌ Error downloading {model_name}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_model(model_name="llama3"):
    """Test the model with a simple query."""
    print(f"\n🧪 Testing {model_name}...")
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": "Write a one-sentence workplace safety tip.",
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Model response: {result.get('response', '')[:100]}...")
            return True
        else:
            print(f"❌ Error testing model: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Main setup flow."""
    print("=" * 60)
    print("🦙 Ollama Setup for SiteGuard AI")
    print("=" * 60)
    print()
    
    # Check installation
    if not check_ollama_installed():
        print("❌ Ollama is not installed!")
        print("\n📥 Download from: https://ollama.ai/download/windows")
        print("Or use: winget install Ollama.Ollama")
        print("\nAfter installation, run this script again.")
        sys.exit(1)
    
    # Check service
    if not check_ollama_running():
        print("⚠️  Ollama service is not running!")
        print("\nStarting Ollama...")
        try:
            subprocess.Popen(["ollama", "serve"], shell=True)
            time.sleep(3)
            if check_ollama_running():
                print("✅ Ollama started successfully!")
            else:
                print("❌ Could not start Ollama. Please start it manually.")
                sys.exit(1)
        except:
            print("❌ Could not start Ollama. Please start it manually.")
            sys.exit(1)
    
    # List existing models
    models_output = list_models()
    
    # Check if llama3 is installed
    if "llama3" in models_output:
        print("\n✅ llama3 is already installed!")
        choice = input("\nDownload another model? (y/N): ").lower()
        if choice != 'y':
            test_model("llama3")
            print("\n" + "=" * 60)
            print("✅ Setup complete! You can now run the app.")
            print("=" * 60)
            return
    else:
        print("\n📥 No models found. Let's download one!")
    
    # Model selection
    print("\nAvailable models:")
    print("1. llama3 (Recommended, ~4.7GB)")
    print("2. mistral (Smaller, faster, ~4.1GB)")
    print("3. phi3 (Smallest, ~2.3GB)")
    print("4. gemma2 (Google, ~5GB)")
    
    choice = input("\nSelect model (1-4) [1]: ").strip() or "1"
    
    model_map = {
        "1": "llama3",
        "2": "mistral",
        "3": "phi3",
        "4": "gemma2"
    }
    
    model = model_map.get(choice, "llama3")
    
    # Download model
    if pull_model(model):
        # Test the model
        test_model(model)
        
        print("\n" + "=" * 60)
        print("✅ Setup complete!")
        print("=" * 60)
        print(f"\n🚀 Start the app with:")
        print("   streamlit run app/web/streamlit_app.py")
        print(f"\n💡 Using model: {model}")
        print("   You can change this in the app sidebar.")
    else:
        print("\n❌ Setup failed. Please try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
