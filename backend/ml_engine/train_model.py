import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os

def train_ngo_recommender(data_dir='.', model_dir='.'):
    csv_path = os.path.join(data_dir, 'synthetic_ngos.csv')
    
    if not os.path.exists(csv_path):
        print(f"❌ Could not find {csv_path}. Run generate_data.py first.")
        return

    print("📊 Loading synthetic NGO data...")
    df = pd.read_csv(csv_path)

    features = [
        'funding_ratio',
        'avg_student_income',
        'disbursement_velocity_days',
        'application_backlog'
    ]
    target = 'impact_score'

    X = df[features]
    y = df[target]

    print(f"🔬 Splitting data (80% Train / 20% Test)...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("🤖 Initializing XGBoost Regressor (Tree Method: hist)...")
    model = xgb.XGBRegressor(
        n_estimators=150,
        learning_rate=0.08,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        tree_method='hist'
    )

    print("⚙️ Training model...")
    model.fit(X_train, y_train)

    print("✅ Testing model accuracy...")
    predictions = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    print("\n" + "="*40)
    print(f"🎯 MODEL EVALUATION RESULTS:")
    print(f"   Mean Absolute Error (MAE): {mae:.2f} points (out of 100)")
    print(f"   R² Accuracy Score:        {r2 * 100:.2f}%")
    print("="*40 + "\n")

    if r2 < 0.8:
        print("⚠️ Warning: Model accuracy is low.")
    else:
        print("🚀 Model performance is excellent!")

    # Save the model
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, 'ngo_recommender.pkl')
    joblib.dump(model, model_path)
    print(f"💾 Model permanently saved to: {model_path}")
    print("Ready to be loaded by FastAPI!")

if __name__ == "__main__":
    train_ngo_recommender()
