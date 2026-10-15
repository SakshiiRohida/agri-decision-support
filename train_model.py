
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split


# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = (
    BASE_DIR / "backend" / "data" / "Crop_recommendation.csv"
)
MODEL_DIR = BASE_DIR / "backend" / "models"
MODEL_FILE = MODEL_DIR / "crop_recommender.pkl"


def main():
    # 1. Load the dataset
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found at: {DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)
    df.columns = df.columns.str.strip().str.lower()

    print("\n--- Dataset Overview ---")
    print("Dataset shape:", df.shape)
    print("\nColumns:", df.columns.tolist())
    print("\nMissing values:")
    print(df.isnull().sum())

    # 2. Validate the expected columns
    features = [
        "n",
        "p",
        "k",
        "temperature",
        "humidity",
        "ph",
        "rainfall",
    ]
    target = "label"

    missing_columns = [
        col for col in features + [target]
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing expected columns: {missing_columns}"
        )

    # 3. Prepare the data
    df = df.dropna(subset=features + [target]).copy()

    for col in features:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=features + [target])

    X = df[features]
    y = df[target].astype(str).str.strip().str.lower()

    # 4. Split into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    # 5. Train the model
    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    # 6. Evaluate on unseen test data
    predictions = model.predict(X_test)

    print("\n--- Model Evaluation ---")
    print(
        f"Test accuracy: "
        f"{accuracy_score(y_test, predictions):.4f}"
    )
    print("\nClassification report:")
    print(classification_report(y_test, predictions))

    # 7. Save the model and feature information
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        {
            "model": model,
            "features": features,
            "classes": model.classes_.tolist(),
            "dataset_rows_used": len(df),
        },
        MODEL_FILE,
    )

    print("\nModel saved successfully!")
    print("Location:", MODEL_FILE)
    print("Training rows:", len(X_train))
    print("Testing rows:", len(X_test))
    print("Crop classes:", len(model.classes_))


if __name__ == "__main__":
    main()
