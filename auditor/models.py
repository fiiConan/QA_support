from dataclasses import dataclass, asdict

@dataclass
class AuditItem:
    block: str
    item: str
    severity: str
    status: bool
    detail: str = ""

    def to_dict(self):
        return {
            "區塊": self.block,
            "檢測項目": self.item,
            "嚴重程度": self.severity,
            "狀態": "✅ 通過" if self.status else "❌ 待修復",
            "備註": self.detail,
        }