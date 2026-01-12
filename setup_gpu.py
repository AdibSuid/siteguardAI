"""
Setup GPU support for PyTorch training
Reinstalls PyTorch with CUDA support for NVIDIA GPUs
"""

import subprocess
import sys

def run_command(cmd, description):
    """Run a command and print output."""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=False,
        text=True
    )
    
    if result.returncode != 0:
        print(f"\n❌ Failed: {description}")
        return False
    else:
        print(f"\n✅ Success: {description}")
        return True

def main():
    print("=" * 60)
    print("🚀 GPU Setup for YOLO Training")
    print("=" * 60)
    print("\n📋 System Info:")
    print("   GPU: NVIDIA GeForce RTX 3070")
    print("   CUDA Version: 12.5")
    print("   Target: PyTorch with CUDA 12.1 support")
    print()
    
    # Uninstall CPU version
    if not run_command(
        "pip uninstall -y torch torchvision torchaudio",
        "Uninstalling PyTorch CPU version"
    ):
        print("\n⚠️  Warning: Uninstall had issues, continuing anyway...")
    
    # Install CUDA version
    # Using cu121 (CUDA 12.1) which is compatible with CUDA 12.5
    if not run_command(
        "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121",
        "Installing PyTorch with CUDA 12.1 support"
    ):
        print("\n❌ Installation failed!")
        sys.exit(1)
    
    # Verify installation
    print("\n" + "=" * 60)
    print("🔍 Verifying GPU Setup")
    print("=" * 60)
    
    try:
        import torch
        print(f"\n✅ PyTorch version: {torch.__version__}")
        print(f"✅ CUDA available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"✅ CUDA version: {torch.version.cuda}")
            print(f"✅ cuDNN version: {torch.backends.cudnn.version()}")
            print(f"✅ GPU device: {torch.cuda.get_device_name(0)}")
            print(f"✅ GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
            
            # Test GPU
            print("\n🧪 Testing GPU computation...")
            x = torch.rand(1000, 1000).cuda()
            y = torch.rand(1000, 1000).cuda()
            z = x @ y
            print(f"✅ GPU computation successful!")
            
            print("\n" + "=" * 60)
            print("✅ GPU SETUP COMPLETE!")
            print("=" * 60)
            print("\n🎯 Next steps:")
            print("   1. Run: python train_model.py")
            print("   2. Training will now use GPU (much faster!)")
            print("   3. Monitor with: nvidia-smi")
        else:
            print("\n❌ CUDA is not available!")
            print("   PyTorch installed but can't detect GPU")
            print("   Check NVIDIA drivers and CUDA installation")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
