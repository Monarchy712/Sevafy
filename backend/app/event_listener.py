"""
Sevafy Blockchain Event Listener
==================================
Background async service that subscribes to contract events in real-time.

Listens for:
  - donorPaymentEvent   → update Donation record with confirmed status
  - ngoPaymentEvent     → create FundTransferRecord, update remaining funds
  - fApprovalEvent      → update application status
  - VerificationRecorded → update student verification status

Features:
  - WebSocket-based subscription (primary)
  - Fallback to HTTP polling if WS fails
  - Auto-reconnect on disconnect
  - Idempotent DB writes (uses tx_hash as dedup key)
"""

import os
import json
import asyncio
import logging
from typing import Optional
from datetime import datetime, timezone

from web3 import Web3
from web3.middleware import geth_poa_middleware

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_WS_URL: str = os.environ.get("BLOCKCHAIN_WS_URL", "")
_RPC_URL: str = os.environ.get("BLOCKCHAIN_RPC_URL", "")
_CONTRACT_ADDRESS: str = os.environ.get("CONTRACT_ADDRESS", "")

# Polling interval when WS is unavailable (seconds)
_POLL_INTERVAL = 5
# Reconnect delay on WS failure (seconds)
_RECONNECT_DELAY = 3
_MAX_RECONNECT_DELAY = 60


def _load_abi() -> list:
    abi_path = os.path.join(os.path.dirname(__file__), "sevafy_abi.json")
    with open(abi_path, "r") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# DB update helpers (idempotent — uses tx_hash dedup)
# ---------------------------------------------------------------------------


def _handle_donor_payment_event(args: dict, tx_hash: str, db_session):
    """
    donorPaymentEvent(donationId, donorUID, ngoUID, amount)
    Update the Donation record from PENDING → CONFIRMED.
    """
    from . import models

    donation_id = args.get("donationId")
    donor_uid = args.get("donorUID")
    amount = args.get("amount")

    # Idempotency: check if we already processed this tx
    existing = db_session.query(models.Donation).filter(
        models.Donation.tx_hash == tx_hash
    ).first()
    if existing and existing.blockchain_donation_id:
        logger.debug("Skipping duplicate donorPaymentEvent tx=%s", tx_hash)
        return

    # Find the pending donation by tx_hash or by matching donor+amount
    donation = None
    if tx_hash:
        donation = db_session.query(models.Donation).filter(
            models.Donation.tx_hash == tx_hash
        ).first()

    if donation:
        donation.blockchain_donation_id = donation_id
        donation.confirmed = True
        db_session.commit()
        logger.info(
            "Donation CONFIRMED: donationId=%s tx=%s",
            donation_id, tx_hash,
        )
    else:
        logger.warning(
            "donorPaymentEvent received but no matching DB record: donationId=%s tx=%s",
            donation_id, tx_hash,
        )


def _handle_ngo_payment_event(args: dict, tx_hash: str, db_session):
    """
    ngoPaymentEvent(donationId, ngoUID, studentUID, amount)
    Create/update FundTransferRecord.
    """
    from . import models

    # Idempotency check
    existing = db_session.query(models.FundTransferRecord).filter(
        models.FundTransferRecord.tx_hash == tx_hash
    ).first()
    if existing:
        logger.debug("Skipping duplicate ngoPaymentEvent tx=%s", tx_hash)
        return

    record = models.FundTransferRecord(
        blockchain_donation_id=args.get("donationId"),
        ngo_blockchain_uid=args.get("ngoUID"),
        student_blockchain_uid=args.get("studentUID"),
        amount=args.get("amount"),
        tx_hash=tx_hash,
        confirmed=True,
        confirmed_at=datetime.now(timezone.utc),
    )
    db_session.add(record)
    db_session.commit()
    logger.info(
        "FundTransfer RECORDED: donationId=%s student=%s tx=%s",
        args.get("donationId"), args.get("studentUID"), tx_hash,
    )


def _handle_approval_event(args: dict, tx_hash: str, db_session):
    """
    fApprovalEvent(donationId, ngoUID, studentUID, amount)
    Log the approval.
    """
    logger.info(
        "Fund approval event: donationId=%s ngo=%s student=%s amount=%s tx=%s",
        args.get("donationId"), args.get("ngoUID"),
        args.get("studentUID"), args.get("amount"), tx_hash,
    )


def _handle_verification_event(args: dict, tx_hash: str, db_session):
    """
    VerificationRecorded(studentUID, verificationType, status, timestamp)
    Update student verification status in DB.
    """
    from . import models

    student_uid = args.get("studentUID")
    status = args.get("status")
    v_type = args.get("verificationType")

    logger.info(
        "Verification event: student=%s type=%s status=%s tx=%s",
        student_uid, v_type, status, tx_hash,
    )


# ---------------------------------------------------------------------------
# Event processor (shared between WS and polling modes)
# ---------------------------------------------------------------------------

_EVENT_HANDLERS = {
    "donorPaymentEvent": _handle_donor_payment_event,
    "ngoPaymentEvent": _handle_ngo_payment_event,
    "fApprovalEvent": _handle_approval_event,
    "VerificationRecorded": _handle_verification_event,
}


async def _process_event(event_name: str, args: dict, tx_hash: str, db_session, ws_mgr):
    """Process a single event: update DB + broadcast via WebSocket."""
    handler = _EVENT_HANDLERS.get(event_name)
    if handler:
        handler(args, tx_hash, db_session)

    # Broadcast to WebSocket clients
    if ws_mgr:
        broadcast_data = {
            "event": event_name,
            "tx_hash": tx_hash,
            **{k: v for k, v in args.items()},
        }
        await ws_mgr.broadcast_to_all_ledger({
            "type": "blockchain_event",
            "data": broadcast_data,
        })


# ---------------------------------------------------------------------------
# Polling-based listener (fallback)
# ---------------------------------------------------------------------------


async def _run_polling_listener(db_session_factory, ws_mgr):
    """
    Fallback: poll for new events using eth_getLogs.
    Tracks last processed block to avoid reprocessing.
    """
    if not _RPC_URL:
        logger.error("BLOCKCHAIN_RPC_URL not set — event listener cannot start")
        return

    w3 = Web3(Web3.HTTPProvider(_RPC_URL))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if not w3.is_connected():
        logger.error("Cannot connect to RPC for polling: %s", _RPC_URL)
        return

    abi = _load_abi()
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(_CONTRACT_ADDRESS),
        abi=abi,
    )

    last_block = w3.eth.block_number
    logger.info("Event polling started from block %d", last_block)

    while True:
        try:
            current_block = w3.eth.block_number
            if current_block > last_block:
                for event_name in _EVENT_HANDLERS.keys():
                    event_filter_fn = getattr(contract.events, event_name, None)
                    if event_filter_fn is None:
                        continue

                    logs = event_filter_fn().get_logs(
                        fromBlock=last_block + 1,
                        toBlock=current_block,
                    )

                    for log in logs:
                        tx_hash = log.transactionHash.hex()
                        args = dict(log.args)
                        db = db_session_factory()
                        try:
                            await _process_event(
                                event_name, args, tx_hash, db, ws_mgr
                            )
                        finally:
                            db.close()

                last_block = current_block

        except Exception as e:
            logger.error("Polling error: %s", e, exc_info=True)

        await asyncio.sleep(_POLL_INTERVAL)


# ---------------------------------------------------------------------------
# WebSocket-based listener (primary)
# ---------------------------------------------------------------------------


async def _run_ws_listener(db_session_factory, ws_mgr):
    """
    Primary: subscribe to events via WebSocket RPC.
    Auto-reconnects on failure with exponential backoff.
    Falls back to polling if WS is unavailable.
    """
    if not _WS_URL:
        logger.warning("BLOCKCHAIN_WS_URL not set — falling back to polling")
        await _run_polling_listener(db_session_factory, ws_mgr)
        return

    reconnect_delay = _RECONNECT_DELAY

    while True:
        try:
            from web3 import AsyncWeb3
            from web3.providers import WebsocketProvider

            w3 = AsyncWeb3(WebsocketProvider(_WS_URL))

            abi = _load_abi()
            contract = w3.eth.contract(
                address=Web3.to_checksum_address(_CONTRACT_ADDRESS),
                abi=abi,
            )

            logger.info("WS event listener connected to %s", _WS_URL)
            reconnect_delay = _RECONNECT_DELAY  # Reset on success

            # Subscribe to all events by creating log filters
            # For each event, create an async subscription
            event_names = list(_EVENT_HANDLERS.keys())
            filters = {}

            for name in event_names:
                event_obj = getattr(contract.events, name, None)
                if event_obj:
                    # Handle both sync and async create_filter
                    res = event_obj().create_filter(fromBlock="latest")
                    if asyncio.iscoroutine(res):
                        f = await res
                    else:
                        f = res
                    filters[name] = f

            # Poll the filters in a loop
            while True:
                for name, f in filters.items():
                    try:
                        # Handle both sync and async get_new_entries
                        res = f.get_new_entries()
                        if asyncio.iscoroutine(res):
                            entries = await res
                        else:
                            entries = res
                        for entry in entries:
                            tx_hash = entry.transactionHash.hex()
                            args = dict(entry.args)
                            db = db_session_factory()
                            try:
                                await _process_event(
                                    name, args, tx_hash, db, ws_mgr
                                )
                            finally:
                                db.close()
                    except Exception as e:
                        logger.error("Filter poll error for %s: %s", name, e)
                        raise  # Trigger reconnect

                await asyncio.sleep(2)

        except Exception as e:
            logger.error(
                "WS listener error (reconnecting in %ds): %s",
                reconnect_delay, e,
            )
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, _MAX_RECONNECT_DELAY)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def start_event_listener(db_session_factory, ws_mgr):
    """
    Start the event listener.
    For stability in v6.11.4, we primarily use the polling listener.
    """
    logger.info("Starting Sevafy event listener (Polling mode)...")
    try:
        await _run_polling_listener(db_session_factory, ws_mgr)
    except Exception as e:
        logger.error("Event listener failed: %s", e)
