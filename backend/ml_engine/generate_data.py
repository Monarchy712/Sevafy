import pandas as pd
import numpy as np
import os
import uuid

def generate_synthetic_ngo_data(num_records=5000, output_dir='.'):
    np.random.seed(42)
    
    # Generate mock UUIDs for NGOs
    ngo_ids = [str(uuid.uuid4()) for _ in range(num_records)]
    
    # 1. Funding Fulfillment Ratio (0.0 to 1.5, representing 0% to 150% funded)
    # A low ratio means the NGO desperately needs its fair share.
    funding_ratio = np.random.beta(a=2, b=5, size=num_records) * 1.5
    
    # 2. Average Student Income (in INR, assuming between 10k and 300k a year)
    # Lower income means higher model impact priority.
    # We use a log-normal distribution to cluster around lower incomes
    avg_student_income = np.random.lognormal(mean=11.3, sigma=0.8, size=num_records)
    avg_student_income = np.clip(avg_student_income, 10000, 300000)

    # 3. Disbursement Velocity (Days)
    # Average gap between donation received and scholarship given
    # Usually between 1 day and 60 days
    disbursement_velocity_days = np.random.gamma(shape=2, scale=10, size=num_records)
    disbursement_velocity_days = np.clip(disbursement_velocity_days, 1, 90)

    # 4. Application Backlog (Urgency count)
    # Number of APPROVED but unpaid applications
    application_backlog = np.random.poisson(lam=15, size=num_records)
    
    df = pd.DataFrame({
        'ngo_id': ngo_ids,
        'funding_ratio': funding_ratio,
        'avg_student_income': avg_student_income,
        'disbursement_velocity_days': disbursement_velocity_days,
        'application_backlog': application_backlog
    })

    # 5. Synthesize a target "Impact Priority Score" (0 to 100)
    # Based on our DBML design, we prioritize:
    # High backlog (urgent), Low Funding (fair share), Low Income (vulnerable), Low Velocity (efficient)
    
    # Normalize features to 0-1 scale internally to calculate a realistic score mapping
    norm_funding = np.clip(1.0 - df['funding_ratio'], 0, 1) # Lower funding = higher score weight (0 to 1)
    
    # Reverse income normalized (poorer = higher score)
    norm_income = 1.0 - ((df['avg_student_income'] - 10000) / (300000 - 10000))
    
    # Reverse velocity normalized (faster = higher score)
    norm_velocity = 1.0 - ((df['disbursement_velocity_days'] - 1) / (90 - 1))
    
    # Backlog normalized (more backlog = higher score)
    norm_backlog = np.clip(df['application_backlog'] / 100.0, 0, 1)
    
    # Combine linearly with weights + some random noise so the ML model has to work for it
    raw_score = (
        0.35 * norm_funding + 
        0.35 * norm_income + 
        0.15 * norm_velocity + 
        0.15 * norm_backlog
    )
    
    # Add small Gaussian noise representing real-world human evaluation deviations
    noise = np.random.normal(0, 0.05, num_records)
    raw_score = np.clip(raw_score + noise, 0, 1)
    
    # Scale to 0-100 Impact Score
    df['impact_score'] = np.round(raw_score * 100, 2)
    
    # Save to CSV
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, 'synthetic_ngos.csv')
    df.to_csv(csv_path, index=False)
    print(f"✅ Generated {num_records} synthetic NGO records.")
    print(f"✅ Saved to: {csv_path}")
    print(df.head())

if __name__ == "__main__":
    generate_synthetic_ngo_data()
