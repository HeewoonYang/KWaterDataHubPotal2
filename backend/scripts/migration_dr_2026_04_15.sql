-- REQ-DHUB-005-003 확장: DR/복구/감사/OM 연동 테이블 신규
-- 실행: docker exec datahub-postgres bash -c "psql -U datahub -d datahub -f /tmp/mig_dr.sql"

-- 1) PIT(Point-In-Time) 복구 정의
CREATE TABLE IF NOT EXISTS dr_pit_recovery (
    id UUID PRIMARY KEY,
    recovery_name VARCHAR(200) NOT NULL,
    target_source_id UUID REFERENCES collection_data_source(id) ON DELETE SET NULL,
    target_backup_id UUID REFERENCES sys_dr_backup(id) ON DELETE SET NULL,
    target_timestamp TIMESTAMP NOT NULL,
    simulation_only BOOLEAN DEFAULT TRUE,
    approval_status VARCHAR(30) DEFAULT 'PENDING',  -- PENDING/APPROVED/REJECTED/EXECUTED
    approved_by UUID,
    approved_at TIMESTAMP,
    reject_reason TEXT,
    simulation_result JSONB,                        -- {estimated_rows, estimated_size_mb, estimated_duration_sec, warnings}
    execution_result JSONB,                         -- {actual_rows, actual_duration_sec, restored_tables}
    executed_at TIMESTAMP,
    status VARCHAR(30) DEFAULT 'DRAFT',             -- DRAFT/SIMULATED/READY/EXECUTING/COMPLETED/FAILED
    error_message TEXT,
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_by UUID,
    updated_at TIMESTAMP DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);
COMMENT ON TABLE dr_pit_recovery IS 'PIT 복구 정의(시뮬레이션+승인+실행)';
CREATE INDEX IF NOT EXISTS ix_dr_pit_status ON dr_pit_recovery(status);
CREATE INDEX IF NOT EXISTS ix_dr_pit_target_source ON dr_pit_recovery(target_source_id);
CREATE INDEX IF NOT EXISTS ix_dr_pit_not_deleted ON dr_pit_recovery(is_deleted) WHERE is_deleted = FALSE;

-- 2) 복구 실행 로그(이력 조회용)
CREATE TABLE IF NOT EXISTS dr_restore_log (
    id UUID PRIMARY KEY,
    pit_recovery_id UUID REFERENCES dr_pit_recovery(id) ON DELETE SET NULL,
    backup_id UUID REFERENCES sys_dr_backup(id) ON DELETE SET NULL,
    restore_type VARCHAR(30) NOT NULL,              -- FULL_RESTORE/PIT_RESTORE/SIMULATION
    source_system VARCHAR(200),
    target_system VARCHAR(200),
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    duration_sec INTEGER,
    restored_rows BIGINT,
    restored_tables INTEGER,
    restored_size_mb NUMERIC(14, 2),
    status VARCHAR(30),                             -- SUCCESS/FAIL/PARTIAL
    error_message TEXT,
    details JSONB,
    executed_by UUID,
    created_at TIMESTAMP DEFAULT NOW()
);
COMMENT ON TABLE dr_restore_log IS '복구 실행 이력 로그';
CREATE INDEX IF NOT EXISTS ix_dr_restore_pit ON dr_restore_log(pit_recovery_id);
CREATE INDEX IF NOT EXISTS ix_dr_restore_status ON dr_restore_log(status);
CREATE INDEX IF NOT EXISTS ix_dr_restore_started ON dr_restore_log(started_at);

-- 3) DB 계정 이력(복원 대상 시스템 계정 변경 추적)
CREATE TABLE IF NOT EXISTS dr_db_account_history (
    id UUID PRIMARY KEY,
    source_id UUID REFERENCES collection_data_source(id) ON DELETE CASCADE,
    account_name VARCHAR(200) NOT NULL,
    action VARCHAR(30) NOT NULL,                    -- CREATE/ALTER/DROP/GRANT/REVOKE/PASSWORD_CHANGE
    privileges JSONB,
    changed_by UUID,
    changed_at TIMESTAMP DEFAULT NOW(),
    note TEXT
);
COMMENT ON TABLE dr_db_account_history IS 'DB 계정 변경 이력';
CREATE INDEX IF NOT EXISTS ix_dr_acct_source ON dr_db_account_history(source_id);
CREATE INDEX IF NOT EXISTS ix_dr_acct_changed ON dr_db_account_history(changed_at);

-- 4) 이관/복제 감사로그 (migration 전용 감사)
CREATE TABLE IF NOT EXISTS migration_audit_log (
    id UUID PRIMARY KEY,
    migration_id UUID REFERENCES collection_migration(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,                    -- CREATE/START/PAUSE/RESUME/FAIL/COMPLETE/VALIDATE/ROLLBACK
    phase VARCHAR(50),                              -- SCHEMA_COPY/DATA_COPY/INDEX_REBUILD/VALIDATION/CUTOVER
    actor_id UUID,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    duration_ms INTEGER,
    table_name VARCHAR(300),
    row_count BIGINT,
    details JSONB,                                  -- {source_checksum, target_checksum, row_diff, schema_diff, ...}
    severity VARCHAR(20) DEFAULT 'INFO',            -- INFO/WARNING/ERROR
    created_at TIMESTAMP DEFAULT NOW()
);
COMMENT ON TABLE migration_audit_log IS '이관 감사 로그(DDL/DML/검증)';
CREATE INDEX IF NOT EXISTS ix_mig_audit_migration ON migration_audit_log(migration_id);
CREATE INDEX IF NOT EXISTS ix_mig_audit_action ON migration_audit_log(action);
CREATE INDEX IF NOT EXISTS ix_mig_audit_created ON migration_audit_log(created_at);

-- 5) 이관 검증 결과
CREATE TABLE IF NOT EXISTS migration_validation_result (
    id UUID PRIMARY KEY,
    migration_id UUID REFERENCES collection_migration(id) ON DELETE CASCADE,
    table_name VARCHAR(300) NOT NULL,
    validation_type VARCHAR(30) NOT NULL,           -- ROW_COUNT/CHECKSUM/SCHEMA_DIFF/PK_CONSISTENCY
    source_value TEXT,
    target_value TEXT,
    match_status VARCHAR(20),                       -- MATCH/MISMATCH/ERROR/SKIPPED
    diff_count BIGINT,
    diff_details JSONB,
    executed_at TIMESTAMP DEFAULT NOW(),
    duration_ms INTEGER
);
COMMENT ON TABLE migration_validation_result IS '이관 검증 결과(row/checksum/schema diff)';
CREATE INDEX IF NOT EXISTS ix_mig_val_migration ON migration_validation_result(migration_id);
CREATE INDEX IF NOT EXISTS ix_mig_val_status ON migration_validation_result(match_status);

-- 6) OpenMetadata 동기화 로그
CREATE TABLE IF NOT EXISTS openmetadata_sync_log (
    id UUID PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,               -- TABLE/COLUMN/LINEAGE/TAG/AUDIT/PIPELINE
    entity_id UUID,                                 -- catalog_dataset.id / catalog_column.id / ...
    entity_name VARCHAR(300),
    sync_direction VARCHAR(30) DEFAULT 'PUSH',      -- PUSH(허브→OM)/PULL(OM→허브)
    operation VARCHAR(30),                          -- CREATE/UPDATE/DELETE/UPSERT
    om_entity_id VARCHAR(300),                      -- OM 측 엔티티 FQN/ID
    status VARCHAR(30),                             -- SUCCESS/FAIL/SKIPPED/PENDING
    http_status INTEGER,
    error_message TEXT,
    payload JSONB,
    response JSONB,
    started_at TIMESTAMP DEFAULT NOW(),
    duration_ms INTEGER
);
COMMENT ON TABLE openmetadata_sync_log IS 'OpenMetadata 동기화 로그(라인에이지/감사/이력 통합관리)';
CREATE INDEX IF NOT EXISTS ix_om_sync_entity ON openmetadata_sync_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS ix_om_sync_status ON openmetadata_sync_log(status);
CREATE INDEX IF NOT EXISTS ix_om_sync_started ON openmetadata_sync_log(started_at);

-- 7) SysDrBackup 보강: 스케줄러 필드 추가
ALTER TABLE sys_dr_backup ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
COMMENT ON COLUMN sys_dr_backup.is_active IS '스케줄 활성여부';
ALTER TABLE sys_dr_backup ADD COLUMN IF NOT EXISTS next_run_at TIMESTAMP;
COMMENT ON COLUMN sys_dr_backup.next_run_at IS '다음실행일시';
ALTER TABLE sys_dr_backup ADD COLUMN IF NOT EXISTS backup_command TEXT;
COMMENT ON COLUMN sys_dr_backup.backup_command IS '백업 명령어 템플릿 (예: pg_dump -h $HOST -U $USER $DB > $FILE)';
ALTER TABLE sys_dr_backup ADD COLUMN IF NOT EXISTS source_id UUID REFERENCES collection_data_source(id) ON DELETE SET NULL;
COMMENT ON COLUMN sys_dr_backup.source_id IS '대상 데이터소스ID';
ALTER TABLE sys_dr_backup ADD COLUMN IF NOT EXISTS last_error_message TEXT;
COMMENT ON COLUMN sys_dr_backup.last_error_message IS '최근 실패 메시지';

CREATE INDEX IF NOT EXISTS ix_sys_dr_active ON sys_dr_backup(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS ix_sys_dr_next_run ON sys_dr_backup(next_run_at) WHERE is_active = TRUE;
