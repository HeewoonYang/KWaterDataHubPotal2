-- REQ-DHUB-005-002 개선 마이그레이션
-- collection_job: 실패 분류 + 품질 점수 컬럼
ALTER TABLE collection_job ADD COLUMN IF NOT EXISTS failure_category VARCHAR(50);
COMMENT ON COLUMN collection_job.failure_category IS '실패카테고리 (CONNECTION_ERROR/SCHEMA_MISMATCH/DATA_TYPE_ERROR/PERMISSION_DENIED/TIMEOUT/QUOTA_EXCEEDED/QUALITY_FAIL/UNKNOWN)';
ALTER TABLE collection_job ADD COLUMN IF NOT EXISTS failure_detail JSONB;
COMMENT ON COLUMN collection_job.failure_detail IS '실패상세 (분류 근거/추천조치)';
ALTER TABLE collection_job ADD COLUMN IF NOT EXISTS quality_score NUMERIC(5,2);
COMMENT ON COLUMN collection_job.quality_score IS '수집후품질점수';
ALTER TABLE collection_job ADD COLUMN IF NOT EXISTS quality_check_at TIMESTAMP;
COMMENT ON COLUMN collection_job.quality_check_at IS '품질검증일시';
CREATE INDEX IF NOT EXISTS ix_coll_job_failure_cat ON collection_job(failure_category);

-- 신규 테이블: 알람 설정
CREATE TABLE IF NOT EXISTS collection_alert_config (
    id UUID PRIMARY KEY,
    config_name VARCHAR(200) NOT NULL,
    channel_type VARCHAR(30) NOT NULL,
    webhook_url VARCHAR(1000),
    email_to VARCHAR(500),
    trigger_type VARCHAR(50) NOT NULL,
    threshold INTEGER DEFAULT 1,
    period_minutes INTEGER DEFAULT 60,
    failure_categories JSONB,
    target_source_id UUID REFERENCES collection_data_source(id) ON DELETE CASCADE,
    severity VARCHAR(20) DEFAULT 'WARNING',
    enabled BOOLEAN DEFAULT TRUE,
    last_triggered_at TIMESTAMP,
    last_triggered_status VARCHAR(30),
    last_triggered_error TEXT,
    trigger_count INTEGER DEFAULT 0,
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_by UUID,
    updated_at TIMESTAMP DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);
COMMENT ON TABLE collection_alert_config IS '수집장애 알람 설정';
CREATE INDEX IF NOT EXISTS ix_coll_alert_enabled ON collection_alert_config(enabled);
CREATE INDEX IF NOT EXISTS ix_coll_alert_trigger ON collection_alert_config(trigger_type);
CREATE INDEX IF NOT EXISTS ix_coll_alert_not_deleted ON collection_alert_config(is_deleted) WHERE is_deleted = FALSE;
