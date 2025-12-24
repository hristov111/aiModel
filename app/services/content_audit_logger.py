"""Audit logging for content classification and routing decisions."""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from uuid import UUID
from pathlib import Path

from app.services.content_classifier import ClassificationResult, ContentLabel
from app.services.content_router import ModelRoute

logger = logging.getLogger(__name__)


@dataclass
class ContentAuditLog:
    """Audit log entry for content classification."""
    timestamp: str
    conversation_id: str
    user_id: str
    
    # Input
    original_text: str
    normalized_text: str
    text_length: int
    
    # Classification
    label: str
    confidence: float
    indicators: list
    layer_results: dict
    
    # Routing
    route: str
    route_locked: bool
    age_verified: bool
    
    # Action taken
    action: str  # "generate", "refuse", "age_verify"
    refusal_reason: Optional[str] = None
    
    # Metadata
    session_info: Optional[dict] = None


class ContentAuditLogger:
    """
    Logs content classification and routing decisions for audit and review.
    
    Use cases:
    - Platform reviews
    - User complaints
    - False positive/negative tuning
    - Compliance requirements
    """
    
    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize audit logger.
        
        Args:
            log_file: Path to audit log file (default: content_audit.log)
        """
        if log_file is None:
            log_file = "content_audit.log"
        
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ContentAuditLogger initialized: {self.log_file}")
    
    def log_classification(
        self,
        conversation_id: UUID,
        user_id: UUID,
        original_text: str,
        classification: ClassificationResult,
        route: ModelRoute,
        route_locked: bool,
        age_verified: bool,
        action: str,
        refusal_reason: Optional[str] = None,
        session_info: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a content classification event.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID
            original_text: Original input text
            classification: Classification result
            route: Model route chosen
            route_locked: Whether route is locked
            age_verified: Whether age is verified
            action: Action taken (generate/refuse/age_verify)
            refusal_reason: Reason for refusal (if applicable)
            session_info: Additional session information
        """
        # Create audit log entry
        audit_log = ContentAuditLog(
            timestamp=datetime.utcnow().isoformat(),
            conversation_id=str(conversation_id),
            user_id=str(user_id),
            original_text=self._truncate_text(original_text, 500),
            normalized_text=self._truncate_text(classification.normalized_text, 500),
            text_length=len(original_text),
            label=classification.label.value,
            confidence=round(classification.confidence, 3),
            indicators=classification.indicators[:10],  # Limit indicators
            layer_results=self._sanitize_layer_results(classification.layer_results),
            route=route.value,
            route_locked=route_locked,
            age_verified=age_verified,
            action=action,
            refusal_reason=refusal_reason,
            session_info=session_info or {},
        )
        
        # Write to log file
        self._write_log(audit_log)
        
        # Also log to standard logger for immediate visibility
        log_level = self._get_log_level(classification.label)
        logger.log(
            log_level,
            f"Content classified: {classification.label.value} "
            f"(confidence: {classification.confidence:.2f}, route: {route.value}, "
            f"action: {action})"
        )
    
    def _write_log(self, audit_log: ContentAuditLog) -> None:
        """Write audit log to file."""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                log_dict = asdict(audit_log)
                f.write(json.dumps(log_dict, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text for logging."""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    
    def _sanitize_layer_results(self, layer_results: Dict) -> Dict:
        """Sanitize layer results for logging."""
        # Remove potentially large data
        sanitized = {}
        for key, value in layer_results.items():
            if isinstance(value, dict):
                # Keep only summary info
                sanitized[key] = {k: v for k, v in value.items() if k != "raw_data"}
            elif isinstance(value, list):
                # Limit list length
                sanitized[key] = value[:10]
            else:
                sanitized[key] = value
        return sanitized
    
    def _get_log_level(self, label: ContentLabel) -> int:
        """Get appropriate log level for classification label."""
        if label in (ContentLabel.MINOR_RISK, ContentLabel.NONCONSENSUAL):
            return logging.WARNING
        elif label in (ContentLabel.EXPLICIT_FETISH, ContentLabel.EXPLICIT_CONSENSUAL_ADULT):
            return logging.INFO
        else:
            return logging.DEBUG
    
    def get_recent_logs(self, limit: int = 100) -> list:
        """
        Get recent audit logs.
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            List of audit log dictionaries
        """
        if not self.log_file.exists():
            return []
        
        try:
            logs = []
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            
            # Return most recent logs
            return logs[-limit:]
        except Exception as e:
            logger.error(f"Failed to read audit logs: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics from audit logs.
        
        Returns:
            Dictionary with statistics
        """
        logs = self.get_recent_logs(limit=1000)
        
        if not logs:
            return {}
        
        # Count by label
        label_counts = {}
        route_counts = {}
        action_counts = {}
        
        for log in logs:
            label = log.get("label", "unknown")
            route = log.get("route", "unknown")
            action = log.get("action", "unknown")
            
            label_counts[label] = label_counts.get(label, 0) + 1
            route_counts[route] = route_counts.get(route, 0) + 1
            action_counts[action] = action_counts.get(action, 0) + 1
        
        return {
            "total_logs": len(logs),
            "label_distribution": label_counts,
            "route_distribution": route_counts,
            "action_distribution": action_counts,
        }


# Global audit logger instance
_audit_logger: Optional[ContentAuditLogger] = None


def get_audit_logger() -> ContentAuditLogger:
    """
    Get or create global audit logger instance.
    
    Returns:
        ContentAuditLogger instance
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = ContentAuditLogger()
    return _audit_logger

