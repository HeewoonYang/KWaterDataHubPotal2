-- REQ-DHUB-005-005-001 외부기관 연계포인트 점검/송수신/재시도 확장 마이그레이션
-- 대상 테이블: collection_external_agency (확장), 신규 3개 테이블

-- 1) collection_external_agency 컬럼 확장 ──────────────────────────────
ALTER TABLE collection_external_agency
    ADD COLUMN IF NOT EXISTS endpoint_type VARCHAR(20) DEFAULT 'API',
    ADD COLUMN IF NOT EXISTS endpoint_config JSONB,
    ADD COLUMN IF NOT EXISTS health_check_enabled BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS health_check_interval_sec INTEGER DEFAULT 300,
    ADD COLUMN IF NOT EXISTS health_timeout_sec INTEGER DEFAULT 10,
    ADD COLUMN IF NOT EXISTS last_health_check_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS last_health_status VARCHAR(20),
    ADD COLUMN IF NOT EXISTS last_health_latency_ms INTEGER,
    ADD COLUMN IF NOT EXISTS last_health_message TEXT,
    ADD COLUMN IF NOT EXISTS consecutive_failures INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS retry_enabled BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS max_retries INTEGER DEFAULT 3,
    ADD COLUMN IF NOT EXISTS retry_interval_sec INTEGER DEFAULT 60,
    ADD COLUMN IF NOT EXISTS retry_backoff VARCHAR(20) DEFAULT 'EXPONENTIAL',
    ADD COLUMN IF NOT EXISTS failover_endpoint VARCHAR(500),
    ADD COLUMN IF NOT EXISTS failover_active BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS failover_activated_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS auth_method VARCHAR(30) DEFAULT 'NONE',
    ADD COLUMN IF NOT EXISTS auth_config JSONB,
    ADD COLUMN IF NOT EXISTS security_policy JSONB,
    ADD COLUMN IF NOT EXISTS alert_enabled BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS alert_threshold_failures INTEGER DEFAULT 3,
    ADD COLUMN IF NOT EXISTS alert_channels JSONB,
    ADD COLUMN IF NOT EXISTS alert_last_sent_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS om_service_name VARCHAR(200),
    ADD COLUMN IF NOT EXISTS om_last_sync_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS om_last_sync_status VARCHAR(20),
    ADD COLUMN IF NOT EXISTS total_tx_count BIGINT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS total_success_count BIGINT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS total_failure_count BIGINT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_success_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS last_failure_at TIMESTAMP;

COMMENT ON COLUMN collection_external_agency.endpoint_type IS '연계포인트 유형 (API/DB/MQ)';
COMMENT ON COLUMN collection_external_agency.endpoint_config IS '점검 파라미터 (DB: host/port/user/pwd_enc, MQ: brokers/topic, API: path/method)';
COMMENT ON COLUMN collection_external_agency.health_check_enabled IS '자동점검 활성화';
COMMENT ON COLUMN collection_external_agency.health_check_interval_sec IS '자동점검주기(초)';
COMMENT ON COLUMN collection_external_agency.health_timeout_sec IS '점검 타임아웃(초)';
COMMENT ON COLUMN collection_external_agency.last_health_check_at IS '최근 점검 일시';
COMMENT ON COLUMN collection_external_agency.last_health_status IS '최근 점검 결과 (HEALTHY/DEGRADED/UNHEALTHY/UNKNOWN)';
COMMENT ON COLUMN collection_external_agency.last_health_latency_ms IS '최근 응답시간(ms)';
COMMENT ON COLUMN collection_external_agency.last_health_message IS '최근 점검 메시지/오류';
COMMENT ON COLUMN collection_external_agency.consecutive_failures IS '연속 실패 횟수';
COMMENT ON COLUMN collection_external_agency.retry_enabled IS '자동 재시도 활성화';
COMMENT ON COLUMN collection_external_agency.max_retries IS '최대 재시도 횟수';
COMMENT ON COLUMN collection_external_agency.retry_interval_sec IS '재시도 간격(초)';
COMMENT ON COLUMN collection_external_agency.retry_backoff IS '재시도 백오프 전략 (FIXED/EXPONENTIAL)';
COMMENT ON COLUMN collection_external_agency.failover_endpoint IS '핫스왑 대체 엔드포인트';
COMMENT ON COLUMN collection_external_agency.failover_active IS '핫스왑 활성화 상태';
COMMENT ON COLUMN collection_external_agency.failover_activated_at IS '핫스왑 전환 일시';
COMMENT ON COLUMN collection_external_agency.auth_method IS '인증 방식 (NONE/API_KEY/BASIC/OAUTH2/MTLS)';
COMMENT ON COLUMN collection_external_agency.auth_config IS '인증 상세 (OAuth token URL, Basic user 등)';
COMMENT ON COLUMN collection_external_agency.security_policy IS '보안 정책 (TLS 필수, IP allowlist, RateLimit)';
COMMENT ON COLUMN collection_external_agency.alert_enabled IS '장애 알림 활성화';
COMMENT ON COLUMN collection_external_agency.alert_threshold_failures IS '연속실패 N회 이상 시 알림';
COMMENT ON COLUMN collection_external_agency.alert_channels IS '알림 채널 목록 (EMAIL/SMS/WEBHOOK)';
COMMENT ON COLUMN collection_external_agency.alert_last_sent_at IS '최근 알림 발송 일시';
COMMENT ON COLUMN collection_external_agency.om_service_name IS 'OpenMetadata 서비스명';
COMMENT ON COLUMN collection_external_agency.om_last_sync_at IS 'OpenMetadata 최근 동기화 일시';
COMMENT ON COLUMN collection_external_agency.om_last_sync_status IS 'OpenMetadata 동기화 상태';
COMMENT ON COLUMN collection_external_agency.total_tx_count IS '총 송수신 건수';
COMMENT ON COLUMN collection_external_agency.total_success_count IS '총 성공 건수';
COMMENT ON COLUMN collection_external_agency.total_failure_count IS '총 실패 건수';
COMMENT ON COLUMN collection_external_agency.last_success_at IS '최근 성공 일시';
COMMENT ON COLUMN collection_external_agency.last_failure_at IS '최근 실패 일시';

CREATE INDEX IF NOT EXISTS ix_collection_external_agency_not_deleted
    ON collection_external_agency(is_deleted) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS ix_collection_external_agency_status
    ON collection_external_agency(status);
CREATE INDEX IF NOT EXISTS ix_collection_external_agency_endpoint_type
    ON collection_external_agency(endpoint_type);

-- 2) 점검 이력 ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS collection_external_agency_health_log (
    id UUID PRIMARY KEY,
    agency_id UUID NOT NULL REFERENCES collection_external_agency(id) ON DELETE CASCADE,
    checked_at TIMESTAMP NOT NULL DEFAULT NOW(),
    check_type VARCHAR(20) NOT NULL,
    endpoint_type VARCHAR(20),
    status VARCHAR(20) NOT NULL,
    latency_ms INTEGER,
    http_status INTEGER,
    error_code VARCHAR(50),
    message TEXT,
    detail JSONB,
    failover_used BOOLEAN DEFAULT FALSE
);
COMMENT ON TABLE collection_external_agency_health_log IS '외부기관 연계포인트 점검 이력';
COMMENT ON COLUMN collection_external_agency_health_log.agency_id IS '기관ID';
COMMENT ON COLUMN collection_external_agency_health_log.checked_at IS '점검일시';
COMMENT ON COLUMN collection_external_agency_health_log.check_type IS '점검유형 (SCHEDULED/MANUAL/RETRY)';
COMMENT ON COLUMN collection_external_agency_health_log.endpoint_type IS '연계포인트 유형 (API/DB/MQ)';
COMMENT ON COLUMN collection_external_agency_health_log.status IS '점검결과 (HEALTHY/DEGRADED/UNHEALTHY/UNKNOWN)';
COMMENT ON COLUMN collection_external_agency_health_log.latency_ms IS '응답시간(ms)';
COMMENT ON COLUMN collection_external_agency_health_log.http_status IS 'HTTP 응답코드 (API)';
COMMENT ON COLUMN collection_external_agency_health_log.failover_used IS '핫스왑 엔드포인트 사용 여부';
CREATE INDEX IF NOT EXISTS ix_ext_agency_health_log_agency
    ON collection_external_agency_health_log(agency_id, checked_at);
CREATE INDEX IF NOT EXISTS ix_ext_agency_health_log_status
    ON collection_external_agency_health_log(status);

-- 3) 송수신 이력 ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS collection_external_agency_tx_log (
    id UUID PRIMARY KEY,
    agency_id UUID NOT NULL REFERENCES collection_external_agency(id) ON DELETE CASCADE,
    tx_direction VARCHAR(10) NOT NULL,
    tx_type VARCHAR(30),
    correlation_id VARCHAR(100),
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP,
    duration_ms INTEGER,
    record_count BIGINT DEFAULT 0,
    bytes_size BIGINT,
    status VARCHAR(20) NOT NULL,
    http_status INTEGER,
    error_code VARCHAR(50),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    payload_preview TEXT,
    metadata_ref JSONB
);
COMMENT ON TABLE collection_external_agency_tx_log IS '외부기관 연계 송수신 이력';
COMMENT ON COLUMN collection_external_agency_tx_log.tx_direction IS '방향 (SEND/RECV)';
COMMENT ON COLUMN collection_external_agency_tx_log.tx_type IS '유형 (DATA/ACK/HEARTBEAT/METADATA)';
COMMENT ON COLUMN collection_external_agency_tx_log.status IS '상태 (SUCCESS/FAIL/PARTIAL/TIMEOUT)';
COMMENT ON COLUMN collection_external_agency_tx_log.metadata_ref IS '라이프사이클/메타데이터 참조(OpenMetadata entity 등)';
CREATE INDEX IF NOT EXISTS ix_ext_agency_tx_log_agency_time
    ON collection_external_agency_tx_log(agency_id, started_at);
CREATE INDEX IF NOT EXISTS ix_ext_agency_tx_log_status
    ON collection_external_agency_tx_log(status);
CREATE INDEX IF NOT EXISTS ix_ext_agency_tx_log_direction
    ON collection_external_agency_tx_log(tx_direction);

-- 4) 재시도 큐 ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS collection_external_agency_retry_queue (
    id UUID PRIMARY KEY,
    agency_id UUID NOT NULL REFERENCES collection_external_agency(id) ON DELETE CASCADE,
    tx_log_id UUID REFERENCES collection_external_agency_tx_log(id) ON DELETE SET NULL,
    attempt INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    next_run_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'PENDING',
    last_error TEXT,
    payload JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
COMMENT ON TABLE collection_external_agency_retry_queue IS '외부기관 연계 재시도 큐';
COMMENT ON COLUMN collection_external_agency_retry_queue.status IS '상태 (PENDING/RUNNING/DONE/DEAD)';
CREATE INDEX IF NOT EXISTS ix_ext_agency_retry_queue_due
    ON collection_external_agency_retry_queue(next_run_at, status);
CREATE INDEX IF NOT EXISTS ix_ext_agency_retry_queue_agency
    ON collection_external_agency_retry_queue(agency_id);
