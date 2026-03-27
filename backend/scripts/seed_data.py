"""
K-water 데이터허브 포털 - 전체 88개 테이블 시드 데이터
UI 화면에 표시되는 실제 데이터 기반으로 생성
"""
import uuid
import json
import random
import hashlib
from datetime import datetime, date, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# ── 연결 ──
# psycopg3 native JSONB 자동 처리를 위해 직접 psycopg 사용
import psycopg
from psycopg.types.json import Jsonb

engine = create_engine("postgresql+psycopg://datahub:datahub@postgres:5432/datahub")


def J(val):
    """JSONB 파라미터 래퍼: dict/list를 JSON 문자열로 변환"""
    if isinstance(val, (dict, list)):
        return json.dumps(val, ensure_ascii=False)
    return val


def uid():
    return uuid.uuid4()


def now(days_ago=0, hours_ago=0):
    return datetime.now() - timedelta(days=days_ago, hours=hours_ago)


def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


# ── 공통 ID 저장소 ──
IDS = {}


def run():
    with Session(engine) as s:
        # 순서 중요: FK 의존성 순서대로
        seed_sys_config(s)
        seed_sys_infrastructure(s)
        seed_sys_cloud_config(s)
        seed_sys_dr_backup(s)
        seed_sys_package(s)
        seed_sys_interface(s)
        seed_sys_integration(s)
        seed_sys_dmz_link(s)

        seed_data_grades(s)
        seed_data_classifications(s)

        seed_user_roles(s)
        seed_user_permissions(s)
        seed_user_role_permissions(s)
        seed_user_accounts(s)
        seed_user_role_maps(s)
        seed_user_data_access_policies(s)
        seed_user_access_requests(s)
        seed_user_login_history(s)
        seed_user_sessions(s)
        seed_std_request_history(s)
        seed_quality_schedule(s)

        seed_catalog_datasets(s)
        seed_catalog_columns(s)
        seed_catalog_tags(s)
        seed_catalog_dataset_tags(s)
        seed_catalog_lineage(s)
        seed_catalog_search_index(s)

        seed_collection_strategy(s)
        seed_collection_data_source(s)
        seed_collection_dataset_config(s)
        seed_collection_schedule(s)
        seed_collection_job(s)
        seed_collection_migration(s)
        seed_collection_external_agency(s)
        seed_collection_spatial_config(s)

        seed_cleansing_rule(s)
        seed_cleansing_job(s)
        seed_cleansing_result_detail(s)
        seed_anonymization_config(s)
        seed_anonymization_log(s)
        seed_transform_model(s)
        seed_transform_mapping(s)

        seed_storage_zone(s)
        seed_storage_highspeed_db(s)
        seed_storage_unstructured(s)
        seed_storage_dataset_location(s)

        seed_distribution_format(s)
        seed_distribution_dataset(s)
        seed_distribution_config(s)
        seed_distribution_request(s)
        seed_distribution_download_log(s)
        seed_distribution_api_endpoint(s)
        seed_distribution_api_key(s)
        seed_distribution_api_usage_log(s)
        seed_distribution_mcp_config(s)
        seed_distribution_fusion_model(s)
        seed_distribution_stats(s)

        seed_portal_dashboard_template(s)
        seed_portal_dashboard_widget(s)
        seed_portal_user_dashboard(s)
        seed_portal_visualization_chart(s)
        seed_portal_chart_template(s)
        seed_portal_bookmark(s)
        seed_portal_recent_view(s)
        seed_portal_search_history(s)
        seed_portal_notification(s)
        seed_portal_notification_subscription(s)
        seed_portal_sitemap_menu(s)

        seed_operation_hub_stats(s)
        seed_operation_report_template(s)
        seed_operation_report_generation(s)
        seed_operation_ai_query_log(s)
        seed_operation_ai_model_config(s)
        seed_operation_access_log(s)
        seed_operation_system_event(s)

        s.commit()
        print("=== 전체 시드 데이터 입력 완료 ===")


# ═══════════════════════════════════════
# SA-01. 공통/시스템
# ═══════════════════════════════════════

def seed_sys_config(s):
    configs = [
        ("app.name", "K-water 데이터허브 포털", "STRING", "시스템"),
        ("app.version", "1.0.0", "STRING", "시스템"),
        ("app.timezone", "Asia/Seoul", "STRING", "시스템"),
        ("auth.session_timeout_min", "30", "NUMBER", "인증"),
        ("auth.max_login_fail", "5", "NUMBER", "인증"),
        ("auth.password_expiry_days", "90", "NUMBER", "인증"),
        ("auth.jwt_secret", "encrypted_secret_key", "STRING", "인증"),
        ("data.max_download_rows", "1000000", "NUMBER", "데이터"),
        ("data.max_upload_size_mb", "500", "NUMBER", "데이터"),
        ("data.default_page_size", "20", "NUMBER", "데이터"),
        ("notification.email_enabled", "true", "BOOLEAN", "알림"),
        ("notification.sms_enabled", "false", "BOOLEAN", "알림"),
        ("quality.auto_check_enabled", "true", "BOOLEAN", "품질"),
        ("quality.min_score_threshold", "80", "NUMBER", "품질"),
        ("storage.max_capacity_tb", "5", "NUMBER", "저장소"),
        ("api.rate_limit_per_min", "60", "NUMBER", "API"),
        ("api.default_version", "v1", "STRING", "API"),
        ("openmetadata.url", "http://openmetadata:8585/api", "STRING", "연동"),
        ("kafka.bootstrap_servers", "kafka:9092", "STRING", "연동"),
        ("redis.url", "redis://redis:6379/0", "STRING", "연동"),
    ]
    for key, val, typ, cat in configs:
        s.execute(text("""INSERT INTO sys_config (id, config_key, config_value, config_type, category, description, is_encrypted, created_at, is_deleted)
            VALUES (:id, :key, :val, :typ, :cat, :desc, :enc, :ca, false)"""),
            {"id": uid(), "key": key, "val": val, "typ": typ, "cat": cat, "desc": f"{cat} 설정 - {key}", "enc": "secret" in key, "ca": now()})
    print(f"  sys_config: {len(configs)}건")

def seed_sys_infrastructure(s):
    infras = [
        ("PostgreSQL (Master)", "DB", "10.0.1.10", "PRD", {"cpu": "8core", "memory": "32GB", "disk": "1TB"}, 45, 62, 38),
        ("PostgreSQL (Replica)", "DB", "10.0.1.11", "PRD", {"cpu": "8core", "memory": "32GB", "disk": "1TB"}, 32, 55, 38),
        ("OpenMetadata Server", "SERVER", "10.0.2.10", "PRD", {"cpu": "4core", "memory": "16GB", "disk": "500GB"}, 28, 48, 22),
        ("FastAPI Gateway", "SERVER", "10.0.2.20", "PRD", {"cpu": "4core", "memory": "8GB", "disk": "100GB"}, 15, 30, 12),
        ("Kafka Cluster", "SERVER", "10.0.3.10", "PRD", {"cpu": "8core", "memory": "32GB", "disk": "2TB"}, 78, 85, 65),
        ("Redis Sentinel", "SERVER", "10.0.3.20", "PRD", {"cpu": "2core", "memory": "8GB", "disk": "50GB"}, 12, 20, 8),
        ("Celery Worker Pool", "SERVER", "10.0.4.10", "PRD", {"cpu": "16core", "memory": "32GB", "disk": "200GB"}, 55, 60, 15),
        ("Nginx LB", "NETWORK", "10.0.0.10", "PRD", {"cpu": "2core", "memory": "4GB", "disk": "50GB"}, 8, 15, 42),
        ("MinIO Storage", "STORAGE", "10.0.5.10", "PRD", {"cpu": "4core", "memory": "16GB", "disk": "10TB"}, 20, 35, 72),
        ("Airflow Scheduler", "SERVER", "10.0.4.20", "PRD", {"cpu": "4core", "memory": "16GB", "disk": "200GB"}, 35, 42, 18),
        ("PostgreSQL (DR)", "DB", "10.1.1.10", "DR", {"cpu": "8core", "memory": "32GB", "disk": "1TB"}, 10, 20, 35),
        ("Elasticsearch", "SERVER", "10.0.6.10", "PRD", {"cpu": "8core", "memory": "32GB", "disk": "2TB"}, 42, 68, 55),
    ]
    IDS["infra"] = []
    for name, typ, host, env, specs, cpu, mem, disk in infras:
        iid = uid()
        IDS["infra"].append(iid)
        specs["cpu_usage"] = cpu
        specs["memory_usage"] = mem
        specs["disk_usage"] = disk
        status = "WARNING" if cpu > 70 else "ACTIVE"
        s.execute(text("""INSERT INTO sys_infrastructure (id, infra_name, infra_type, host_address, status, environment, specs, monitoring_url, last_health_check, created_at, is_deleted)
            VALUES (:id, :n, :t, :h, :st, :e, CAST(:sp AS jsonb), :mu, :lhc, :ca, false)"""),
            {"id": iid, "n": name, "t": typ, "h": host, "st": status, "e": env,
             "sp": json.dumps(specs, ensure_ascii=False), "mu": f"http://grafana.internal/d/{name.lower().replace(' ','-')}", "lhc": now(), "ca": now()})
    print(f"  sys_infrastructure: {len(infras)}건")

def seed_sys_cloud_config(s):
    clouds = [
        ("NCP", "VM", "datahub-api-01", "KR-1", 450000),
        ("NCP", "VM", "datahub-api-02", "KR-1", 450000),
        ("NCP", "K8S", "datahub-k8s-cluster", "KR-1", 1200000),
        ("NCP", "STORAGE", "datahub-obj-storage", "KR-1", 350000),
        ("NCP", "DB", "datahub-pg-primary", "KR-1", 800000),
        ("NCP", "DB", "datahub-pg-replica", "KR-2", 600000),
        ("NCP", "LB", "datahub-lb-01", "KR-1", 150000),
        ("NCP", "STORAGE", "datahub-backup-storage", "KR-2", 200000),
    ]
    for prov, rtype, rname, region, cost in clouds:
        s.execute(text("""INSERT INTO sys_cloud_config (id, cloud_provider, resource_type, resource_name, resource_id, region, configuration, status, monthly_cost, created_at, is_deleted)
            VALUES (:id, :p, :rt, :rn, :ri, :reg, '{}', 'ACTIVE', :cost, :ca, false)"""),
            {"id": uid(), "p": prov, "rt": rtype, "rn": rname, "ri": f"ncp-{uid().hex[:8]}", "reg": region, "cost": cost, "ca": now()})
    print(f"  sys_cloud_config: {len(clouds)}건")

def seed_sys_dr_backup(s):
    backups = [
        ("PostgreSQL 전체 백업", "FULL", "PostgreSQL Master", "0 2 * * *", 30, "/backup/pg/full"),
        ("PostgreSQL 증분 백업", "INCREMENTAL", "PostgreSQL Master", "0 */6 * * *", 7, "/backup/pg/incr"),
        ("OpenMetadata 백업", "FULL", "OpenMetadata Server", "0 3 * * *", 14, "/backup/om"),
        ("MinIO 오브젝트 백업", "FULL", "MinIO Storage", "0 4 * * 0", 60, "/backup/minio"),
        ("Redis RDB 스냅샷", "FULL", "Redis Sentinel", "0 */12 * * *", 3, "/backup/redis"),
        ("Airflow DAG 백업", "FULL", "Airflow Scheduler", "0 5 * * *", 30, "/backup/airflow"),
        ("전체 시스템 DR 백업", "FULL", "전체", "0 1 * * 0", 90, "/backup/dr/full"),
        ("로그 아카이빙", "INCREMENTAL", "전체", "0 6 * * *", 365, "/backup/logs"),
    ]
    for name, btype, target, cron, ret, path in backups:
        s.execute(text("""INSERT INTO sys_dr_backup (id, backup_name, backup_type, target_system, schedule_cron, retention_days, storage_path, last_backup_at, last_backup_size_mb, last_backup_status, created_at, is_deleted)
            VALUES (:id, :n, :bt, :ts, :c, :r, :p, :lb, :sz, 'SUCCESS', :ca, false)"""),
            {"id": uid(), "n": name, "bt": btype, "ts": target, "c": cron, "r": ret, "p": path,
             "lb": now(hours_ago=random.randint(1, 48)), "sz": random.randint(100, 50000), "ca": now()})
    print(f"  sys_dr_backup: {len(backups)}건")

def seed_sys_package(s):
    packages = [
        ("PostgreSQL", "16.2", "PostgreSQL Global", "오픈소스", "PASSED"),
        ("FastAPI", "0.110.0", "Tiangolo", "MIT", "PASSED"),
        ("Vue.js", "3.4.21", "Evan You", "MIT", "PASSED"),
        ("Apache Kafka", "3.7.0", "Apache Foundation", "Apache 2.0", "PASSED"),
        ("Redis", "7.2.4", "Redis Ltd", "BSD", "PASSED"),
        ("OpenMetadata", "1.3.1", "Open Metadata", "Apache 2.0", "PASSED"),
        ("AG Grid", "31.1.0", "AG Grid Ltd", "Enterprise", "PASSED"),
        ("ECharts", "5.5.0", "Apache Foundation", "Apache 2.0", "PASSED"),
        ("Element Plus", "2.6.1", "Element Plus", "MIT", "PASSED"),
        ("Celery", "5.3.6", "Ask Solem", "BSD", "IN_PROGRESS"),
    ]
    for name, ver, vendor, lic, poc in packages:
        s.execute(text("""INSERT INTO sys_package (id, package_name, package_version, vendor, license_type, license_expiry, poc_status, verification_date, description, created_at, is_deleted)
            VALUES (:id, :n, :v, :vd, :lt, :le, :ps, :vd2, :d, :ca, false)"""),
            {"id": uid(), "n": name, "v": ver, "vd": vendor, "lt": lic,
             "le": date(2027, 12, 31), "ps": poc, "vd2": date(2026, 3, 1), "d": f"{name} {ver} 패키지", "ca": now()})
    print(f"  sys_package: {len(packages)}건")

def seed_sys_interface(s):
    interfaces = [
        ("IF-001", "오아시스 SSO 연동", "REST", "오아시스", "데이터허브", "HTTPS", "https://oasis.kwater.or.kr/sso/api", "JSON", "REALTIME"),
        ("IF-002", "OpenMetadata 카탈로그 동기화", "REST", "OpenMetadata", "데이터허브", "HTTP", "http://openmetadata:8585/api", "JSON", "BATCH"),
        ("IF-003", "Kafka 실시간 수집", "KAFKA", "IoT 센서", "데이터허브", "TCP", "kafka:9092", "JSON", "REALTIME"),
        ("IF-004", "SAP ERP 연동", "SOAP", "SAP ERP", "데이터허브", "HTTPS", "https://sap.kwater.or.kr/ws", "XML", "BATCH"),
        ("IF-005", "기상청 API 연동", "REST", "기상청", "데이터허브", "HTTPS", "https://apis.data.go.kr/weather", "JSON", "BATCH"),
        ("IF-006", "수자원공사 GIS 연동", "REST", "GIS서버", "데이터허브", "HTTPS", "https://gis.kwater.or.kr/api", "JSON", "BATCH"),
        ("IF-007", "외부 공개 API 제공", "REST", "데이터허브", "외부시스템", "HTTPS", "https://datahub.kwater.or.kr/api/v1", "JSON", "REALTIME"),
        ("IF-008", "알림 메시지 발송", "REST", "데이터허브", "SMS Gateway", "HTTPS", "https://sms.kwater.or.kr/api", "JSON", "EVENT"),
    ]
    for code, name, itype, src, tgt, proto, url, fmt, stype in interfaces:
        s.execute(text("""INSERT INTO sys_interface (id, interface_code, interface_name, interface_type, source_system, target_system, protocol, endpoint_url, data_format, schedule_type, status, created_at, is_deleted)
            VALUES (:id, :c, :n, :it, :src, :tgt, :p, :u, :f, :st, 'ACTIVE', :ca, false)"""),
            {"id": uid(), "c": code, "n": name, "it": itype, "src": src, "tgt": tgt, "p": proto, "u": url, "f": fmt, "st": stype, "ca": now()})
    print(f"  sys_interface: {len(interfaces)}건")

def seed_sys_integration(s):
    integrations = [
        ("SAP ERP 데이터 연동", "SAP", "INBOUND"),
        ("Oracle 레거시 DB 연동", "ORACLE", "INBOUND"),
        ("티베로 수도 시스템", "TIBERO", "INBOUND"),
        ("PostgreSQL 분석 DB", "POSTGRESQL", "OUTBOUND"),
        ("MySQL 모니터링 DB", "MYSQL", "INBOUND"),
    ]
    for name, dbtype, direction in integrations:
        s.execute(text("""INSERT INTO sys_integration (id, integration_name, source_db_type, connection_config, sync_direction, sync_status, last_sync_at, created_at, is_deleted)
            VALUES (:id, :n, :dt, CAST(:cc AS jsonb), :d, 'SUCCESS', :ls, :ca, false)"""),
            {"id": uid(), "n": name, "dt": dbtype, "cc": '{"host":"10.0.1.100","port":5432}', "d": direction, "ls": now(hours_ago=random.randint(1, 24)), "ca": now()})
    print(f"  sys_integration: {len(integrations)}건")

def seed_sys_dmz_link(s):
    links = [
        ("외부 공개 API Proxy", "PROXY", "OUTBOUND"),
        ("기상청 데이터 수신", "ONE_WAY", "INBOUND"),
        ("파일 전송 (내→외)", "FILE_TRANSFER", "OUTBOUND"),
        ("SMS 발송 Proxy", "PROXY", "OUTBOUND"),
    ]
    for name, ltype, direction in links:
        s.execute(text("""INSERT INTO sys_dmz_link (id, link_name, link_type, external_url, dmz_proxy_url, transfer_direction, security_level, is_active, created_at, is_deleted)
            VALUES (:id, :n, :lt, :eu, :dp, :d, 'HIGH', true, :ca, false)"""),
            {"id": uid(), "n": name, "lt": ltype, "eu": "https://external.kwater.or.kr", "dp": "https://dmz.kwater.or.kr/proxy", "d": direction, "ca": now()})
    print(f"  sys_dmz_link: {len(links)}건")


# ═══════════════════════════════════════
# SA-02. 사용자/권한
# ═══════════════════════════════════════

def seed_user_roles(s):
    roles = [
        ("ADMIN", "시스템관리자", True, "/portal", True, 1),
        ("MANAGER", "데이터관리자", True, "/portal", True, 2),
        ("INTERNAL", "내부사용자", True, "/portal", False, 3),
        ("EXTERNAL", "외부사용자", True, "/portal", False, 4),
    ]
    IDS["roles"] = {}
    for code, name, is_sys, route, admin, sort in roles:
        rid = uid()
        IDS["roles"][code] = rid
        s.execute(text("""INSERT INTO user_role (id, role_code, role_name, description, is_system_role, default_route, can_access_admin, sort_order, created_at, is_deleted)
            VALUES (:id, :c, :n, :d, :is_sys, :r, :ca_admin, :so, :ca, false)"""),
            {"id": rid, "c": code, "n": name, "d": f"{name} 역할", "is_sys": is_sys, "r": route, "ca_admin": admin, "so": sort, "ca": now()})
    print(f"  user_role: {len(roles)}건")

def seed_user_permissions(s):
    perms = [
        ("MENU_ADMIN_SYSTEM", "시스템관리 메뉴", "MENU", "/admin/system", "MANAGE"),
        ("MENU_ADMIN_USER", "사용자관리 메뉴", "MENU", "/admin/user", "MANAGE"),
        ("MENU_ADMIN_STANDARD", "데이터표준 메뉴", "MENU", "/admin/standard", "MANAGE"),
        ("MENU_ADMIN_COLLECTION", "데이터수집 메뉴", "MENU", "/admin/collection", "MANAGE"),
        ("MENU_ADMIN_CLEANSING", "데이터정제 메뉴", "MENU", "/admin/cleansing", "MANAGE"),
        ("MENU_ADMIN_STORAGE", "데이터저장 메뉴", "MENU", "/admin/storage", "MANAGE"),
        ("MENU_ADMIN_DIST", "데이터유통 메뉴", "MENU", "/admin/distribution", "MANAGE"),
        ("MENU_ADMIN_OPS", "운영관리 메뉴", "MENU", "/admin/operation", "MANAGE"),
        ("DATA_READ", "데이터 조회", "DATA", "dataset", "READ"),
        ("DATA_DOWNLOAD", "데이터 다운로드", "DATA", "dataset", "DOWNLOAD"),
        ("DATA_WRITE", "데이터 등록/수정", "DATA", "dataset", "WRITE"),
        ("DATA_DELETE", "데이터 삭제", "DATA", "dataset", "DELETE"),
        ("API_ACCESS", "API 접근", "API", "api", "READ"),
        ("VISUALIZATION", "시각화 기능", "FUNCTION", "visualization", "READ"),
        ("AI_SEARCH", "AI 검색 기능", "FUNCTION", "ai-search", "READ"),
    ]
    IDS["perms"] = {}
    for code, name, ptype, resource, action in perms:
        pid = uid()
        IDS["perms"][code] = pid
        s.execute(text("""INSERT INTO user_permission (id, permission_code, permission_name, permission_type, resource, action, created_at, is_deleted)
            VALUES (:id, :c, :n, :pt, :r, :a, :ca, false)"""),
            {"id": pid, "c": code, "n": name, "pt": ptype, "r": resource, "a": action, "ca": now()})
    print(f"  user_permission: {len(perms)}건")

def seed_user_role_permissions(s):
    mapping = {
        "ADMIN": list(IDS["perms"].keys()),
        "MANAGER": ["MENU_ADMIN_STANDARD", "MENU_ADMIN_COLLECTION", "MENU_ADMIN_CLEANSING", "MENU_ADMIN_STORAGE", "MENU_ADMIN_DIST", "MENU_ADMIN_OPS", "DATA_READ", "DATA_DOWNLOAD", "DATA_WRITE", "DATA_DELETE", "API_ACCESS", "VISUALIZATION", "AI_SEARCH"],
        "INTERNAL": ["DATA_READ", "DATA_DOWNLOAD", "API_ACCESS", "VISUALIZATION", "AI_SEARCH"],
        "EXTERNAL": ["DATA_READ", "DATA_DOWNLOAD"],
    }
    cnt = 0
    for role_code, perm_codes in mapping.items():
        for pc in perm_codes:
            s.execute(text("""INSERT INTO user_role_permission (id, role_id, permission_id, created_at, is_deleted) VALUES (:id, :r, :p, :ca, false)"""),
                {"id": uid(), "r": IDS["roles"][role_code], "p": IDS["perms"][pc], "ca": now()})
            cnt += 1
    print(f"  user_role_permission: {cnt}건")

def seed_user_accounts(s):
    users = [
        ("admin", "admin", "INTERNAL", "20210001", "관리자", "admin@kwater.or.kr", "010-1234-0001", "IT001", "정보화처", "처장", "ACTIVE", "ADMIN"),
        ("manager", "manager", "INTERNAL", "20210015", "김매니저", "manager@kwater.or.kr", "010-1234-0002", "WR001", "수자원부", "과장", "ACTIVE", "MANAGER"),
        ("user", "user", "INTERNAL", "20220032", "홍길동", "user@kwater.or.kr", "010-1234-0003", "WS001", "수도부", "대리", "ACTIVE", "INTERNAL"),
        ("lee", "lee123", "INTERNAL", "20220048", "이영희", "lee@kwater.or.kr", "010-1234-0004", "EV001", "환경부", "사원", "ACTIVE", "INTERNAL"),
        ("park", "park123", "INTERNAL", "20190087", "박철수", "park@kwater.or.kr", "010-1234-0005", "WR001", "수자원부", "부장", "ACTIVE", "MANAGER"),
        ("jung", "jung123", "INTERNAL", "20230012", "정미경", "jung@kwater.or.kr", "010-1234-0006", "IT001", "정보화처", "사원", "SUSPENDED", "INTERNAL"),
        ("guest", "guest", "EXTERNAL", None, "외부사용자", "guest@example.com", "010-9876-0001", None, None, None, "ACTIVE", "EXTERNAL"),
        ("ext_kim", "ext123", "EXTERNAL", None, "김외부", "ext_kim@test.com", "010-9876-0002", None, "한국환경공단", None, "ACTIVE", "EXTERNAL"),
        ("ext_lee", "ext456", "EXTERNAL", None, "이외부", "ext_lee@test.com", "010-9876-0003", None, "환경부", None, "ACTIVE", "EXTERNAL"),
        ("ext_park", "ext789", "EXTERNAL", None, "박기상", "ext_park@weather.go.kr", "010-9876-0004", None, "기상청", None, "ACTIVE", "EXTERNAL"),
    ]
    # 추가 내부사용자 90명
    depts = [("WR001", "수자원부"), ("WS001", "수도부"), ("EV001", "환경부"), ("MG001", "경영부"), ("IT001", "정보화처")]
    positions = ["사원", "대리", "과장", "부장"]
    last_names = "김이박최정강조윤장임한오서신권황안송류홍"
    first_names = "민준서준예준도윤시우주원하준지호지후준서현우도현건우"
    for i in range(90):
        dept_code, dept_name = random.choice(depts)
        pos = random.choice(positions)
        ln = random.choice(last_names)
        fn = first_names[random.randint(0, len(first_names)-2):random.randint(0, len(first_names)-2)+2] or "준호"
        name = ln + fn
        emp = f"202{random.randint(0,5)}{random.randint(1000,9999)}"
        users.append((f"user{i+10}", f"pass{i+10}", "INTERNAL", emp, name, f"user{i+10}@kwater.or.kr", f"010-{random.randint(1000,9999)}-{random.randint(1000,9999)}", dept_code, dept_name, pos, "ACTIVE", "INTERNAL"))

    IDS["users"] = {}
    for login_id, pw, utype, emp, name, email, phone, dept_code, dept_name, pos, status, role in users:
        uid_val = uid()
        IDS["users"][login_id] = uid_val
        s.execute(text("""INSERT INTO user_account (id, user_type, login_id, password_hash, employee_no, name, email, phone, department_code, department_name, position, status, last_login_at, login_fail_count, created_at, is_deleted)
            VALUES (:id, :ut, :li, :ph, :en, :n, :e, :p, :dc, :dn, :pos, :st, :ll, 0, :ca, false)"""),
            {"id": uid_val, "ut": utype, "li": login_id, "ph": hash_pw(pw), "en": emp, "n": name, "e": email, "p": phone, "dc": dept_code, "dn": dept_name, "pos": pos, "st": status, "ll": now(days_ago=random.randint(0, 7)), "ca": now(days_ago=random.randint(30, 365))})
    print(f"  user_account: {len(users)}건")

def seed_user_role_maps(s):
    cnt = 0
    role_map = {"admin": "ADMIN", "manager": "MANAGER", "park": "MANAGER", "guest": "EXTERNAL", "ext_kim": "EXTERNAL", "ext_lee": "EXTERNAL", "ext_park": "EXTERNAL"}
    for login_id, uid_val in IDS["users"].items():
        role_code = role_map.get(login_id, "INTERNAL")
        s.execute(text("""INSERT INTO user_role_map (id, user_id, role_id, granted_by, granted_at, status) VALUES (:id, :u, :r, :gb, :ga, 'ACTIVE')"""),
            {"id": uid(), "u": uid_val, "r": IDS["roles"][role_code], "gb": IDS["users"]["admin"], "ga": now(days_ago=30)})
        cnt += 1
    print(f"  user_role_map: {cnt}건")

def seed_user_data_access_policies(s):
    policies = [
        ("관리자 전체 접근", "ADMIN", 1, '["READ","WRITE","DELETE","DOWNLOAD","MANAGE"]'),
        ("관리자 전체 접근 L2", "ADMIN", 2, '["READ","WRITE","DELETE","DOWNLOAD","MANAGE"]'),
        ("관리자 전체 접근 L3", "ADMIN", 3, '["READ","WRITE","DELETE","DOWNLOAD","MANAGE"]'),
        ("매니저 내부공유", "MANAGER", 2, '["READ","WRITE","DOWNLOAD"]'),
        ("매니저 공개", "MANAGER", 3, '["READ","WRITE","DOWNLOAD"]'),
        ("내부사용자 내부공유", "INTERNAL", 2, '["READ","DOWNLOAD"]'),
        ("내부사용자 공개", "INTERNAL", 3, '["READ","DOWNLOAD"]'),
        ("외부사용자 공개", "EXTERNAL", 3, '["READ","DOWNLOAD"]'),
    ]
    for name, role, grade, actions in policies:
        s.execute(text("""INSERT INTO user_data_access_policy (id, policy_name, role_id, data_grade_id, allowed_actions, requires_approval, created_at, is_deleted)
            VALUES (:id, :n, :r, :g, CAST(:a AS jsonb), :ra, :ca, false)"""),
            {"id": uid(), "n": name, "r": IDS["roles"][role], "g": grade, "a": actions, "ra": grade == 1, "ca": now()})
    print(f"  user_data_access_policy: {len(policies)}건")

def seed_user_access_requests(s):
    requests = [
        ("user", "DATASET", "L2", "REQUESTED", "수질 모니터링 센서 데이터 분석 목적"),
        ("ext_kim", "API", "L3", "APPROVED", "환경 데이터 연구 활용"),
        ("ext_lee", "DATASET", "L2", "REJECTED", "내부 데이터 접근 불가"),
        ("lee", "DATASET", "L1", "REVIEWING", "비공개 데이터 열람 요청"),
    ]
    for login, rtype, grade, status, reason in requests:
        reviewer = IDS["users"]["admin"] if status != "REQUESTED" else None
        s.execute(text("""INSERT INTO user_access_request (id, requester_id, target_resource_type, data_grade_code, reason, status, reviewer_id, reviewed_at, created_at, is_deleted)
            VALUES (:id, :req, :rt, :g, :re, :st, :rv, :ra, :ca, false)"""),
            {"id": uid(), "req": IDS["users"][login], "rt": rtype, "g": grade, "re": reason, "st": status, "rv": reviewer, "ra": now(days_ago=1) if reviewer else None, "ca": now(days_ago=random.randint(1, 10))})
    print(f"  user_access_request: {len(requests)}건")

def seed_user_login_history(s):
    cnt = 0
    for login_id in ["admin", "manager", "user", "lee", "park", "guest", "ext_kim"]:
        for d in range(30):
            s.execute(text("""INSERT INTO user_login_history (id, user_id, login_type, client_ip, user_agent, login_result, logged_at)
                VALUES (:id, :u, :lt, :ip, :ua, :lr, :la)"""),
                {"id": uid(), "u": IDS["users"][login_id], "lt": "SSO" if login_id not in ("guest", "ext_kim") else "PASSWORD",
                 "ip": f"10.10.{random.randint(1,50)}.{random.randint(1,254)}", "ua": "Mozilla/5.0 Chrome/122",
                 "lr": "SUCCESS" if random.random() > 0.05 else "FAIL", "la": now(days_ago=d, hours_ago=random.randint(0, 12))})
            cnt += 1
    print(f"  user_login_history: {cnt}건")

def seed_user_sessions(s):
    for login_id in ["admin", "manager", "user", "lee", "park"]:
        s.execute(text("""INSERT INTO user_session (id, user_id, access_token_jti, refresh_token_jti, client_ip, issued_at, expires_at, is_revoked)
            VALUES (:id, :u, :at, :rt, :ip, :ia, :ea, false)"""),
            {"id": uid(), "u": IDS["users"][login_id], "at": uid().hex, "rt": uid().hex, "ip": "10.10.5.22", "ia": now(), "ea": now() + timedelta(hours=1)})
    print(f"  user_session: 5건")


# ═══════════════════════════════════════
# SA-03. 데이터표준 (기존 테이블 보완)
# ═══════════════════════════════════════

def seed_data_grades(s):
    """data_grade 테이블은 이미 마이그레이션에 있을 수 있으므로 upsert"""
    cnt = s.execute(text("SELECT count(*) FROM data_grade")).scalar()
    if cnt == 0:
        grades = [("L1", "비공개", "시스템관리자만 접근 가능", "ADMIN", "필수", 1),
                  ("L2", "내부공유", "내부사용자 이상 접근 가능", "ADMIN,MANAGER,INTERNAL", "선택", 2),
                  ("L3", "공개", "모든 사용자 접근 가능", "ALL", "불필요", 3)]
        for code, name, desc, scope, anon, sort in grades:
            s.execute(text("""INSERT INTO data_grade (grade_code, grade_name, description, access_scope, dataset_count, anonymize_required, sort_order, created_at, updated_at)
                VALUES (:c, :n, :d, :s, 0, :a, :so, :ca, :ca)"""),
                {"c": code, "n": name, "d": desc, "s": scope, "a": anon, "so": sort, "ca": now()})
        print(f"  data_grade: 3건")
    else:
        print(f"  data_grade: 이미 {cnt}건 존재")

def seed_data_classifications(s):
    cnt = s.execute(text("SELECT count(*) FROM data_classification")).scalar()
    if cnt > 0:
        print(f"  data_classification: 이미 {cnt}건 존재")
        return
    cats = [
        (1, None, "수자원", "WR", 423), (1, None, "수도", "WS", 287), (1, None, "환경", "EV", 215),
        (1, None, "경영", "MG", 178), (1, None, "공간정보", "GI", 89), (1, None, "기타", "ET", 55),
    ]
    IDS["class"] = {}
    for level, parent, name, code, dsc in cats:
        s.execute(text("""INSERT INTO data_classification (parent_id, level, name, code, description, dataset_count, sort_order, status, created_at, updated_at, is_deleted)
            VALUES (:p, :l, :n, :c, :d, :ds, :so, 'ACTIVE', :ca, :ca, false) RETURNING id"""),
            {"p": parent, "l": level, "n": name, "c": code, "d": f"{name} 분류", "ds": dsc, "so": len(IDS.get("class", {})), "ca": now()})
        row = s.execute(text("SELECT id FROM data_classification WHERE code = :c"), {"c": code}).fetchone()
        IDS["class"][code] = row[0]

    # 중분류 추가
    sub_cats = [
        ("WR", "댐관리", "WR01"), ("WR", "하천관리", "WR02"), ("WR", "수문관측", "WR03"),
        ("WS", "정수처리", "WS01"), ("WS", "배수관리", "WS02"), ("WS", "수질검사", "WS03"),
        ("EV", "수질모니터링", "EV01"), ("EV", "환경영향평가", "EV02"),
        ("MG", "경영실적", "MG01"), ("MG", "전력관리", "MG02"),
    ]
    for parent_code, name, code in sub_cats:
        s.execute(text("""INSERT INTO data_classification (parent_id, level, name, code, description, dataset_count, sort_order, status, created_at, updated_at, is_deleted)
            VALUES (:p, 2, :n, :c, :d, :ds, 0, 'ACTIVE', :ca, :ca, false)"""),
            {"p": IDS["class"][parent_code], "n": name, "c": code, "d": f"{name} 중분류", "ds": random.randint(10, 80), "ca": now()})
    print(f"  data_classification: {len(cats) + len(sub_cats)}건")

def seed_std_request_history(s):
    # std_request가 이미 있으면 이력 추가
    cnt = s.execute(text("SELECT count(*) FROM std_request")).scalar()
    if cnt == 0:
        print("  std_request_history: std_request 없음, 스킵")
        return
    reqs = s.execute(text("SELECT id FROM std_request LIMIT 5")).fetchall()
    for req in reqs:
        s.execute(text("""INSERT INTO std_request_history (request_id, action, old_status, new_status, comment, changed_by, changed_at)
            VALUES (:ri, 'STATUS_CHANGE', 'PENDING', 'APPROVED', '승인 처리', 1, :ca)"""),
            {"ri": req[0], "ca": now()})
    print(f"  std_request_history: {len(reqs)}건")

def seed_quality_schedule(s):
    schedules = [
        ("일일 완전성 검증", "0 6 * * *", "댐 수위 관측 데이터"),
        ("주간 유효성 검증", "0 2 * * 1", "수질 모니터링 데이터"),
        ("월간 정확성 검증", "0 3 1 * *", "전력 사용량 통계"),
        ("일일 일관성 검증", "0 7 * * *", "상수도 배수관 GIS"),
    ]
    rules = s.execute(text("SELECT id FROM quality_rule LIMIT 4")).fetchall()
    for i, (name, cron, target) in enumerate(schedules):
        rule_id = rules[i][0] if i < len(rules) else None
        s.execute(text("""INSERT INTO quality_schedule (rule_id, schedule_name, schedule_cron, target_dataset, is_active, last_run_at, next_run_at, created_at, is_deleted)
            VALUES (:ri, :n, :c, :t, true, :lr, :nr, :ca, false)"""),
            {"ri": rule_id, "n": name, "c": cron, "t": target, "lr": now(hours_ago=6), "nr": now() + timedelta(hours=18), "ca": now()})
    print(f"  quality_schedule: {len(schedules)}건")


# ═══════════════════════════════════════
# SA-04. 데이터자산/카탈로그
# ═══════════════════════════════════════

def seed_catalog_datasets(s):
    datasets = [
        ("댐 수위 관측 데이터 (2026)", "댐 수위 관측 데이터 (2026)", "WR", 3, "수자원부", "DB", "REALTIME", 120000000, 52428800000, "admin"),
        ("수질 모니터링 센서 데이터", "수질 모니터링 센서 데이터", "EV", 2, "환경부", "IoT", "REALTIME", 85000000, 38000000000, "manager"),
        ("상수도 배수관 GIS 데이터", "상수도 배수관 GIS 데이터", "WS", 2, "수도부", "GIS", "DAILY", 3200000, 15000000000, "user"),
        ("전력 사용량 통계 (월별)", "전력 사용량 통계 (월별)", "MG", 3, "경영부", "CSV", "MONTHLY", 15600, 8500000, "manager"),
        ("강수량 예측 모델 API", "강수량 예측 모델 API", "WR", 3, "수자원부", "API", "REALTIME", None, None, "admin"),
        ("하천 유량 관측 데이터", "하천 유량 관측 데이터", "WR", 2, "수자원부", "DB", "HOURLY", 52000000, 25000000000, "manager"),
        ("환경영향평가 보고서", "환경영향평가 보고서", "EV", 2, "환경부", "FILE", "MANUAL", 8200, 420000000, "lee"),
        ("상수도 수질검사 결과", "상수도 수질검사 결과", "WS", 2, "수도부", "DB", "DAILY", 520000, 2100000000, "user"),
        ("경영실적 데이터 (분기)", "경영실적 데이터 (분기)", "MG", 1, "경영부", "CSV", "MONTHLY", 4800, 3200000, "park"),
        ("IoT 센서 원시 데이터", "IoT 센서 원시 데이터", "WR", 2, "수자원부", "IoT", "REALTIME", 1800000000, 980000000000, "manager"),
    ]
    IDS["datasets"] = {}
    cls_ids = {}
    rows = s.execute(text("SELECT id, code FROM data_classification WHERE level = 1")).fetchall()
    for row in rows:
        cls_ids[row[1]] = row[0]

    for name, name_kr, cls_code, grade, dept, fmt, freq, rcnt, size, owner_login in datasets:
        did = uid()
        IDS["datasets"][name] = did
        s.execute(text("""INSERT INTO catalog_dataset (id, dataset_name, dataset_name_kr, classification_id, grade_id, source_system, owner_department, owner_user_id, description, data_format, refresh_frequency, row_count, size_bytes, status, created_at, is_deleted)
            VALUES (:id, :n, :nk, :ci, :gi, :ss, :od, :ou, :d, :f, :fr, :rc, :sz, 'ACTIVE', :ca, false)"""),
            {"id": did, "n": name, "nk": name_kr, "ci": cls_ids.get(cls_code), "gi": grade, "ss": "K-water 내부시스템", "od": dept, "ou": IDS["users"].get(owner_login), "d": f"{name_kr} 데이터셋", "f": fmt, "fr": freq, "rc": rcnt, "sz": size, "ca": now(days_ago=random.randint(0, 30))})
    print(f"  catalog_dataset: {len(datasets)}건")

def seed_catalog_columns(s):
    col_defs = {
        "댐 수위 관측 데이터 (2026)": [
            ("MEAS_DT", "측정일시", "TIMESTAMP", None, True, False), ("DAM_CD", "댐코드", "VARCHAR", 10, True, False),
            ("DAM_NM", "댐명칭", "VARCHAR", 50, False, False), ("WATER_LV", "수위", "NUMERIC", 8, False, True),
            ("INFLOW", "유입량", "NUMERIC", 10, False, True), ("OUTFLOW", "방류량", "NUMERIC", 10, False, True),
            ("STORAGE_RT", "저수율", "NUMERIC", 5, False, True), ("TEMP", "수온", "NUMERIC", 5, False, True),
            ("TURBIDITY", "탁도", "NUMERIC", 8, False, True), ("RAINFALL", "강수량", "NUMERIC", 8, False, True),
            ("STATUS_CD", "상태코드", "VARCHAR", 2, False, True), ("REG_DT", "등록일시", "TIMESTAMP", None, False, False),
        ],
        "수질 모니터링 센서 데이터": [
            ("SENSOR_ID", "센서ID", "VARCHAR", 20, True, False), ("MEAS_DT", "측정일시", "TIMESTAMP", None, True, False),
            ("PH", "수소이온농도", "NUMERIC", 5, False, True), ("DO_VAL", "용존산소", "NUMERIC", 8, False, True),
            ("BOD", "BOD", "NUMERIC", 8, False, True), ("COD", "COD", "NUMERIC", 8, False, True),
            ("SS", "부유물질", "NUMERIC", 8, False, True), ("TN", "총질소", "NUMERIC", 8, False, True),
            ("TP", "총인", "NUMERIC", 8, False, True), ("WATER_TEMP", "수온", "NUMERIC", 5, False, True),
            ("TURB", "탁도", "NUMERIC", 8, False, True), ("EC", "전기전도도", "NUMERIC", 8, False, True),
            ("CHLORO", "클로로필", "NUMERIC", 8, False, True), ("LOCATION_CD", "지점코드", "VARCHAR", 20, False, False),
            ("LOCATION_NM", "지점명", "VARCHAR", 100, False, True), ("LAT", "위도", "NUMERIC", 12, False, True),
            ("LON", "경도", "NUMERIC", 12, False, True), ("STATUS", "상태", "VARCHAR", 10, False, True),
        ],
    }
    cnt = 0
    for ds_name, cols in col_defs.items():
        ds_id = IDS["datasets"].get(ds_name)
        if not ds_id:
            continue
        for i, (cname, cname_kr, dtype, length, is_pk, nullable) in enumerate(cols):
            s.execute(text("""INSERT INTO catalog_column (id, dataset_id, column_name, column_name_kr, data_type, length, is_pk, is_nullable, sort_order)
                VALUES (:id, :di, :cn, :ck, :dt, :l, :pk, :nu, :so)"""),
                {"id": uid(), "di": ds_id, "cn": cname, "ck": cname_kr, "dt": dtype, "l": length, "pk": is_pk, "nu": nullable, "so": i})
            cnt += 1
    print(f"  catalog_column: {cnt}건")

def seed_catalog_tags(s):
    tags = [("수자원", "분류"), ("수도", "분류"), ("환경", "분류"), ("경영", "분류"), ("IoT", "유형"), ("GIS", "유형"),
            ("실시간", "주기"), ("배치", "주기"), ("공개", "등급"), ("비공개", "등급"), ("센서", "소스"),
            ("ERP", "소스"), ("API", "유형"), ("CSV", "유형"), ("DB", "유형")]
    IDS["tags"] = {}
    for name, cat in tags:
        tid = uid()
        IDS["tags"][name] = tid
        s.execute(text("""INSERT INTO catalog_tag (id, tag_name, tag_category, usage_count, created_at, is_deleted)
            VALUES (:id, :n, :c, :u, :ca, false)"""),
            {"id": tid, "n": name, "c": cat, "u": random.randint(5, 100), "ca": now()})
    print(f"  catalog_tag: {len(tags)}건")

def seed_catalog_dataset_tags(s):
    tag_map = {
        "댐 수위 관측 데이터 (2026)": ["수자원", "DB", "실시간"],
        "수질 모니터링 센서 데이터": ["환경", "IoT", "센서", "실시간"],
        "상수도 배수관 GIS 데이터": ["수도", "GIS"],
        "전력 사용량 통계 (월별)": ["경영", "CSV", "배치"],
        "강수량 예측 모델 API": ["수자원", "API"],
        "하천 유량 관측 데이터": ["수자원", "DB"],
    }
    cnt = 0
    for ds_name, tag_names in tag_map.items():
        ds_id = IDS["datasets"].get(ds_name)
        if not ds_id:
            continue
        for tn in tag_names:
            tid = IDS["tags"].get(tn)
            if tid:
                s.execute(text("""INSERT INTO catalog_dataset_tag (id, dataset_id, tag_id) VALUES (:id, :d, :t)"""),
                    {"id": uid(), "d": ds_id, "t": tid})
                cnt += 1
    print(f"  catalog_dataset_tag: {cnt}건")

def seed_catalog_lineage(s):
    lineages = [
        ("IoT 센서 원시 데이터", "수질 모니터링 센서 데이터", "ETL", "수질 센서 정제 파이프라인"),
        ("댐 수위 관측 데이터 (2026)", "강수량 예측 모델 API", "TRANSFORM", "예측 모델 학습 파이프라인"),
        ("하천 유량 관측 데이터", "댐 수위 관측 데이터 (2026)", "VIEW", "수자원 통합 뷰"),
    ]
    for up, down, ltype, pipe in lineages:
        uid_up = IDS["datasets"].get(up)
        uid_down = IDS["datasets"].get(down)
        if uid_up and uid_down:
            s.execute(text("""INSERT INTO catalog_lineage (id, upstream_dataset_id, downstream_dataset_id, lineage_type, pipeline_name, created_at, is_deleted)
                VALUES (:id, :u, :d, :lt, :p, :ca, false)"""),
                {"id": uid(), "u": uid_up, "d": uid_down, "lt": ltype, "p": pipe, "ca": now()})
    print(f"  catalog_lineage: {len(lineages)}건")

def seed_catalog_search_index(s):
    for ds_name, ds_id in IDS["datasets"].items():
        s.execute(text("""INSERT INTO catalog_search_index (id, dataset_id, search_text, indexed_at)
            VALUES (:id, :d, :st, :ia)"""),
            {"id": uid(), "d": ds_id, "st": ds_name, "ia": now()})
    print(f"  catalog_search_index: {len(IDS['datasets'])}건")


# ═══════════════════════════════════════
# SA-05. 데이터수집
# ═══════════════════════════════════════

def seed_collection_strategy(s):
    strategies = [
        ("실시간 CDC 수집", "CDC", "STRUCTURED", 1), ("배치 일괄 수집", "BATCH", "STRUCTURED", 2),
        ("실시간 Kafka 스트리밍", "REALTIME", "SEMI_STRUCTURED", 1), ("파일 업로드", "FILE_UPLOAD", "UNSTRUCTURED", 3),
        ("API 폴링 수집", "BATCH", "STRUCTURED", 2), ("IoT 센서 수집", "REALTIME", "SEMI_STRUCTURED", 1),
    ]
    IDS["strategies"] = []
    for name, stype, tdt, pri in strategies:
        sid = uid()
        IDS["strategies"].append(sid)
        s.execute(text("""INSERT INTO collection_strategy (id, strategy_name, strategy_type, target_data_type, priority, is_active, created_at, is_deleted)
            VALUES (:id, :n, :st, :td, :p, true, :ca, false)"""),
            {"id": sid, "n": name, "st": stype, "td": tdt, "p": pri, "ca": now()})
    print(f"  collection_strategy: {len(strategies)}건")

def seed_collection_data_source(s):
    sources = [
        ("K-water Oracle ERP", "RDBMS", "ORACLE", "10.0.10.50", 1521, "ERPDB"),
        ("K-water 티베로 수도관리", "RDBMS", "TIBERO", "10.0.10.60", 8629, "WSDB"),
        ("IoT 센서 Kafka", "KAFKA", None, "10.0.3.10", 9092, None),
        ("기상청 공공API", "API", None, "apis.data.go.kr", 443, None),
        ("SAP HANA 경영", "RDBMS", "SAP_HANA", "10.0.10.70", 30015, "SAPDB"),
        ("PostgreSQL 분석DB", "RDBMS", "POSTGRESQL", "10.0.1.10", 5432, "analyticsdb"),
        ("GIS 파일서버", "FILE", None, "10.0.5.20", None, None),
        ("수자원공사 내부 API", "API", None, "internal-api.kwater.or.kr", 443, None),
    ]
    IDS["sources"] = []
    for name, stype, dbtype, host, port, db in sources:
        sid = uid()
        IDS["sources"].append(sid)
        s.execute(text("""INSERT INTO collection_data_source (id, source_name, source_type, db_type, connection_host, connection_port, connection_db, last_test_result, status, created_at, is_deleted)
            VALUES (:id, :n, :st, :dt, :h, :p, :db, 'SUCCESS', 'ACTIVE', :ca, false)"""),
            {"id": sid, "n": name, "st": stype, "dt": dbtype, "h": host, "p": port, "db": db, "ca": now()})
    print(f"  collection_data_source: {len(sources)}건")

def seed_collection_dataset_config(s):
    configs = [
        ("댐 수위 실시간 수집", 0, 0, "TB_DAM_LEVEL"), ("수질 센서 Kafka 수집", 2, 2, None),
        ("ERP 경영실적 배치", 4, 1, "TB_MGMT_PERF"), ("GIS 배수관 일배치", 6, 1, "TB_PIPE_GIS"),
        ("기상청 날씨 API 수집", 3, 4, None), ("수도관리 수질검사", 1, 1, "TB_WATER_QUALITY"),
    ]
    IDS["coll_configs"] = []
    for name, src_idx, strat_idx, table in configs:
        cid = uid()
        IDS["coll_configs"].append(cid)
        s.execute(text("""INSERT INTO collection_dataset_config (id, source_id, strategy_id, dataset_name, source_table, status, created_at, is_deleted)
            VALUES (:id, :si, :sti, :n, :t, 'ACTIVE', :ca, false)"""),
            {"id": cid, "si": IDS["sources"][src_idx], "sti": IDS["strategies"][strat_idx], "n": name, "t": table, "ca": now()})
    print(f"  collection_dataset_config: {len(configs)}건")

def seed_collection_schedule(s):
    scheds = [("CRON", "*/5 * * * *"), ("CRON", "0 */1 * * *"), ("CRON", "0 2 * * *"), ("CRON", "0 1 * * *"), ("CRON", "0 */6 * * *"), ("CRON", "0 3 * * *")]
    for i, (stype, cron) in enumerate(scheds):
        if i < len(IDS["coll_configs"]):
            s.execute(text("""INSERT INTO collection_schedule (id, dataset_config_id, schedule_type, schedule_cron, is_active, created_at, is_deleted)
                VALUES (:id, :dc, :st, :c, true, :ca, false)"""),
                {"id": uid(), "dc": IDS["coll_configs"][i], "st": stype, "c": cron, "ca": now()})
    print(f"  collection_schedule: {len(scheds)}건")

def seed_collection_job(s):
    statuses = ["SUCCESS", "SUCCESS", "SUCCESS", "RUNNING", "SUCCESS", "FAIL"]
    cnt = 0
    for i, cfg_id in enumerate(IDS["coll_configs"]):
        for d in range(15):
            st = random.choice(statuses)
            rows = random.randint(1000, 900000) if st != "RUNNING" else None
            s.execute(text("""INSERT INTO collection_job (id, dataset_config_id, job_status, started_at, finished_at, total_rows, success_rows, error_rows)
                VALUES (:id, :dc, :st, :sa, :fa, :tr, :sr, :er)"""),
                {"id": uid(), "dc": cfg_id, "st": st, "sa": now(days_ago=d, hours_ago=random.randint(0, 12)),
                 "fa": now(days_ago=d, hours_ago=random.randint(0, 12)) if st != "RUNNING" else None,
                 "tr": rows, "sr": int(rows * 0.99) if rows else None, "er": int(rows * 0.01) if rows else None})
            cnt += 1
    print(f"  collection_job: {cnt}건")

def seed_collection_migration(s):
    migs = [
        ("Oracle ERP 전체 마이그레이션", 0, "FULL", "COMPLETED", 45, 45),
        ("티베로 수도 증분 마이그레이션", 1, "INCREMENTAL", "COMPLETED", 12, 12),
        ("SAP HANA 경영 CDC", 4, "CDC", "RUNNING", 8, 5),
    ]
    for name, src_idx, mtype, status, total, completed in migs:
        s.execute(text("""INSERT INTO collection_migration (id, migration_name, source_id, migration_type, status, total_tables, completed_tables, started_at, created_at, is_deleted)
            VALUES (:id, :n, :si, :mt, :st, :tt, :ct, :sa, :ca, false)"""),
            {"id": uid(), "n": name, "si": IDS["sources"][src_idx], "mt": mtype, "st": status, "tt": total, "ct": completed, "sa": now(days_ago=5), "ca": now(days_ago=10)})
    print(f"  collection_migration: {len(migs)}건")

def seed_collection_external_agency(s):
    agencies = [
        ("기상청", "KMA001", "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0", "REST", "0 */3 * * *"),
        ("환경부", "ME001", "https://apis.data.go.kr/B553530/WaterQuality", "REST", "0 6 * * *"),
        ("국토교통부", "MOLIT001", "https://apis.data.go.kr/1613000/RTMSDataSvcSHRent", "REST", "0 2 * * 1"),
        ("한국수자원공사", "KWATER001", "https://data.kwater.or.kr/api", "REST", "0 */6 * * *"),
        ("한국환경공단", "KECO001", "https://apis.data.go.kr/B553305/monica", "REST", "0 4 * * *"),
    ]
    for name, code, endpoint, proto, cron in agencies:
        s.execute(text("""INSERT INTO collection_external_agency (id, agency_name, agency_code, api_endpoint, protocol, schedule_cron, status, created_at, is_deleted)
            VALUES (:id, :n, :c, :e, :p, :cr, 'ACTIVE', :ca, false)"""),
            {"id": uid(), "n": name, "c": code, "e": endpoint, "p": proto, "cr": cron, "ca": now()})
    print(f"  collection_external_agency: {len(agencies)}건")

def seed_collection_spatial_config(s):
    spatials = [
        ("상수도 배수관 GIS 수집", "GIS", "https://gis.kwater.or.kr/api/pipe", "EPSG:5186"),
        ("댐 위성 영상 수집", "SATELLITE", "https://satellite.kwater.or.kr/api", "EPSG:4326"),
        ("드론 촬영 데이터 수집", "DRONE", "sftp://drone.kwater.or.kr", "EPSG:5186"),
    ]
    for name, stype, url, coord in spatials:
        s.execute(text("""INSERT INTO collection_spatial_config (id, config_name, spatial_data_type, source_url, coordinate_system, status, created_at, is_deleted)
            VALUES (:id, :n, :st, :u, :c, 'ACTIVE', :ca, false)"""),
            {"id": uid(), "n": name, "st": stype, "u": url, "c": coord, "ca": now()})
    print(f"  collection_spatial_config: {len(spatials)}건")


# ═══════════════════════════════════════
# SA-06. 데이터정제
# ═══════════════════════════════════════

def seed_cleansing_rule(s):
    rules = [
        ("수위 데이터 이상값 제거", "RANGE", "NUMBER", "ERROR"), ("수질 NULL 보정", "NULL_FILL", "ALL", "WARNING"),
        ("배수관 좌표 정규화", "FORMAT", "STRING", "WARNING"), ("전력사용량 단위 통일", "CUSTOM", "NUMBER", "INFO"),
        ("개인정보 비식별화", "REGEX", "STRING", "ERROR"), ("센서 중복 데이터 제거", "DEDUP", "ALL", "WARNING"),
        ("날짜 형식 표준화", "FORMAT", "DATE", "WARNING"), ("코드값 유효성 검증", "RANGE", "STRING", "ERROR"),
    ]
    IDS["cleansing_rules"] = []
    for name, rtype, col_type, sev in rules:
        rid = uid()
        IDS["cleansing_rules"].append(rid)
        s.execute(text("""INSERT INTO cleansing_rule (id, rule_name, rule_type, target_column_type, severity, is_active, sort_order, created_at, is_deleted)
            VALUES (:id, :n, :rt, :ct, :s, true, :so, :ca, false)"""),
            {"id": rid, "n": name, "rt": rtype, "ct": col_type, "s": sev, "so": len(IDS["cleansing_rules"]), "ca": now()})
    print(f"  cleansing_rule: {len(rules)}건")

def seed_cleansing_job(s):
    jobs = [
        ("수위 이상값 정제", "댐 수위 관측 데이터 (2026)", "SUCCESS", 12500, 12400, 100),
        ("수질 NULL 보정", "수질 모니터링 센서 데이터", "SUCCESS", 8200, 8020, 180),
        ("배수관 좌표 정규화", "상수도 배수관 GIS 데이터", "RUNNING", 3200000, 3040000, 160000),
        ("전력 단위 통일", "전력 사용량 통계 (월별)", "SUCCESS", 15600, 15600, 0),
        ("개인정보 비식별화", "하천 유량 관측 데이터", "SUCCESS", 42000, 42000, 0),
        ("센서 중복 제거", "IoT 센서 원시 데이터", "FAIL", 1800, 1593, 207),
    ]
    IDS["cleansing_jobs"] = []
    for name, ds_name, status, total, cleansed, err in jobs:
        jid = uid()
        IDS["cleansing_jobs"].append(jid)
        ds_id = IDS["datasets"].get(ds_name)
        s.execute(text("""INSERT INTO cleansing_job (id, job_name, dataset_id, job_status, started_at, finished_at, total_rows, cleansed_rows, error_rows, created_at, is_deleted)
            VALUES (:id, :n, :di, :st, :sa, :fa, :tr, :cr, :er, :ca, false)"""),
            {"id": jid, "n": name, "di": ds_id, "st": status, "sa": now(hours_ago=random.randint(1, 48)),
             "fa": now(hours_ago=random.randint(0, 24)) if status != "RUNNING" else None, "tr": total, "cr": cleansed, "er": err, "ca": now()})
    print(f"  cleansing_job: {len(jobs)}건")

def seed_cleansing_result_detail(s):
    cnt = 0
    if IDS["cleansing_jobs"]:
        for _ in range(50):
            s.execute(text("""INSERT INTO cleansing_result_detail (id, job_id, rule_id, column_name, before_value, after_value, action_taken, row_index, processed_at)
                VALUES (:id, :ji, :ri, :cn, :bv, :av, :at, :rx, :pa)"""),
                {"id": uid(), "ji": random.choice(IDS["cleansing_jobs"]), "ri": random.choice(IDS["cleansing_rules"]),
                 "cn": random.choice(["WATER_LV", "PH", "BOD", "TEMP", "STATUS_CD"]),
                 "bv": str(random.uniform(-999, 999)), "av": str(random.uniform(0, 100)),
                 "at": random.choice(["REPLACED", "REMOVED", "FLAGGED"]), "rx": random.randint(1, 100000), "pa": now()})
            cnt += 1
    print(f"  cleansing_result_detail: {cnt}건")

def seed_anonymization_config(s):
    configs = [
        ("사용자 로그 마스킹", "MASKING"), ("이메일 가명처리", "PSEUDONYM"),
        ("전화번호 암호화", "ENCRYPTION"), ("주소 일반화", "GENERALIZATION"),
    ]
    IDS["anon_configs"] = []
    ds_keys = list(IDS["datasets"].keys())
    for name, method in configs:
        cid = uid()
        IDS["anon_configs"].append(cid)
        s.execute(text("""INSERT INTO anonymization_config (id, config_name, dataset_id, target_columns, method, is_active, created_at, is_deleted)
            VALUES (:id, :n, :di, CAST(:tc AS jsonb), :m, true, :ca, false)"""),
            {"id": cid, "n": name, "di": IDS["datasets"].get(random.choice(ds_keys)), "tc": '["NAME","EMAIL","PHONE"]', "m": method, "ca": now()})
    print(f"  anonymization_config: {len(configs)}건")

def seed_anonymization_log(s):
    cnt = 0
    for cid in IDS["anon_configs"]:
        for d in range(5):
            s.execute(text("""INSERT INTO anonymization_log (id, config_id, executed_at, total_rows, processed_rows, status)
                VALUES (:id, :ci, :ea, :tr, :pr, 'SUCCESS')"""),
                {"id": uid(), "ci": cid, "ea": now(days_ago=d), "tr": random.randint(1000, 50000), "pr": random.randint(1000, 50000)})
            cnt += 1
    print(f"  anonymization_log: {cnt}건")

def seed_transform_model(s):
    models = [
        ("수자원 통합 뷰", "JOIN", "ACTIVE"), ("수질 일평균 집계", "AGGREGATION", "ACTIVE"),
        ("GIS 좌표 변환", "MAPPING", "DRAFT"), ("경영 피벗 테이블", "PIVOT", "ACTIVE"),
    ]
    IDS["transform_models"] = []
    for name, ttype, status in models:
        mid = uid()
        IDS["transform_models"].append(mid)
        s.execute(text("""INSERT INTO transform_model (id, model_name, transform_type, status, created_at, is_deleted)
            VALUES (:id, :n, :tt, :st, :ca, false)"""),
            {"id": mid, "n": name, "tt": ttype, "st": status, "ca": now()})
    print(f"  transform_model: {len(models)}건")

def seed_transform_mapping(s):
    cnt = 0
    cols = [("MEAS_DT", "측정일시", "CAST"), ("WATER_LV", "수위_M", "ROUND"), ("DAM_CD", "댐코드", None), ("STATUS", "상태코드", "CODE_CONVERT")]
    for mid in IDS["transform_models"][:2]:
        for i, (src, tgt, func) in enumerate(cols):
            s.execute(text("""INSERT INTO transform_mapping (id, transform_model_id, source_column, target_column, transform_function, sort_order)
                VALUES (:id, :mi, :sc, :tc, :tf, :so)"""),
                {"id": uid(), "mi": mid, "sc": src, "tc": tgt, "tf": func, "so": i})
            cnt += 1
    print(f"  transform_mapping: {cnt}건")


# ═══════════════════════════════════════
# SA-07. 데이터저장
# ═══════════════════════════════════════

def seed_storage_zone(s):
    zones = [
        ("원시 데이터 영역", "RAW", "RAW", "DATA_LAKE", 2000, 1200), ("스테이징 영역", "STG", "STAGING", "RDBMS", 500, 180),
        ("운영 데이터 저장소", "ODS", "ODS", "RDBMS", 1000, 650), ("데이터 웨어하우스", "EDW", "EDW", "RDBMS", 3000, 1800),
        ("데이터 마트", "MART", "MART", "RDBMS", 500, 320), ("아카이브", "ARCH", "ARCHIVE", "OBJECT", 10000, 4500),
    ]
    IDS["zones"] = []
    for name, code, ztype, stype, max_gb, used_gb in zones:
        zid = uid()
        IDS["zones"].append(zid)
        s.execute(text("""INSERT INTO storage_zone (id, zone_name, zone_code, zone_type, storage_type, max_capacity_gb, used_capacity_gb, status, created_at, is_deleted)
            VALUES (:id, :n, :c, :zt, :st, :mg, :ug, 'ACTIVE', :ca, false)"""),
            {"id": zid, "n": name, "c": code, "zt": ztype, "st": stype, "mg": max_gb, "ug": used_gb, "ca": now()})
    print(f"  storage_zone: {len(zones)}건")

def seed_storage_highspeed_db(s):
    dbs = [("Redis 캐시 클러스터", "REDIS", "API 응답 캐시", 16, "LRU", 3600),
           ("Apache Ignite 분석", "IGNITE", "실시간 분석 메모리 DB", 64, "LFU", 86400)]
    for name, dbtype, purpose, mem, policy, ttl in dbs:
        s.execute(text("""INSERT INTO storage_highspeed_db (id, db_name, db_type, connection_config, purpose, max_memory_gb, eviction_policy, ttl_seconds, status, created_at, is_deleted)
            VALUES (:id, :n, :dt, CAST(:cc AS jsonb), :p, :m, :ep, :t, 'ACTIVE', :ca, false)"""),
            {"id": uid(), "n": name, "dt": dbtype, "cc": '{"host":"10.0.3.20","port":6379}', "p": purpose, "m": mem, "ep": policy, "t": ttl, "ca": now()})
    print(f"  storage_highspeed_db: {len(dbs)}건")

def seed_storage_unstructured(s):
    storages = [("MinIO 오브젝트 스토리지", "OBJECT_STORAGE", "datahub-objects", "/data", 10000, 3200),
                ("NAS 파일 스토리지", "NAS", None, "/nas/datahub", 5000, 1800)]
    for name, stype, bucket, path, total, used in storages:
        s.execute(text("""INSERT INTO storage_unstructured (id, storage_name, storage_type, bucket_name, base_path, total_capacity_gb, used_capacity_gb, status, created_at, is_deleted)
            VALUES (:id, :n, :st, :b, :p, :tg, :ug, 'ACTIVE', :ca, false)"""),
            {"id": uid(), "n": name, "st": stype, "b": bucket, "p": path, "tg": total, "ug": used, "ca": now()})
    print(f"  storage_unstructured: {len(storages)}건")

def seed_storage_dataset_location(s):
    cnt = 0
    for ds_name, ds_id in IDS["datasets"].items():
        if IDS["zones"]:
            s.execute(text("""INSERT INTO storage_dataset_location (id, dataset_id, zone_id, physical_location, size_bytes, row_count, last_refreshed_at)
                VALUES (:id, :di, :zi, :pl, :sz, :rc, :lr)"""),
                {"id": uid(), "di": ds_id, "zi": random.choice(IDS["zones"]), "pl": f"public.tb_{ds_name[:10].lower().replace(' ','_')}", "sz": random.randint(1000000, 50000000000), "rc": random.randint(1000, 100000000), "lr": now()})
            cnt += 1
    print(f"  storage_dataset_location: {cnt}건")


# ═══════════════════════════════════════
# SA-08. 데이터유통
# ═══════════════════════════════════════

def seed_distribution_format(s):
    formats = [("CSV", "CSV", "text/csv", ".csv"), ("JSON", "JSON", "application/json", ".json"),
               ("XML", "XML", "application/xml", ".xml"), ("PARQUET", "Apache Parquet", "application/octet-stream", ".parquet"),
               ("XLSX", "Excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xlsx")]
    for code, name, mime, ext in formats:
        s.execute(text("""INSERT INTO distribution_format (id, format_code, format_name, mime_type, file_extension, is_active)
            VALUES (:id, :c, :n, :m, :e, true)"""),
            {"id": uid(), "c": code, "n": name, "m": mime, "e": ext})
    print(f"  distribution_format: {len(formats)}건")

def seed_distribution_dataset(s):
    IDS["dist_ds"] = []
    for ds_name, ds_id in IDS["datasets"].items():
        did = uid()
        IDS["dist_ds"].append(did)
        s.execute(text("""INSERT INTO distribution_dataset (id, dataset_id, distribution_name, is_downloadable, requires_approval, view_count, download_count, status, created_at, is_deleted)
            VALUES (:id, :di, :dn, true, :ra, :vc, :dc, 'ACTIVE', :ca, false)"""),
            {"id": did, "di": ds_id, "dn": ds_name, "ra": random.random() > 0.5, "vc": random.randint(10, 500), "dc": random.randint(1, 100), "ca": now()})
    print(f"  distribution_dataset: {len(IDS['dist_ds'])}건")

def seed_distribution_config(s):
    s.execute(text("""INSERT INTO distribution_config (id, config_name, target_db_config, column_change_policy, status, created_at, is_deleted)
        VALUES (:id, '기본 유통 구성', CAST(:cc AS jsonb), 'REQUIRE_APPROVAL', 'ACTIVE', :ca, false)"""),
        {"id": uid(), "cc": '{"target":"analytics_db"}', "ca": now()})
    print(f"  distribution_config: 1건")

def seed_distribution_request(s):
    requests = [
        ("user", "DOWNLOAD", "CSV", "APPROVED", "댐 수위 데이터 분석"), ("ext_lee", "DOWNLOAD", "CSV", "APPROVED", "환경 연구"),
        ("ext_kim", "API_ACCESS", None, "APPROVED", "API 연동"), ("user", "DOWNLOAD", "JSON", "PENDING", "수질 데이터 활용"),
        ("ext_park", "DOWNLOAD", "CSV", "REJECTED", "비인가 데이터 요청"),
    ]
    IDS["dist_reqs"] = []
    ds_ids = list(IDS["datasets"].values())
    for login, rtype, fmt, status, purpose in requests:
        rid = uid()
        IDS["dist_reqs"].append(rid)
        s.execute(text("""INSERT INTO distribution_request (id, requester_id, dataset_ids, request_type, requested_format, purpose, status, approved_by, approved_at, created_at, is_deleted)
            VALUES (:id, :req, CAST(:ds AS jsonb), :rt, :f, :p, :st, :ab, :aa, :ca, false)"""),
            {"id": rid, "req": IDS["users"][login], "ds": f'["{random.choice(ds_ids)}"]', "rt": rtype, "f": fmt, "p": purpose, "st": status,
             "ab": IDS["users"]["admin"] if status in ("APPROVED", "REJECTED") else None,
             "aa": now(days_ago=1) if status in ("APPROVED", "REJECTED") else None, "ca": now(days_ago=random.randint(1, 15))})
    print(f"  distribution_request: {len(requests)}건")

def seed_distribution_download_log(s):
    cnt = 0
    for login in ["user", "ext_lee", "ext_kim", "ext_park", "manager", "lee"]:
        for d in range(10):
            if IDS["dist_ds"]:
                s.execute(text("""INSERT INTO distribution_download_log (id, user_id, dataset_id, download_format, row_count, file_size_bytes, client_ip, downloaded_at)
                    VALUES (:id, :u, :di, :f, :rc, :fs, :ip, :da)"""),
                    {"id": uid(), "u": IDS["users"][login], "di": random.choice(IDS["dist_ds"]),
                     "f": random.choice(["CSV", "JSON", "XLSX"]), "rc": random.randint(100, 1000000),
                     "fs": random.randint(10000, 500000000), "ip": f"10.10.{random.randint(1,50)}.{random.randint(1,254)}", "da": now(days_ago=d)})
                cnt += 1
    print(f"  distribution_download_log: {cnt}건")

def seed_distribution_api_endpoint(s):
    apis = [
        ("댐 수위 조회 API", "/api/v1/data/dam-level", "GET"), ("수질 데이터 조회 API", "/api/v1/data/water-quality", "GET"),
        ("유량 데이터 조회 API", "/api/v1/data/flow-rate", "GET"), ("전력통계 조회 API", "/api/v1/data/power-stats", "GET"),
        ("데이터셋 목록 API", "/api/v1/datasets", "GET"), ("데이터셋 상세 API", "/api/v1/datasets/{id}", "GET"),
        ("검색 API", "/api/v1/search", "POST"), ("다운로드 API", "/api/v1/download", "POST"),
    ]
    IDS["api_endpoints"] = []
    for name, path, method in apis:
        eid = uid()
        IDS["api_endpoints"].append(eid)
        s.execute(text("""INSERT INTO distribution_api_endpoint (id, api_name, api_path, http_method, description, rate_limit_per_min, requires_auth, version, status, created_at, is_deleted)
            VALUES (:id, :n, :p, :m, :d, 60, true, 'v1', 'ACTIVE', :ca, false)"""),
            {"id": eid, "n": name, "p": path, "m": method, "d": f"{name} 엔드포인트", "ca": now()})
    print(f"  distribution_api_endpoint: {len(apis)}건")

def seed_distribution_api_key(s):
    keys = [("admin", "관리자 API 키"), ("ext_kim", "외부 연구자 API 키"), ("ext_park", "기상청 연동 키")]
    IDS["api_keys"] = []
    for login, name in keys:
        kid = uid()
        IDS["api_keys"].append(kid)
        s.execute(text("""INSERT INTO distribution_api_key (id, user_id, api_key_hash, api_key_prefix, name, rate_limit_per_min, expires_at, is_active, created_at, is_deleted)
            VALUES (:id, :u, :h, :p, :n, 60, :ea, true, :ca, false)"""),
            {"id": kid, "u": IDS["users"][login], "h": hash_pw(uid().hex), "p": uid().hex[:8], "n": name, "ea": now() + timedelta(days=365), "ca": now()})
    print(f"  distribution_api_key: {len(keys)}건")

def seed_distribution_api_usage_log(s):
    cnt = 0
    for _ in range(100):
        s.execute(text("""INSERT INTO distribution_api_usage_log (id, api_key_id, endpoint_id, client_ip, response_status, response_time_ms, called_at)
            VALUES (:id, :ak, :ep, :ip, :rs, :rt, :ca)"""),
            {"id": uid(), "ak": random.choice(IDS["api_keys"]) if IDS["api_keys"] else None, "ep": random.choice(IDS["api_endpoints"]) if IDS["api_endpoints"] else None,
             "ip": f"10.10.{random.randint(1,50)}.{random.randint(1,254)}", "rs": random.choice([200, 200, 200, 200, 201, 400, 500]),
             "rt": random.randint(10, 2000), "ca": now(days_ago=random.randint(0, 30), hours_ago=random.randint(0, 23))})
        cnt += 1
    print(f"  distribution_api_usage_log: {cnt}건")

def seed_distribution_mcp_config(s):
    configs = [
        ("데이터허브 MCP 서버", "https://datahub.kwater.or.kr/mcp", "HTTP"),
        ("내부 분석 MCP", "stdio://datahub-analysis", "STDIO"),
    ]
    for name, url, transport in configs:
        s.execute(text("""INSERT INTO distribution_mcp_config (id, mcp_name, server_url, transport_type, status, created_at, is_deleted)
            VALUES (:id, :n, :u, :t, 'ACTIVE', :ca, false)"""),
            {"id": uid(), "n": name, "u": url, "t": transport, "ca": now()})
    print(f"  distribution_mcp_config: {len(configs)}건")

def seed_distribution_fusion_model(s):
    models = [
        ("수자원 통합 분석 모델", "JOIN", "COMPLETED"), ("환경-수질 융합 데이터", "MERGE", "IN_PROGRESS"),
        ("경영 KPI 집계 모델", "AGGREGATE", "NOT_STARTED"),
    ]
    for name, ftype, poc in models:
        s.execute(text("""INSERT INTO distribution_fusion_model (id, model_name, source_datasets, fusion_type, poc_status, status, created_at, is_deleted)
            VALUES (:id, :n, CAST(:sd AS jsonb), :ft, :ps, 'DRAFT', :ca, false)"""),
            {"id": uid(), "n": name, "sd": "[]", "ft": ftype, "ps": poc, "ca": now()})
    print(f"  distribution_fusion_model: {len(models)}건")

def seed_distribution_stats(s):
    cnt = 0
    for d in range(90):
        dt = date.today() - timedelta(days=d)
        if IDS["dist_ds"]:
            for ds_id in IDS["dist_ds"][:5]:
                s.execute(text("""INSERT INTO distribution_stats (id, stat_date, stat_type, dataset_id, view_count, download_count, api_call_count, unique_users, total_bytes_served)
                    VALUES (:id, :sd, 'DAILY', :di, :vc, :dc, :ac, :uu, :tb)"""),
                    {"id": uid(), "sd": dt, "di": ds_id, "vc": random.randint(5, 200), "dc": random.randint(0, 50),
                     "ac": random.randint(10, 500), "uu": random.randint(1, 30), "tb": random.randint(1000000, 5000000000)})
                cnt += 1
    print(f"  distribution_stats: {cnt}건")


# ═══════════════════════════════════════
# SA-09. 포털/UX
# ═══════════════════════════════════════

def seed_portal_dashboard_template(s):
    templates = [("기본 대시보드", "DEFAULT", True), ("통계 대시보드", "STATISTICS", True), ("모니터링 대시보드", "MONITORING", True)]
    for name, code, is_sys in templates:
        s.execute(text("""INSERT INTO portal_dashboard_template (id, template_name, template_code, widget_layout, is_system, created_at, is_deleted)
            VALUES (:id, :n, :c, CAST(:wl AS jsonb), :is, :ca, false)"""),
            {"id": uid(), "n": name, "c": code, "wl": '{"cols":12,"rows":8}', "is": is_sys, "ca": now()})
    print(f"  portal_dashboard_template: {len(templates)}건")

def seed_portal_dashboard_widget(s):
    widgets = [
        ("TOTAL_DATASETS", "총 데이터셋", "KPI", None), ("TODAY_COLLECTION", "오늘 수집건수", "KPI", None),
        ("TODAY_LOAD", "오늘 적재건수", "KPI", None), ("ACTIVE_USERS", "활성 사용자", "KPI", None),
        ("STORAGE_USAGE", "저장 용량", "KPI", None), ("QUALITY_SCORE", "품질 점수", "KPI", None),
        ("COLLECTION_CHART", "수집/적재 현황", "CHART", "BAR"), ("CATEGORY_CHART", "분류별 현황", "CHART", "PIE"),
        ("RECENT_DATA", "최근 등록 데이터", "TABLE", None), ("NOTICES", "공지사항", "TABLE", None),
        ("AI_SEARCH", "AI 검색", "SEARCH", None), ("DOWNLOAD_RANK", "다운로드 순위", "CHART", "BAR"),
    ]
    IDS["widgets"] = []
    for code, name, wtype, ctype in widgets:
        wid = uid()
        IDS["widgets"].append(wid)
        s.execute(text("""INSERT INTO portal_dashboard_widget (id, widget_code, widget_name, widget_type, chart_type, is_active, created_at, is_deleted)
            VALUES (:id, :c, :n, :wt, :ct, true, :ca, false)"""),
            {"id": wid, "c": code, "n": name, "wt": wtype, "ct": ctype, "ca": now()})
    print(f"  portal_dashboard_widget: {len(widgets)}건")

def seed_portal_user_dashboard(s):
    for login in ["admin", "manager", "user", "lee", "park"]:
        s.execute(text("""INSERT INTO portal_user_dashboard (id, user_id, dashboard_name, is_default, widget_layout, created_at, is_deleted)
            VALUES (:id, :u, '기본', true, CAST(:wl AS jsonb), :ca, false)"""),
            {"id": uid(), "u": IDS["users"][login], "wl": '{"widgets":[]}', "ca": now()})
    print(f"  portal_user_dashboard: 5건")

def seed_portal_visualization_chart(s):
    charts = [
        ("월별 수집 추이", "BAR", "admin"), ("수질 항목 변화", "LINE", "user"),
        ("데이터 유형 분포", "PIE", "admin"), ("수위-유량 상관관계", "SCATTER", "manager"),
        ("저수율 변화 추이", "LINE", "user"), ("부서별 API 사용량", "BAR", "admin"),
    ]
    for name, ctype, owner in charts:
        s.execute(text("""INSERT INTO portal_visualization_chart (id, chart_name, chart_type, chart_config, is_public, view_count, owner_id, created_at, is_deleted)
            VALUES (:id, :n, :ct, CAST(:cfg AS jsonb), true, :vc, :oi, :ca, false)"""),
            {"id": uid(), "n": name, "ct": ctype, "cfg": '{}', "vc": random.randint(5, 100), "oi": IDS["users"][owner], "ca": now(days_ago=random.randint(0, 10))})
    print(f"  portal_visualization_chart: {len(charts)}건")

def seed_portal_chart_template(s):
    templates = [("기본 막대 차트", "BAR"), ("기본 선 차트", "LINE"), ("기본 원형 차트", "PIE"), ("기본 산점도", "SCATTER"), ("기본 영역 차트", "LINE")]
    for name, ctype in templates:
        s.execute(text("""INSERT INTO portal_chart_template (id, template_name, chart_type, chart_config, sort_order, is_active)
            VALUES (:id, :n, :ct, CAST(:cfg AS jsonb), :so, true)"""),
            {"id": uid(), "n": name, "ct": ctype, "cfg": '{}', "so": templates.index((name, ctype))})
    print(f"  portal_chart_template: {len(templates)}건")

def seed_portal_bookmark(s):
    bookmarks = [("user", "DATASET"), ("user", "DATASET"), ("user", "DATASET"), ("manager", "DATASET"), ("lee", "CHART")]
    ds_ids = list(IDS["datasets"].values())
    cnt = 0
    for login, rtype in bookmarks:
        s.execute(text("""INSERT INTO portal_bookmark (id, user_id, resource_type, resource_id, resource_name, bookmarked_at)
            VALUES (:id, :u, :rt, :ri, :rn, :ba)"""),
            {"id": uid(), "u": IDS["users"][login], "rt": rtype, "ri": random.choice(ds_ids), "rn": "즐겨찾기 항목", "ba": now(days_ago=random.randint(0, 10))})
        cnt += 1
    print(f"  portal_bookmark: {cnt}건")

def seed_portal_recent_view(s):
    cnt = 0
    ds_names = list(IDS["datasets"].keys())
    for login in ["admin", "manager", "user", "lee", "park"]:
        for d in range(20):
            ds_name = random.choice(ds_names)
            s.execute(text("""INSERT INTO portal_recent_view (id, user_id, resource_type, resource_id, resource_name, viewed_at)
                VALUES (:id, :u, 'DATASET', :ri, :rn, :va)"""),
                {"id": uid(), "u": IDS["users"][login], "ri": IDS["datasets"][ds_name], "rn": ds_name, "va": now(days_ago=d, hours_ago=random.randint(0, 12))})
            cnt += 1
    print(f"  portal_recent_view: {cnt}건")

def seed_portal_search_history(s):
    keywords = ["수위", "수질", "댐", "유량", "전력", "GIS", "환경", "배수관", "센서", "IoT", "강수량", "모니터링"]
    cnt = 0
    for login in ["admin", "manager", "user", "lee", "park", "guest"]:
        for _ in range(10):
            s.execute(text("""INSERT INTO portal_search_history (id, user_id, search_keyword, search_type, result_count, searched_at)
                VALUES (:id, :u, :k, :st, :rc, :sa)"""),
                {"id": uid(), "u": IDS["users"][login], "k": random.choice(keywords), "st": random.choice(["KEYWORD", "AI", "FILTER"]),
                 "rc": random.randint(0, 50), "sa": now(days_ago=random.randint(0, 30))})
            cnt += 1
    print(f"  portal_search_history: {cnt}건")

def seed_portal_notification(s):
    notis = [
        ("DATA_CHANGE", "댐 수위 관측 데이터가 업데이트되었습니다", "즐겨찾기한 데이터셋이 갱신되었습니다."),
        ("QUALITY", "3월 품질 진단 결과가 등록되었습니다", "전체 품질 점수: 92.4%"),
        ("SYSTEM", "데이터허브 포털 오픈 안내", "데이터허브 포털이 정식 오픈되었습니다."),
        ("APPROVAL", "데이터 신청이 승인되었습니다", "댐 수위 관측 데이터 다운로드가 승인되었습니다."),
        ("SYSTEM", "시스템 점검 안내 (03/28 02:00~06:00)", "정기 시스템 점검이 예정되어 있습니다."),
        ("DATA_CHANGE", "신규 데이터셋이 등록되었습니다", "강수량 예측 모델 API가 등록되었습니다."),
        ("DOWNLOAD", "다운로드가 완료되었습니다", "전력 사용량 통계 CSV 파일이 준비되었습니다."),
    ]
    cnt = 0
    for login in ["admin", "manager", "user", "lee", "park"]:
        for ntype, title, msg in notis:
            s.execute(text("""INSERT INTO portal_notification (id, user_id, notification_type, title, message, is_read, created_at)
                VALUES (:id, :u, :nt, :t, :m, :ir, :ca)"""),
                {"id": uid(), "u": IDS["users"][login], "nt": ntype, "t": title, "m": msg, "ir": random.random() > 0.4, "ca": now(days_ago=random.randint(0, 10))})
            cnt += 1
    print(f"  portal_notification: {cnt}건")

def seed_portal_notification_subscription(s):
    types = ["DATA_CHANGE", "QUALITY", "SYSTEM", "APPROVAL", "DOWNLOAD"]
    cnt = 0
    for login in ["admin", "manager", "user", "lee", "park"]:
        for ntype in types:
            s.execute(text("""INSERT INTO portal_notification_subscription (id, user_id, notification_type, is_enabled, channel)
                VALUES (:id, :u, :nt, :ie, 'WEB')"""),
                {"id": uid(), "u": IDS["users"][login], "nt": ntype, "ie": random.random() > 0.3})
            cnt += 1
    print(f"  portal_notification_subscription: {cnt}건")

def seed_portal_sitemap_menu(s):
    # 대분류
    menus = [
        (None, "메인홈", "PORTAL_HOME", 1, "/portal", "DashboardOutlined", '["ALL"]', 1),
        (None, "데이터카탈로그", "PORTAL_CATALOG", 1, "/portal/catalog", "DatabaseOutlined", '["ALL"]', 2),
        (None, "데이터시각화", "PORTAL_VIS", 1, "/portal/visualization", "BarChartOutlined", '["ADMIN","MANAGER","INTERNAL"]', 3),
        (None, "데이터유통", "PORTAL_DIST", 1, "/portal/distribution", "ShareAltOutlined", '["ALL"]', 4),
        (None, "AI검색", "PORTAL_AI", 1, "/portal/ai-search", "SearchOutlined", '["ADMIN","MANAGER","INTERNAL"]', 5),
        (None, "마이페이지", "PORTAL_MY", 1, "/portal/mypage", "UserOutlined", '["ALL"]', 6),
        (None, "시스템관리", "ADMIN_SYS", 1, "/admin/system", "SettingOutlined", '["ADMIN"]', 10),
        (None, "사용자관리", "ADMIN_USER", 1, "/admin/user", "TeamOutlined", '["ADMIN"]', 11),
        (None, "데이터표준", "ADMIN_STD", 1, "/admin/standard", "BookOutlined", '["ADMIN","MANAGER"]', 12),
        (None, "데이터수집", "ADMIN_COLL", 1, "/admin/collection", "CloudDownloadOutlined", '["ADMIN","MANAGER"]', 13),
        (None, "데이터정제", "ADMIN_CLS", 1, "/admin/cleansing", "FilterOutlined", '["ADMIN","MANAGER"]', 14),
        (None, "데이터저장", "ADMIN_STOR", 1, "/admin/storage", "HddOutlined", '["ADMIN","MANAGER"]', 15),
        (None, "데이터유통", "ADMIN_DIST", 1, "/admin/distribution", "SwapOutlined", '["ADMIN","MANAGER"]', 16),
        (None, "운영관리", "ADMIN_OPS", 1, "/admin/operation", "ToolOutlined", '["ADMIN","MANAGER"]', 17),
    ]
    for parent, name, code, level, route, icon, roles, sort in menus:
        s.execute(text("""INSERT INTO portal_sitemap_menu (id, parent_id, menu_name, menu_code, menu_level, route_path, icon_name, required_roles, is_visible, sort_order, created_at, is_deleted)
            VALUES (:id, :p, :n, :c, :l, :r, :i, CAST(:ro AS jsonb), true, :so, :ca, false)"""),
            {"id": uid(), "p": parent, "n": name, "c": code, "l": level, "r": route, "i": icon, "ro": roles, "so": sort, "ca": now()})
    print(f"  portal_sitemap_menu: {len(menus)}건")


# ═══════════════════════════════════════
# SA-10. 운영/감사
# ═══════════════════════════════════════

def seed_operation_hub_stats(s):
    cnt = 0
    for d in range(90):
        dt = date.today() - timedelta(days=d)
        s.execute(text("""INSERT INTO operation_hub_stats (id, stat_date, stat_type, total_datasets, total_users, active_users, total_downloads, total_api_calls, total_storage_gb, data_quality_score, collection_success_rate)
            VALUES (:id, :sd, 'DAILY', :td, :tu, :au, :tdl, :tac, :tsg, :dqs, :csr)"""),
            {"id": uid(), "sd": dt, "td": 1247 + d, "tu": 308 + d // 3, "au": random.randint(100, 200), "tdl": random.randint(200, 500),
             "tac": random.randint(30000, 60000), "tsg": 3100 + random.randint(0, 100), "dqs": round(random.uniform(88, 96), 2), "csr": round(random.uniform(95, 99.9), 2)})
        cnt += 1
    print(f"  operation_hub_stats: {cnt}건")

def seed_operation_report_template(s):
    templates = [
        ("월간 운영 현황 리포트", "STATISTICS", "PDF"), ("데이터 품질 진단 리포트", "QUALITY", "PDF"),
        ("사용자 활동 분석 리포트", "USAGE", "EXCEL"), ("API 사용량 분석 리포트", "USAGE", "EXCEL"),
    ]
    IDS["report_templates"] = []
    for name, ttype, fmt in templates:
        tid = uid()
        IDS["report_templates"].append(tid)
        s.execute(text("""INSERT INTO operation_report_template (id, template_name, template_type, output_format, description, created_at, is_deleted)
            VALUES (:id, :n, :tt, :f, :d, :ca, false)"""),
            {"id": tid, "n": name, "tt": ttype, "f": fmt, "d": f"{name} 자동 생성 템플릿", "ca": now()})
    print(f"  operation_report_template: {len(templates)}건")

def seed_operation_report_generation(s):
    cnt = 0
    for tid in IDS["report_templates"]:
        for d in range(5):
            s.execute(text("""INSERT INTO operation_report_generation (id, template_id, report_name, output_format, file_path, file_size_bytes, generation_status, generated_by, generated_at)
                VALUES (:id, :ti, :rn, 'PDF', :fp, :fs, 'COMPLETED', :gb, :ga)"""),
                {"id": uid(), "ti": tid, "rn": f"리포트_{date.today() - timedelta(days=d*30)}", "fp": f"/reports/{uid().hex[:8]}.pdf",
                 "fs": random.randint(100000, 5000000), "gb": IDS["users"]["admin"], "ga": now(days_ago=d*30)})
            cnt += 1
    print(f"  operation_report_generation: {cnt}건")

def seed_operation_ai_query_log(s):
    queries = [
        "최근 등록된 수자원 데이터는?", "댐 수위 데이터의 컬럼 정보 알려줘", "수질 관련 공개 데이터 목록",
        "전력 사용량 데이터 다운로드 방법", "하천 유량 데이터 최신 현황", "IoT 센서 데이터 수집 상태",
        "환경영향평가 보고서 검색", "수도 관련 GIS 데이터", "경영 실적 데이터 조회", "데이터 품질 점수 확인",
    ]
    cnt = 0
    for login in ["admin", "manager", "user", "lee", "park"]:
        for _ in range(20):
            q = random.choice(queries)
            s.execute(text("""INSERT INTO operation_ai_query_log (id, user_id, query_text, query_type, response_text, model_name, token_count, response_time_ms, satisfaction_rating, queried_at)
                VALUES (:id, :u, :qt, 'NATURAL_LANGUAGE', :rt, 'claude-sonnet-4-6', :tc, :rtm, :sr, :qa)"""),
                {"id": uid(), "u": IDS["users"][login], "qt": q, "rt": f"{q}에 대한 AI 응답입니다.",
                 "tc": random.randint(100, 2000), "rtm": random.randint(500, 5000),
                 "sr": random.choice([3, 4, 4, 5, 5]), "qa": now(days_ago=random.randint(0, 30))})
            cnt += 1
    print(f"  operation_ai_query_log: {cnt}건")

def seed_operation_ai_model_config(s):
    models = [
        ("Claude Sonnet 4.6", "LLM", "CLAUDE", "https://api.anthropic.com/v1"),
        ("OpenAI GPT-4o", "LLM", "OPENAI", "https://api.openai.com/v1"),
        ("로컬 임베딩 모델", "EMBEDDING", "LOCAL", "http://10.0.6.10:8080"),
    ]
    for name, mtype, provider, url in models:
        s.execute(text("""INSERT INTO operation_ai_model_config (id, model_name, model_type, provider, endpoint_url, is_active, created_at, is_deleted)
            VALUES (:id, :n, :mt, :p, :u, true, :ca, false)"""),
            {"id": uid(), "n": name, "mt": mtype, "p": provider, "u": url, "ca": now()})
    print(f"  operation_ai_model_config: {len(models)}건")

def seed_operation_access_log(s):
    actions = ["READ", "DOWNLOAD", "API_CALL", "LOGIN", "LOGOUT", "ADMIN_ACTION"]
    resources = ["DATASET", "API", "REPORT", "SYSTEM"]
    cnt = 0
    for login in ["admin", "manager", "user", "lee", "park", "guest", "ext_kim"]:
        for d in range(15):
            for _ in range(random.randint(2, 8)):
                s.execute(text("""INSERT INTO operation_access_log (id, user_id, action, resource_type, resource_name, client_ip, request_method, request_path, response_status, result, logged_at)
                    VALUES (:id, :u, :a, :rt, :rn, :ip, :rm, :rp, :rs, :res, :la)"""),
                    {"id": uid(), "u": IDS["users"][login], "a": random.choice(actions), "rt": random.choice(resources),
                     "rn": random.choice(list(IDS["datasets"].keys())), "ip": f"10.10.{random.randint(1,50)}.{random.randint(1,254)}",
                     "rm": random.choice(["GET", "POST"]), "rp": f"/api/v1/{random.choice(['datasets', 'search', 'download', 'standards'])}",
                     "rs": random.choice([200, 200, 200, 201, 403, 500]), "res": "SUCCESS",
                     "la": now(days_ago=d, hours_ago=random.randint(0, 23))})
                cnt += 1
    print(f"  operation_access_log: {cnt}건")

def seed_operation_system_event(s):
    events = [
        ("PERFORMANCE", "Kafka 브로커 CPU 사용률 경고", "WARNING", "Kafka Cluster CPU 사용률이 78%를 초과했습니다."),
        ("ERROR", "수집 파이프라인 실패", "ERROR", "IoT 센서 데이터 수집 중 연결 타임아웃 발생"),
        ("MAINTENANCE", "정기 시스템 점검 완료", "INFO", "2026-03-28 02:00~06:00 정기점검 정상 완료"),
        ("OPTIMIZATION", "인덱스 리빌드 완료", "INFO", "std_code 테이블 인덱스 리빌드 수행 완료 (15초 소요)"),
        ("PERFORMANCE", "PostgreSQL 슬로우 쿼리 감지", "WARNING", "catalog_dataset 테이블 풀스캔 쿼리 감지 (3.2초)"),
        ("ERROR", "MinIO 디스크 사용률 70% 초과", "WARNING", "MinIO 오브젝트 스토리지 디스크 사용률 72%"),
        ("MAINTENANCE", "Alembic 마이그레이션 실행", "INFO", "88개 테이블 생성 마이그레이션 정상 완료"),
        ("OPTIMIZATION", "Redis 캐시 히트율 개선", "INFO", "캐시 TTL 조정으로 히트율 85% → 92% 향상"),
    ]
    for etype, title, sev, desc in events:
        s.execute(text("""INSERT INTO operation_system_event (id, event_type, event_source, severity, title, description, occurred_at, resolved_at)
            VALUES (:id, :et, :es, :s, :t, :d, :oa, :ra)"""),
            {"id": uid(), "et": etype, "es": "시스템 모니터링", "s": sev, "t": title, "d": desc,
             "oa": now(days_ago=random.randint(0, 15)), "ra": now(days_ago=random.randint(0, 10)) if sev != "ERROR" else None})
    print(f"  operation_system_event: {len(events)}건")


if __name__ == "__main__":
    run()
