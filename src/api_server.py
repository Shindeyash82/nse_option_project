"""
FastAPI application to expose /predict endpoints.
Optional API server for option chain predictions.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
from src.fetch_predict import OptionChainPredictor

app = FastAPI(title="NSE Option Chain Predictor API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize predictor
predictor = OptionChainPredictor()


class PredictionRequest(BaseModel):
    """Request model for prediction endpoint."""
    symbol: str = "NIFTY"
    features: Optional[Dict[str, float]] = None  # Optional: provide features directly


class PredictionResponse(BaseModel):
    """Response model for prediction endpoint."""
    predicted_class: Optional[str] = None
    predicted_class_idx: int
    probabilities: list
    spot: Optional[float] = None
    timestamp: str
    features: Optional[Dict[str, float]] = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "NSE Option Chain Predictor API",
        "version": "1.0.0",
        "endpoints": {
            "/predict": "POST - Get prediction for option chain",
            "/predict/{symbol}": "GET - Quick prediction for symbol",
            "/health": "GET - Health check"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model_loaded": predictor.model is not None,
        "features_loaded": predictor.features is not None
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Predict endpoint - fetches option chain and returns prediction.
    
    Args:
        request: PredictionRequest with symbol and optional features
        
    Returns:
        PredictionResponse with prediction results
    """
    try:
        if request.features:
            # Use provided features directly
            prediction = predictor.predict(request.features)
            if prediction is None:
                raise HTTPException(status_code=500, detail="Prediction failed")
            
            return PredictionResponse(
                predicted_class=prediction.get('predicted_class'),
                predicted_class_idx=prediction.get('predicted_class_idx', 0),
                probabilities=prediction.get('probabilities', []),
                timestamp=prediction.get('timestamp', ''),
                features=request.features
            )
        else:
            # Fetch and predict
            result = predictor.fetch_and_predict(request.symbol)
            if result is None:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to fetch option chain for {request.symbol}"
                )
            
            return PredictionResponse(
                predicted_class=result.get('predicted_class'),
                predicted_class_idx=result.get('predicted_class_idx', 0),
                probabilities=result.get('probabilities', []),
                spot=result.get('spot'),
                timestamp=result.get('timestamp', ''),
                features=result.get('features')
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predict/{symbol}", response_model=PredictionResponse)
async def predict_get(symbol: str):
    """
    Quick prediction endpoint via GET request.
    
    Args:
        symbol: Option symbol (e.g., NIFTY, BANKNIFTY)
        
    Returns:
        PredictionResponse with prediction results
    """
    try:
        result = predictor.fetch_and_predict(symbol)
        if result is None:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch option chain for {symbol}"
            )
        
        return PredictionResponse(
            predicted_class=result.get('predicted_class'),
            predicted_class_idx=result.get('predicted_class_idx', 0),
            probabilities=result.get('probabilities', []),
            spot=result.get('spot'),
            timestamp=result.get('timestamp', ''),
            features=result.get('features')
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/features")
async def get_features():
    """Get list of features used by the model."""
    if predictor.features is None:
        raise HTTPException(status_code=404, detail="Features not loaded")
    
    return {
        "features": predictor.features,
        "count": len(predictor.features)
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run FastAPI server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)



