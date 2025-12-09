"""
Quick test script to verify setup and model availability.
"""
import os
from pathlib import Path


def check_setup():
    """Check if setup is correct."""
    print("=" * 60)
    print("NSE Option Chain Optimizer - Setup Check")
    print("=" * 60)
    print()
    
    # Check model files
    print("Checking model files...")
    model_files = {
        "lgb_model_oversampled.txt": "LightGBM model",
        "label_encoder_oversampled.joblib": "Label encoder",
        "features_oversampled.json": "Feature list"
    }
    
    models_dir = Path("models")
    all_present = True
    
    for filename, description in model_files.items():
        filepath = models_dir / filename
        if filepath.exists():
            print(f"  ✓ {filename} ({description})")
        else:
            print(f"  ✗ {filename} ({description}) - MISSING")
            all_present = False
    
    print()
    
    # Check data directories
    print("Checking data directories...")
    data_dirs = ["data/raw", "data/processed"]
    for dir_path in data_dirs:
        path = Path(dir_path)
        if path.exists():
            file_count = len(list(path.glob("*")))
            print(f"  ✓ {dir_path} ({file_count} files)")
        else:
            print(f"  ✗ {dir_path} - MISSING (will be created automatically)")
            path.mkdir(parents=True, exist_ok=True)
    
    print()
    
    # Check Python packages
    print("Checking Python packages...")
    packages = [
        "pandas", "numpy", "requests", "lightgbm", 
        "sklearn", "streamlit", "fastapi", "plotly"
    ]
    
    lightgbm_issue = False
    for package in packages:
        try:
            if package == "sklearn":
                __import__("sklearn")
                print(f"  ✓ {package}")
            elif package == "lightgbm":
                try:
                    __import__(package)
                    print(f"  ✓ {package}")
                except (FileNotFoundError, OSError) as e:
                    print(f"  ⚠ {package} - INSTALLED BUT HAS COMPATIBILITY ISSUE")
                    print(f"    Error: {str(e)[:60]}...")
                    print(f"    Solution: Use Python 3.11 or 3.12, or install via conda")
                    lightgbm_issue = True
            else:
                __import__(package)
                print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - NOT INSTALLED")
            print(f"    Run: pip install {package}")
    
    print()
    print("=" * 60)
    
    if lightgbm_issue:
        print("⚠️  LightGBM Compatibility Issue Detected")
        print()
        print("Python 3.13 has compatibility issues with LightGBM on Windows.")
        print("Solutions:")
        print("  1. Use Python 3.11 or 3.12 (recommended)")
        print("  2. Install via conda: conda install -c conda-forge lightgbm")
        print("  3. Use WSL (Windows Subsystem for Linux)")
        print()
        print("Note: You can still use other features like data collection")
        print("      and dashboards, but predictions require LightGBM.")
        print()
    
    if all_present and not lightgbm_issue:
        print("✓ Setup looks good! You can run predictions.")
        print()
        print("Quick start:")
        print("  python src/predict_live.py NIFTY")
        print("  streamlit run src/app_inmemory.py")
    elif all_present and lightgbm_issue:
        print("⚠️  Model files present but LightGBM has issues.")
        print("   Fix LightGBM issue to run predictions.")
    else:
        print("⚠️  Some model files are missing.")
        print("   Train a model first: python src/trainer.py")
        print("   Or ensure model files are in models/ directory")
    
    print("=" * 60)


if __name__ == "__main__":
    check_setup()

