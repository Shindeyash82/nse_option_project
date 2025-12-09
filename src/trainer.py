"""
Script to train LightGBM model on aggregated snapshots.
Run after collecting data with collector.py.
"""
import pandas as pd
import numpy as np
import lightgbm as lgb
import joblib
import json
import os
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE
from typing import Optional, Tuple


def load_aggregated_data(data_dir: str = "data/processed") -> Optional[pd.DataFrame]:
    """
    Load aggregated snapshot data from processed directory.
    
    Args:
        data_dir: Directory containing processed data files
        
    Returns:
        DataFrame with features and target, or None if no data found
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"Data directory {data_dir} does not exist")
        return None
    
    # Look for parquet or CSV files
    parquet_files = list(data_path.glob("*.parquet"))
    csv_files = list(data_path.glob("*.csv"))
    
    if not parquet_files and not csv_files:
        print(f"No data files found in {data_dir}")
        return None
    
    # Load parquet files if available, otherwise CSV
    files = parquet_files if parquet_files else csv_files
    dfs = []
    
    for file in files:
        try:
            if file.suffix == '.parquet':
                df = pd.read_parquet(file)
            else:
                df = pd.read_csv(file)
            dfs.append(df)
        except Exception as e:
            print(f"Error loading {file}: {e}")
    
    if not dfs:
        return None
    
    data = pd.concat(dfs, ignore_index=True)
    print(f"Loaded {len(data)} rows from {len(files)} files")
    return data


def prepare_features_and_target(data: pd.DataFrame, target_col: str = "target") -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepare features and target from data.
    
    Args:
        data: Input DataFrame
        target_col: Name of target column
        
    Returns:
        Tuple of (features DataFrame, target Series)
    """
    if target_col not in data.columns:
        raise ValueError(f"Target column '{target_col}' not found in data")
    
    # Select feature columns (exclude target and metadata columns)
    exclude_cols = [target_col, 'timestamp', 'date', 'time']
    feature_cols = [col for col in data.columns if col not in exclude_cols]
    
    X = data[feature_cols].copy()
    y = data[target_col].copy()
    
    # Handle missing values
    X = X.fillna(0)
    
    return X, y


def train_model(
    X: pd.DataFrame,
    y: pd.Series,
    use_oversampling: bool = True,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[lgb.Booster, LabelEncoder, dict]:
    """
    Train LightGBM model.
    
    Args:
        X: Feature DataFrame
        y: Target Series
        use_oversampling: Whether to use SMOTE oversampling
        test_size: Test set size fraction
        random_state: Random seed
        
    Returns:
        Tuple of (trained model, label encoder, feature list)
    """
    # Encode target labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=test_size, random_state=random_state, stratify=y_encoded
    )
    
    # Oversampling if requested
    if use_oversampling:
        print("Applying SMOTE oversampling...")
        smote = SMOTE(random_state=random_state)
        X_train, y_train = smote.fit_resample(X_train, y_train)
        print(f"After oversampling: {len(X_train)} samples")
    
    # Prepare LightGBM dataset
    train_data = lgb.Dataset(X_train, label=y_train)
    test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
    
    # Model parameters
    params = {
        'objective': 'multiclass',
        'num_class': len(label_encoder.classes_),
        'metric': 'multi_logloss',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': 0
    }
    
    # Train model
    print("Training LightGBM model...")
    model = lgb.train(
        params,
        train_data,
        valid_sets=[train_data, test_data],
        valid_names=['train', 'eval'],
        num_boost_round=1000,
        callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(period=100)]
    )
    
    # Evaluate
    y_pred = model.predict(X_test)
    y_pred_class = np.argmax(y_pred, axis=1)
    accuracy = np.mean(y_pred_class == y_test)
    print(f"Test accuracy: {accuracy:.4f}")
    
    # Feature list
    features = list(X.columns)
    
    return model, label_encoder, features


def save_model(
    model: lgb.Booster,
    label_encoder: LabelEncoder,
    features: list,
    model_dir: str = "models",
    suffix: str = "oversampled"
):
    """
    Save trained model and artifacts.
    
    Args:
        model: Trained LightGBM model
        label_encoder: Fitted label encoder
        features: List of feature names
        model_dir: Directory to save models
        suffix: Suffix for filenames
    """
    model_path = Path(model_dir)
    model_path.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_file = model_path / f"lgb_model_{suffix}.txt"
    model.save_model(str(model_file))
    print(f"Saved model to {model_file}")
    
    # Save label encoder
    encoder_file = model_path / f"label_encoder_{suffix}.joblib"
    joblib.dump(label_encoder, encoder_file)
    print(f"Saved label encoder to {encoder_file}")
    
    # Save features
    features_file = model_path / f"features_{suffix}.json"
    with open(features_file, 'w') as f:
        json.dump(features, f, indent=2)
    print(f"Saved features to {features_file}")


def main():
    """Main training pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Train LightGBM model on aggregated snapshots")
    parser.add_argument("--data-dir", default="data/processed", help="Directory with processed data")
    parser.add_argument("--model-dir", default="models", help="Directory to save models")
    parser.add_argument("--target-col", default="target", help="Target column name")
    parser.add_argument("--no-oversampling", action="store_true", help="Disable SMOTE oversampling")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test set size fraction")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    # Load data
    print("Loading aggregated data...")
    data = load_aggregated_data(args.data_dir)
    if data is None:
        print("Failed to load data. Exiting.")
        return
    
    # Prepare features and target
    print("Preparing features and target...")
    X, y = prepare_features_and_target(data, args.target_col)
    print(f"Features: {len(X.columns)}, Samples: {len(X)}")
    print(f"Target distribution:\n{y.value_counts()}")
    
    # Train model
    model, label_encoder, features = train_model(
        X, y,
        use_oversampling=not args.no_oversampling,
        test_size=args.test_size,
        random_state=args.random_state
    )
    
    # Save model
    suffix = "oversampled" if not args.no_oversampling else "standard"
    save_model(model, label_encoder, features, args.model_dir, suffix)
    
    print("Training complete!")


if __name__ == "__main__":
    main()



