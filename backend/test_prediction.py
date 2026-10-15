
from pathlib import Path
import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
MODEL_FILE = BASE_DIR / "models" / "crop_recommender.pkl"

# Load the trained model and its expected feature order
saved = joblib.load(MODEL_FILE)
model = saved["model"]
features = saved["features"]

# Illustrative input values, not a real farm measurement
sample_farm = {
    "n": 90,
    "p": 42,
    "k": 43,
    "temperature": 25.5,
    "humidity": 80.0,
    "ph": 6.5,
    "rainfall": 200.0,
}

input_data = pd.DataFrame(
    [[sample_farm[feature] for feature in features]],
    columns=features,
)

prediction = model.predict(input_data)[0]
probabilities = model.predict_proba(input_data)[0]
top_indices = probabilities.argsort()[::-1][:3]

print("\n--- Endura Crop Prediction Test ---")
print("Predicted crop:", prediction)
print("\nTop 3 model predictions:")

for index in top_indices:
    crop = model.classes_[index]
    confidence = probabilities[index] * 100
    print(f"{crop.title()}: {confidence:.2f}%")
