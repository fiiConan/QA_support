from typing import List
from models import AuditItem

def log_result(report: List[AuditItem], block: str, item: str, severity: str, status: bool, detail: str = ""):
    report.append(AuditItem(
        block=block,
        item=item,
        severity=severity,
        status=status,
        detail=detail
    ))