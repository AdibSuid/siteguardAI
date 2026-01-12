from ultralytics import YOLO
import torch

if __name__ == '__main__':
    # Check CUDA availability
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device: {torch.cuda.get_device_name(0)}")
        print(f"CUDA version: {torch.version.cuda}")
        device = 0  # Use first GPU
    else:
        print("WARNING: CUDA not available. Install PyTorch with CUDA support for GPU training.")
        print("Visit: https://pytorch.org/get-started/locally/")
        device = "cpu"

    # Load pretrained YOLO11n model
    model = YOLO("yolo11n.pt")

    # Train the model on Construction-PPE dataset with GPU
    model.train(
        data="construction-ppe.yaml",
        epochs=100,
        imgsz=640,
        device=device,  # Explicitly set device
        project="runs/train",
        name="ppe-detector",
        workers=0  # Set to 0 to avoid multiprocessing issues on Windows
    )