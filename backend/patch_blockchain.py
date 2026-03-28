import os

file_path = "c:/Users/samya/OneDrive/Desktop/Sevafy2/Sevafy/backend/app/main.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Replace the donation creation
old_donation = """    # Amount as integer (contract uses uint) -> Keeping as float for simulation
    donation = models.Donation(
        donator_id=profile.id,
        ngo_id=ngo.id,
        amount=request.amount,
        remaining_amount=request.amount,
        confirmed=True,
        tx_hash="SIMULATED_SUCCESS",
    )
    db.add(donation)
    
    profile.has_donated = True
    profile.total_donated = float(profile.total_donated or 0) + request.amount
    ngo.net_funding = float(ngo.net_funding or 0) + request.amount

    db.commit()
    db.refresh(donation)
    db.refresh(profile)

    return schemas.DonateResponse(
        status="success",
        total_donated=float(profile.total_donated),
        donation_id=str(donation.id),
        tx_hash="SIMULATED_SUCCESS",
        confirmed=True,
    )"""

new_donation = """    # Amount as integer (contract uses uint) -> Keeping as float for simulation
    from app import blockchain
    try:
        bc_res = blockchain.call_donor_payment(
            donor_uid=current_user.blockchain_uid,
            ngo_uid=ngo.blockchain_uid,
            amount=int(request.amount)
        )
        tx_hash = bc_res.get("tx_hash", "SIMULATED_SUCCESS")
        bc_donation_id = bc_res.get("donation_id")
    except Exception as e:
        print("Blockchain Error:", e)
        raise HTTPException(status_code=500, detail=f"Blockchain transaction failed: {str(e)}")

    donation = models.Donation(
        donator_id=profile.id,
        ngo_id=ngo.id,
        amount=request.amount,
        remaining_amount=request.amount,
        confirmed=True,
        tx_hash=tx_hash,
        blockchain_donation_id=bc_donation_id
    )
    db.add(donation)
    
    profile.has_donated = True
    profile.total_donated = float(profile.total_donated or 0) + request.amount
    ngo.net_funding = float(ngo.net_funding or 0) + request.amount

    db.commit()
    db.refresh(donation)
    db.refresh(profile)

    return schemas.DonateResponse(
        status="success",
        total_donated=float(profile.total_donated),
        donation_id=str(bc_donation_id) if bc_donation_id is not None else str(donation.id),
        tx_hash=tx_hash,
        confirmed=True,
    )"""

content = content.replace(old_donation, new_donation)

# 2. Append the missing blockchain endpoints
new_endpoints = """
# ══════════════════════════════════════════════════════════
# BLOCKCHAIN NATIVE VIEWS
# ══════════════════════════════════════════════════════════

from app import blockchain

@app.get("/api/blockchain/my-transactions")
def get_my_transactions(current_user: models.User = Depends(auth.get_current_user)):
    try:
        # User roles to Client Type mapping
        client_type = current_user.role.value
        # For Donors, they dispatch funds ('D').
        op_code = "D" if client_type == "DONATOR" else "R"
        data = blockchain.get_uid_payment_data(current_user.blockchain_uid, client_type, op_code)
        
        # We need to ensure records have 'tx_type' for the frontend
        for d in data:
            d["tx_type"] = "DONOR_TO_NGO" if client_type == "DONATOR" else "NGO_TO_STUDENT"
            
        return data
    except Exception as e:
        print("Blockchain fetch error:", e)
        return []

@app.get("/api/blockchain/remaining-funds/{donation_id}")
def remaining_funds(donation_id: int):
    try:
        rem = blockchain.get_remaining_funds(donation_id)
        return {"remaining_funds": rem, "fully_used": rem == 0}
    except Exception as e:
        return {"remaining_funds": 0, "fully_used": False}

@app.get("/api/blockchain/donation/{donation_id}/students")
def get_students_for_donation(donation_id: int):
    try:
        students = blockchain.get_students_funded_by_donation(donation_id)
        return students
    except Exception as e:
        return []
"""

if "/api/blockchain/my-transactions" not in content:
    content += new_endpoints

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched main.py successfully!")
