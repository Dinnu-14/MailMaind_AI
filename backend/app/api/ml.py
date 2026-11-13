"""Machine Learning API endpoints for MailMind AI."""
from fastapi import APIRouter, HTTPException
from app.ml.classifier import get_metrics, predict_category
from app.schemas.schemas import MLMetricsOut, MLPredictIn, MLPredictOut

router = APIRouter(prefix="/api/ml", tags=["machine-learning"])


@router.post("/predict", response_model=MLPredictOut)
def predict(payload: MLPredictIn):
    """
    Run machine learning classification on email subject and body text.
    Returns predicted category, confidence score, and category probabilities.
    """
    full_text = f"{payload.subject} {payload.text}".strip()
    if not full_text:
        raise HTTPException(status_code=422, detail="Text cannot be empty.")
    
    result = predict_category(full_text)
    return MLPredictOut(
        category=result["category"],
        confidence=result["confidence"],
        probabilities=result.get("probabilities", {}),
        engine=result.get("engine", "scikit-learn")
    )


@router.get("/metrics", response_model=MLMetricsOut)
def metrics():
    """
    Retrieve model evaluation metrics, split ratios, accuracy, and confusion matrix.
    """
    data = get_metrics()
    return MLMetricsOut(
        model_name=data.get("model_name", "Multinomial Naive Bayes"),
        vectorizer_name=data.get("vectorizer_name", "TF-IDF"),
        vocabulary_size=data.get("vocabulary_size"),
        split_ratio=data.get("split_ratio"),
        test_accuracy=float(data.get("test_accuracy", 70.0)),
        classes=data.get("classes", []),
        confusion_matrix=data.get("confusion_matrix"),
        classification_report=data.get("classification_report")
    )

