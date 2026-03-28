"""
Neon schema migration + NGO seed data.
Run once: cd backend && venv/bin/python seed_ngos.py
"""
import os
from dotenv import load_dotenv
load_dotenv()

import sqlalchemy
from sqlalchemy import text

url = os.environ["DATABASE_URL"]
engine = sqlalchemy.create_engine(url)

with engine.connect() as conn:
    print("Connecting to Neon...")

    # ── Schema migrations ──────────────────────────────
    migrations = [
        "ALTER TABLE ngos ADD COLUMN IF NOT EXISTS about TEXT;",
        "ALTER TABLE ngos ADD COLUMN IF NOT EXISTS net_funding NUMERIC(14,2) DEFAULT 0;",
        "ALTER TABLE ngos ADD COLUMN IF NOT EXISTS beneficiary TEXT[];",
        "ALTER TABLE donator_profiles ADD COLUMN IF NOT EXISTS has_donated BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE donator_profiles ADD COLUMN IF NOT EXISTS total_donated NUMERIC(14,2) DEFAULT 0;",
    ]
    for m in migrations:
        try:
            conn.execute(text(m))
            print(f"  ✓ {m[:60]}...")
        except Exception as e:
            print(f"  ✗ {e}")
    conn.commit()
    print("Schema migrations complete.\n")

    # ── Clear existing seed data (cascade through FK) ──
    conn.execute(text("TRUNCATE TABLE ngos CASCADE;"))
    conn.commit()

    # ── Seed 5 realistic Indian NGOs ───────────────────
    ngos = [
        {
            "name": "Pratham Education Foundation",
            "description": "One of India's largest non-governmental organizations, focused on children's education.",
            "about": "Pratham was founded in 1995 in Mumbai to provide pre-school education to children in the slums. Today it has grown into one of the largest non-profit organizations in India. Our mission is 'Every Child in School and Learning Well.' We believe every child deserves a quality education regardless of their socio-economic background.",
            "net_funding": 1254000.00,
            "beneficiary": "{elementary,middle-school}",
            "bank_account_number": "9876543210123456",
            "bank_ifsc_code": "HDFC0001234",
            "upi_id": "pratham@hdfcbank",
        },
        {
            "name": "Teach For India",
            "description": "Building a movement of leaders to eliminate educational inequity.",
            "about": "Teach For India is committed to building a pipeline of leaders working to ensure all children receive an excellent education. We recruit outstanding graduates and professionals as Fellows who teach in under-resourced schools for two years. Our alumni network of 4,600+ leaders continues to work across sectors towards educational equity.",
            "net_funding": 832500.00,
            "beneficiary": "{elementary,middle-school,high-school}",
            "bank_account_number": "1234567890987654",
            "bank_ifsc_code": "ICIC0006789",
            "upi_id": "tfi@icicibank",
        },
        {
            "name": "Akshaya Patra Foundation",
            "description": "The world's largest NGO-run midday meal program feeding millions daily.",
            "about": "The Akshaya Patra Foundation strives to eliminate classroom hunger by implementing the Mid-Day Meal Scheme across government schools and government-aided schools in India. We serve wholesome meals to over 2 million children every school day across 20,000+ schools. No child should be denied an education because of hunger.",
            "net_funding": 2100750.00,
            "beneficiary": "{elementary,middle-school}",
            "bank_account_number": "5678901234567890",
            "bank_ifsc_code": "SBIN0005678",
            "upi_id": "akshayapatra@sbi",
        },
        {
            "name": "Vidya Gyan",
            "description": "Providing world-class education to meritorious rural students.",
            "about": "Vidya Gyan identifies exceptionally talented children from underprivileged rural backgrounds and provides them with world-class residential education. Our scholars come from families earning less than ₹1 lakh per year, and we transform their potential into achievement. 100% of our graduates go on to top universities including IITs, NITs, and AIIMS.",
            "net_funding": 475200.00,
            "beneficiary": "{high-school,undergrad}",
            "bank_account_number": "3456789012345678",
            "bank_ifsc_code": "UTIB0003456",
            "upi_id": "vidyagyan@axisbank",
        },
        {
            "name": "Asha for Education",
            "description": "A volunteer-driven organization catalyzing socio-economic change through education.",
            "about": "Asha for Education focuses on providing education to underprivileged children in India. Operating through 60+ chapters across the world, we are entirely run by volunteers. Our unique model funds education projects across India — from primary schools in remote villages to college scholarships for first-generation learners.",
            "net_funding": 689300.00,
            "beneficiary": "{undergrad}",
            "bank_account_number": "7890123456789012",
            "bank_ifsc_code": "KKBK0007890",
            "upi_id": "asha@kotak",
        },
    ]

    for ngo in ngos:
        conn.execute(text("""
            INSERT INTO ngos (id, name, description, about, net_funding, beneficiary, 
                              bank_account_number, bank_ifsc_code, upi_id)
            VALUES (gen_random_uuid(), :name, :description, :about, :net_funding, 
                    CAST(:beneficiary AS text[]), :bank_account_number, :bank_ifsc_code, :upi_id)
        """), ngo)
        print(f"  ✓ Seeded: {ngo['name']}")

    conn.commit()
    print("\nAll 5 NGOs seeded successfully!")
