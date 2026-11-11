import time
from typing import List, Dict, Optional, Any
from .models import TransactionRecord, DecisionStatus

class TransactionLedger:
    """
    Maintains the audited ledger of all autonomous spend requests,
    quarantine holding state, and settlement outcomes.
    """

    def __init__(self):
        self._records: List[TransactionRecord] = []
        self._records_by_id: Dict[str, TransactionRecord] = {}

    def record(self, record: TransactionRecord) -> None:
        self._records.insert(0, record)
        self._records_by_id[record.transaction_id] = record

    def get_all(self, limit: int = 100) -> List[TransactionRecord]:
        return self._records[:limit]

    def get_by_id(self, transaction_id: str) -> Optional[TransactionRecord]:
        return self._records_by_id.get(transaction_id)

    def get_quarantine_queue(self) -> List[TransactionRecord]:
        return [
            r for r in self._records
            if r.evaluation.status == DecisionStatus.QUARANTINED
            and r.settlement_status == "PENDING"
        ]

    def update_status(
        self, transaction_id: str, new_status: str, audit_notes: Optional[str] = None
    ) -> Optional[TransactionRecord]:
        record = self.get_by_id(transaction_id)
        if record:
            record.settlement_status = new_status
            if audit_notes:
                record.audit_notes = audit_notes
        return record

    def get_metrics(self) -> Dict[str, Any]:
        total_volume = sum(
            r.request.amount
            for r in self._records
            if r.settlement_status in ["CAPTURED", "AUTHORIZED"]
        )
        approved_count = sum(
            1 for r in self._records if r.evaluation.status == DecisionStatus.APPROVED
        )
        quarantine_pending = len(self.get_quarantine_queue())
        rejected_count = sum(
            1 for r in self._records if r.evaluation.status == DecisionStatus.REJECTED
        )
        adversarial_blocks = sum(
            1 for r in self._records if not r.evaluation.firewall_scan.is_safe
        )

        return {
            "total_settled_volume": round(total_volume, 2),
            "approved_count": approved_count,
            "quarantine_pending": quarantine_pending,
            "rejected_count": rejected_count,
            "adversarial_blocks": adversarial_blocks,
            "total_requests": len(self._records),
        }
