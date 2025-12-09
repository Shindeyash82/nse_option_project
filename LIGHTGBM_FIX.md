# LightGBM DLL Issue - Solutions

## Current Issue
LightGBM is installed but cannot load the DLL file (`lib_lightgbm.dll`). This is a common Windows issue.

## Solutions to Try

### Solution 1: Install Visual C++ Redistributables (Most Common Fix)
LightGBM requires Visual C++ runtime libraries:

1. Download and install **Microsoft Visual C++ Redistributable**:
   - For 64-bit: https://aka.ms/vs/17/release/vc_redist.x64.exe
   - Or search "Visual C++ Redistributable 2015-2022"

2. Restart your terminal/IDE after installation

3. Test again:
   ```bash
   python -c "import lightgbm; print('Success!')"
   ```

### Solution 2: Install via Conda (Recommended)
Conda handles DLL dependencies better:

```bash
# If you have conda installed
conda install -c conda-forge lightgbm

# Or create a new conda environment
conda create -n nse_env python=3.10
conda activate nse_env
conda install -c conda-forge lightgbm
pip install -r requirements.txt
```

### Solution 3: Use Pre-built Wheel with DLLs
Try installing from a different source:

```bash
python -m pip uninstall lightgbm -y
python -m pip install lightgbm --only-binary :all:
```

### Solution 4: Manual DLL Check
Check if DLL exists:
```bash
python -c "import lightgbm; import os; print(os.path.join(os.path.dirname(lightgbm.__file__), 'bin'))"
```

Then navigate to that folder and check if `lib_lightgbm.dll` exists.

## What Works Without LightGBM

Even without LightGBM working, you can:

1. **Fetch Data**: `python test_fetch_data.py NIFTY` ✅
2. **View Historical Data**: `streamlit run src/app.py` ✅
3. **Collect Data**: `python src/collector.py --once` ✅

## Testing After Fix

Once LightGBM is fixed, test with:
```bash
python -c "import lightgbm; print('LightGBM version:', lightgbm.__version__)"
python src/predict_live_safe.py NIFTY
```


