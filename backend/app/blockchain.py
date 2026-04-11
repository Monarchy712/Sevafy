import os
import json
import logging
from typing import List, Dict, Any, Optional

from web3 import Web3
from web3.middleware import geth_poa_middleware

logger = logging.getLogger(__name__)

# Env variables uthao, hardcode mat karna bhai

_RPC_URL: str = os.environ.get("BLOCKCHAIN_RPC_URL", "")
_CONTRACT_ADDRESS: str = os.environ.get("CONTRACT_ADDRESS", "")
_WALLET_PRIVATE_KEY: str = os.environ.get("WALLET_PRIVATE_KEY", "")

# Singleton patterns: ek baar banao aur reuse karo

_w3: Optional[Web3] = None
_contract = None
_account = None


def _load_abi() -> list:
    abi_path = os.path.join(os.path.dirname(__file__), "sevafy_abi.json")
    with open(abi_path, "r") as f:
        return json.load(f)


def _get_web3() -> Web3:
    global _w3
    if _w3 is None:
        if not _RPC_URL:
            raise RuntimeError("BLOCKCHAIN_RPC_URL not set in environment")
        _w3 = Web3(Web3.HTTPProvider(_RPC_URL))
        # PoA middleware for networks like Polygon / BSC
        _w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        if not _w3.is_connected():
            raise ConnectionError(f"Cannot connect to blockchain RPC: {_RPC_URL}")
        logger.info("Web3 connected to %s (chain %s)", _RPC_URL, _w3.eth.chain_id)
    return _w3


def _get_contract():
    global _contract
    if _contract is None:
        w3 = _get_web3()
        if not _CONTRACT_ADDRESS:
            raise RuntimeError("CONTRACT_ADDRESS not set in environment")
        abi = _load_abi()
        _contract = w3.eth.contract(
            address=Web3.to_checksum_address(_CONTRACT_ADDRESS),
            abi=abi,
        )
        logger.info("Contract loaded at %s", _CONTRACT_ADDRESS)
    return _contract


def _get_account():
    global _account
    if _account is None:
        if not _WALLET_PRIVATE_KEY:
            raise RuntimeError("WALLET_PRIVATE_KEY not set in environment")
        w3 = _get_web3()
        _account = w3.eth.account.from_key(_WALLET_PRIVATE_KEY)
        logger.info("Wallet loaded: %s", _account.address)
    return _account




def _send_transaction(fn) -> Dict[str, Any]:
    # Transaction build, sign aur send karne ka main function
    w3 = _get_web3()
    account = _get_account()

    tx = fn.build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 500_000,
        "gasPrice": w3.eth.gas_price,
    })

    signed = w3.eth.account.sign_transaction(tx, private_key=_WALLET_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    logger.info(
        "TX %s — status=%s gasUsed=%s",
        receipt.transactionHash.hex(),
        receipt.status,
        receipt.gasUsed,
    )

    if receipt.status != 1:
        raise RuntimeError(
            f"Transaction reverted: {receipt.transactionHash.hex()}"
        )

    return receipt


def _parse_event_from_receipt(receipt, event_name: str) -> Optional[Dict]:
    """Extract the first occurrence of an event from a tx receipt."""
    contract = _get_contract()
    event = getattr(contract.events, event_name, None)
    if event is None:
        return None
    from web3.logs import DISCARD
    logs = event().process_receipt(receipt, errors=DISCARD)
    if logs:
        return dict(logs[0].args)
    return None


# Contract mein data change karne wale functions - isme gas lagegi


def call_donor_payment(donor_uid: int, ngo_uid: int, amount: int) -> Dict[str, Any]:
    contract = _get_contract()
    fn = contract.functions.donorPaymentCall(donor_uid, ngo_uid, amount)
    receipt = _send_transaction(fn)

    # Parse donorPaymentEvent to get the donationId
    event_data = _parse_event_from_receipt(receipt, "donorPaymentEvent")
    donation_id = event_data["donationId"] if event_data else None

    return {
        "tx_hash": receipt.transactionHash.hex(),
        "donation_id": donation_id,
        "receipt": receipt,
    }


def call_fund_transfer(
    donation_id: int,
    ngo_uid: int,
    student_uid: int,
    amount: int,
    purpose: int,
) -> Dict[str, Any]:
    contract = _get_contract()
    fn = contract.functions.fundTransfer(
        donation_id, ngo_uid, student_uid, amount, purpose
    )
    receipt = _send_transaction(fn)

    approval_event = _parse_event_from_receipt(receipt, "fApprovalEvent")
    payment_event = _parse_event_from_receipt(receipt, "ngoPaymentEvent")

    return {
        "tx_hash": receipt.transactionHash.hex(),
        "approval_event": approval_event,
        "payment_event": payment_event,
        "receipt": receipt,
    }


def call_record_verification(
    student_uid: int, verification_type: str, status: bool
) -> Dict[str, Any]:
    """
    Log a student verification result on-chain.
    Calls: recordVerification(studentUID, type, status)
    Returns: { tx_hash, receipt }
    """
    contract = _get_contract()
    fn = contract.functions.recordVerification(student_uid, verification_type, status)
    receipt = _send_transaction(fn)

    verification_event = _parse_event_from_receipt(receipt, "VerificationRecorded")

    return {
        "tx_hash": receipt.transactionHash.hex(),
        "verification_event": verification_event,
        "receipt": receipt,
    }


# Sirf data dekhne ke liye - gas nahi lagegi


def get_remaining_funds(donation_id: int) -> int:
    """Returns remaining usable funds for a donationId."""
    contract = _get_contract()
    return contract.functions.remainingFunds(donation_id).call()


def get_students_funded_by_donation(donation_id: int) -> List[Dict]:
    """Returns all students funded from a specific donation."""
    contract = _get_contract()
    raw = contract.functions.getStudentsFundedByDonation(donation_id).call()
    return [
        {
            "purpose": item[0],
            "donation_id": item[1],
            "sender_uid": item[2],
            "receiver_uid": item[3],
            "amount": item[4],
            "timestamp": item[5],
        }
        for item in raw
    ]


def get_uid_payment_data(
    uid: int, client_type: str, operation: str
) -> List[Dict]:
    """
    Get payment data for a UID.
    client_type: "DONOR" | "NGO" | "STUDENT"
    operation: "D" (Disbursed) | "R" (Received)
    """
    contract = _get_contract()
    raw = contract.functions.getUIDPaymentData(uid, client_type, operation).call()
    return [
        {
            "purpose": item[0],
            "donation_id": item[1],
            "sender_uid": item[2],
            "receiver_uid": item[3],
            "amount": item[4],
            "timestamp": item[5],
        }
        for item in raw
    ]


def get_last_50_transactions() -> List[Dict]:
    """
    Returns last 50 merged transactions (donor + NGO).
    Used for the Transparent Ledger.
    NOTE: This is an onlyOwner view function — must be called from owner wallet.
    """
    contract = _get_contract()
    account = _get_account()
    raw = contract.functions.last50Transactions().call({"from": account.address})
    return [
        {
            "purpose": item[0],
            "donation_id": item[1],
            "sender_uid": item[2],
            "receiver_uid": item[3],
            "amount": item[4],
            "timestamp": item[5],
        }
        for item in raw
    ]


def is_donation_fully_used(donation_id: int) -> bool:
    """Check if all funds from a donation have been disbursed."""
    contract = _get_contract()
    return contract.functions.isDonationFullyUsed(donation_id).call()


def get_donation_counter() -> int:
    """Get the current donation counter (total donations made)."""
    contract = _get_contract()
    return contract.functions.donationCounter().call()
