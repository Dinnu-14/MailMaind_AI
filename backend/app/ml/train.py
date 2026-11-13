"""Offline model training script for MailMind AI.
Trains TF-IDF vectorizer + Multinomial Naive Bayes classifier on dataset/emails.csv.
"""
import json
import logging
from pathlib import Path
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB

from app.ml.preprocessor import clean_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mailmind.train")


def train_model(
    dataset_path: Path | str = "dataset/emails.csv",
    output_dir: Path | str = "trained_models"
):
    dataset_path = Path(dataset_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")

    logger.info(f"Loading dataset from {dataset_path}")
    df = pd.read_csv(dataset_path)
    
    # Text cleaning
    df["clean_text"] = df["email_text"].apply(clean_text)

    X = df["clean_text"]
    y = df["category"]

    # Stratified split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    logger.info("Fitting TF-IDF Vectorizer...")
    vectorizer = TfidfVectorizer(max_features=2500, ngram_range=(1, 2))
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    logger.info("Training Multinomial Naive Bayes model...")
    model = MultinomialNB(alpha=0.1)
    model.fit(X_train_vec, y_train)

    # Evaluation
    y_pred = model.predict(X_test_vec)
    acc = accuracy_score(y_test, y_pred)
    logger.info(f"Model test accuracy: {acc * 100:.2f}%")

    report = classification_report(y_test, y_pred, output_dict=True)
    cm = confusion_matrix(y_test, y_pred).tolist()

    metrics = {
        "model_name": "Multinomial Naive Bayes (MultinomialNB)",
        "vectorizer_name": "TF-IDF (Term Frequency - Inverse Document Frequency)",
        "vocabulary_size": len(vectorizer.vocabulary_),
        "split_ratio": "80% Training, 20% Held-Out Testing (Stratified)",
        "random_state": 42,
        "total_samples": len(df),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "test_accuracy": round(acc * 100, 2),
        "classes": list(model.classes_),
        "confusion_matrix": cm,
        "classification_report": report,
    }

    # Save artifacts
    model_file = output_dir / "classifier.pkl"
    vec_file = output_dir / "vectorizer.pkl"
    metrics_file = output_dir / "metrics.json"

    joblib.dump(model, model_file)
    joblib.dump(vectorizer, vec_file)
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4)

    logger.info(f"Saved artifacts to {output_dir}")
    return metrics


if __name__ == "__main__":
    train_model()

