"""수집 실패 분류 + 알람 발송 서비스 (REQ-DHUB-005-002-003).

- error_message 패턴 기반으로 failure_category 자동 분류
- collection_alert_config 의 트리거 조건 평가 → 웹훅/이메일 발송
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Optional

import httpx
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.collection import (
    CollectionAlertConfig,
    CollectionDataSource,
    CollectionDatasetConfig,
    CollectionJob,
)

logger = logging.getLogger(__name__)


# ── 실패 분류 규칙 ───────────────────────────────────────────────────
# 패턴은 위에서부터 평가, 첫 매치 채택. 새 패턴 추가 시 우선순위에 주의.
_FAILURE_PATTERNS: list[tuple[str, re.Pattern, str, str]] = [
    # (category, regex, ko_label, recommended_action)
    ("CONNECTION_ERROR", re.compile(r"connection (refused|reset|timed?\s*out|closed)|could not connect|host (unreachable|unknown)|network (is )?unreachable|no route to host", re.I),
        "원천 연결 실패", "데이터소스 호스트/포트/방화벽 점검 및 [데이터소스 연결테스트] 실행"),
    ("PERMISSION_DENIED", re.compile(r"permission denied|access denied|authentication failed|invalid (user|password|credentials)|unauthor[i|s]ed|forbidden|insufficient privil(eges|ege)|login (failed|denied)", re.I),
        "권한/인증 실패", "데이터소스 계정 자격증명·권한·키 만료 여부 확인"),
    ("TIMEOUT", re.compile(r"timeout|timed?\s*out|deadline exceeded|operation took too long", re.I),
        "타임아웃", "수집 쿼리 최적화·인덱스 점검·타임아웃 임계값 조정 검토"),
    ("QUOTA_EXCEEDED", re.compile(r"quota (exceeded|exhaust)|rate.?limit(ed)?|too many requests|429|disk (full|quota)|out of (memory|space)|no space left", re.I),
        "쿼터/자원 초과", "원천 API 쿼터 또는 디스크/메모리 자원 확인"),
    ("SCHEMA_MISMATCH", re.compile(r"column .* (does not exist|not found|missing)|table .* (does not exist|not found)|schema mismatch|undefined column|relation .* does not exist", re.I),
        "스키마 불일치", "원천 스키마 변경 가능성 — 컬럼매핑/소스쿼리 재정의 필요"),
    ("DATA_TYPE_ERROR", re.compile(r"invalid input syntax|cast (failed|error)|type mismatch|invalid (date|number|integer|format)|cannot convert|value too long for type|numeric overflow", re.I),
        "데이터타입 오류", "타입 변환 규칙 추가 또는 원천 데이터 정제 로직 보완"),
    ("QUALITY_FAIL", re.compile(r"quality (gate|check) failed|quality score below threshold|quality below", re.I),
        "품질검증 실패", "품질검증결과 확인 후 정제 규칙 또는 표준 매핑 보완"),
]


def classify_error(error_message: str | None) -> tuple[str, dict]:
    """error_message 에서 failure_category, failure_detail 추출.

    Returns
    -------
    (category, detail) : tuple
        category : str  — 분류 코드
        detail   : dict — {label, recommended_action, matched_pattern}
    """
    if not error_message:
        return "UNKNOWN", {"label": "원인 미상", "recommended_action": "수동 분석 필요"}

    for cat, pat, label, action in _FAILURE_PATTERNS:
        m = pat.search(error_message)
        if m:
            return cat, {
                "label": label,
                "recommended_action": action,
                "matched_pattern": pat.pattern,
                "matched_text": m.group(0)[:200],
            }
    return "UNKNOWN", {
        "label": "원인 미상",
        "recommended_action": "오류 메시지 수동 검토 후 분류 규칙 추가 권장",
    }


def annotate_job_failure(job: CollectionJob) -> CollectionJob:
    """CollectionJob 객체의 error_message 를 분석해 failure_category/detail 채움.

    호출자: collection_tasks 의 실패 처리 경로, 또는 수동 백필 스크립트.
    """
    if job.job_status != "FAIL":
        return job
    if job.failure_category:  # 이미 분류 완료 — 스킵
        return job
    cat, detail = classify_error(job.error_message)
    job.failure_category = cat
    job.failure_detail = detail
    return job


# ── 알람 디스패치 ─────────────────────────────────────────────────────
def evaluate_and_dispatch_alerts(db: Session) -> dict:
    """활성 알람 설정을 모두 평가하고 트리거된 항목에 대해 웹훅 발송."""
    cfgs = db.execute(
        select(CollectionAlertConfig).where(
            CollectionAlertConfig.enabled == True,  # noqa: E712
            CollectionAlertConfig.is_deleted == False,  # noqa: E712
        )
    ).scalars().all()

    sent = failed = 0
    for cfg in cfgs:
        try:
            triggered, ctx = _check_trigger(db, cfg)
            if not triggered:
                continue
            ok, err = _dispatch(cfg, ctx)
            cfg.last_triggered_at = datetime.now()
            cfg.last_triggered_status = "SENT" if ok else "FAILED"
            cfg.last_triggered_error = err
            cfg.trigger_count = (cfg.trigger_count or 0) + 1
            if ok:
                sent += 1
            else:
                failed += 1
        except Exception as e:
            logger.exception("alert dispatch failed: cfg=%s", cfg.id)
            cfg.last_triggered_status = "FAILED"
            cfg.last_triggered_error = str(e)[:500]
            failed += 1
    db.commit()
    return {"sent": sent, "failed": failed, "evaluated": len(cfgs)}


def _check_trigger(db: Session, cfg: CollectionAlertConfig) -> tuple[bool, dict]:
    """알람 트리거 조건 평가 + 컨텍스트 반환."""
    period_min = cfg.period_minutes or 60
    since = datetime.now() - timedelta(minutes=period_min)

    base_q = select(CollectionJob).where(CollectionJob.started_at >= since)
    if cfg.target_source_id:
        base_q = base_q.join(
            CollectionDatasetConfig, CollectionJob.dataset_config_id == CollectionDatasetConfig.id
        ).where(CollectionDatasetConfig.source_id == cfg.target_source_id)

    if cfg.trigger_type == "CONSECUTIVE_FAIL":
        # 최근 N개 잡이 모두 FAIL
        threshold = cfg.threshold or 1
        recent = db.execute(
            base_q.order_by(CollectionJob.started_at.desc()).limit(threshold)
        ).scalars().all()
        if len(recent) < threshold:
            return False, {}
        if all(j.job_status == "FAIL" for j in recent):
            return True, {
                "metric": f"연속 실패 {threshold}회",
                "jobs": [{"id": str(j.id), "started_at": j.started_at.isoformat() if j.started_at else None,
                            "category": j.failure_category, "error": (j.error_message or "")[:200]} for j in recent],
            }
        return False, {}

    if cfg.trigger_type == "FAILURE_RATE":
        threshold_pct = cfg.threshold or 50
        total = db.execute(select(func.count()).select_from(base_q.subquery())).scalar() or 0
        if total == 0:
            return False, {}
        fail_q = base_q.where(CollectionJob.job_status == "FAIL")
        fail = db.execute(select(func.count()).select_from(fail_q.subquery())).scalar() or 0
        rate = (fail / total) * 100
        if rate >= threshold_pct:
            return True, {"metric": f"실패율 {rate:.1f}% (임계 {threshold_pct}%)", "total": total, "fail": fail}
        return False, {}

    if cfg.trigger_type == "QUALITY_FAIL":
        threshold_score = cfg.threshold or 80
        low_q = base_q.where(
            and_(CollectionJob.quality_score.isnot(None), CollectionJob.quality_score < threshold_score)
        )
        rows = db.execute(low_q.order_by(CollectionJob.quality_check_at.desc()).limit(10)).scalars().all()
        if rows:
            return True, {
                "metric": f"품질점수 < {threshold_score} 발생 {len(rows)}건",
                "jobs": [{"id": str(j.id), "score": float(j.quality_score or 0)} for j in rows],
            }
        return False, {}

    if cfg.trigger_type == "CATEGORY_MATCH":
        cats = cfg.failure_categories or []
        if not cats:
            return False, {}
        q = base_q.where(CollectionJob.failure_category.in_(cats))
        rows = db.execute(q.order_by(CollectionJob.started_at.desc()).limit(10)).scalars().all()
        if rows:
            return True, {
                "metric": f"감시 카테고리 매치 {len(rows)}건",
                "categories": cats,
                "jobs": [{"id": str(j.id), "category": j.failure_category, "error": (j.error_message or "")[:200]} for j in rows],
            }
        return False, {}

    return False, {}


def _dispatch(cfg: CollectionAlertConfig, ctx: dict) -> tuple[bool, str | None]:
    """채널에 따라 실제 발송. SLACK/TEAMS/WEBHOOK 은 HTTP POST. EMAIL 은 stub(로그만)."""
    payload = _build_payload(cfg, ctx)

    if cfg.channel_type in ("WEBHOOK", "SLACK", "TEAMS"):
        if not cfg.webhook_url:
            return False, "webhook_url 미설정"
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(cfg.webhook_url, json=payload)
                if resp.status_code >= 400:
                    return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
            return True, None
        except Exception as e:
            return False, f"webhook error: {e}"[:500]

    if cfg.channel_type == "EMAIL":
        # SMTP 미연결 — 운영시 mailhog/ses 등으로 교체
        logger.info("[ALERT EMAIL stub] to=%s payload=%s", cfg.email_to, payload)
        return True, None

    return False, f"미지원 channel_type: {cfg.channel_type}"


def _build_payload(cfg: CollectionAlertConfig, ctx: dict) -> dict:
    """채널에 맞는 페이로드 생성."""
    title = f"[{cfg.severity}] {cfg.config_name} - {ctx.get('metric', '트리거')}"
    text_lines = [
        f"트리거: {cfg.trigger_type}",
        f"메트릭: {ctx.get('metric', '-')}",
        f"평가주기: {cfg.period_minutes}분",
        f"발생시각: {datetime.now().isoformat(timespec='seconds')}",
    ]
    if "jobs" in ctx:
        text_lines.append("관련 작업:")
        for j in ctx["jobs"][:5]:
            text_lines.append(f"  - {j}")

    base = {
        "alert_id": str(cfg.id),
        "config_name": cfg.config_name,
        "severity": cfg.severity,
        "trigger_type": cfg.trigger_type,
        "context": ctx,
    }

    if cfg.channel_type == "SLACK":
        return {"text": title, "attachments": [{"color": _slack_color(cfg.severity), "text": "\n".join(text_lines), "fields": [{"title": "Alert ID", "value": str(cfg.id), "short": True}]}]}

    if cfg.channel_type == "TEAMS":
        return {
            "@type": "MessageCard", "@context": "https://schema.org/extensions",
            "themeColor": _teams_color(cfg.severity), "summary": title, "title": title,
            "text": "<br>".join(text_lines),
        }

    # WEBHOOK / EMAIL — 일반 JSON
    return {**base, "title": title, "body": "\n".join(text_lines)}


def _slack_color(sev: str) -> str:
    return {"INFO": "#36a64f", "WARNING": "#ff9900", "ERROR": "#cc0000", "CRITICAL": "#990000"}.get(sev or "WARNING", "#cccccc")


def _teams_color(sev: str) -> str:
    return {"INFO": "00cc66", "WARNING": "ff9900", "ERROR": "cc0000", "CRITICAL": "990000"}.get(sev or "WARNING", "888888")
