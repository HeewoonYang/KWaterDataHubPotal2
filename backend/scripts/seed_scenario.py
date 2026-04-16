"""
프로토타입 시나리오 데이터: 스마트미터링 + RWIS
수집소스 → 데이터셋구성 → 수집작업 → 카탈로그 → 유통까지 E2E 삽입
+ 시계열 샘플 데이터 테이블 생성
"""
import uuid, json, random, math
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

engine = create_engine("postgresql+psycopg://datahub:datahub@postgres:5432/datahub")

def uid():
    return uuid.uuid4()

def now(days_ago=0, hours_ago=0, minutes_ago=0):
    return datetime.now() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)

IDS = {}

def run():
    with Session(engine) as s:
        # 1. 시계열 데이터 테이블 생성
        create_timeseries_tables(s)
        # 2. 스마트미터링 시나리오
        seed_smart_metering(s)
        # 3. RWIS 시나리오
        seed_rwis(s)
        s.commit()
        print("=== 시나리오 데이터 입력 완료 ===")


def create_timeseries_tables(s):
    """시계열 샘플 데이터 저장 테이블"""
    s.execute(text("""
        CREATE TABLE IF NOT EXISTS scenario_smart_metering (
            id SERIAL PRIMARY KEY,
            meter_id VARCHAR(20) NOT NULL,
            read_dt TIMESTAMP NOT NULL,
            usage_kwh NUMERIC(10,2),
            flow_m3 NUMERIC(10,3),
            pressure_kpa NUMERIC(8,2),
            temp_c NUMERIC(5,1),
            voltage_v NUMERIC(6,1),
            current_a NUMERIC(6,2),
            power_factor NUMERIC(4,2),
            status VARCHAR(10) DEFAULT 'NORMAL',
            created_at TIMESTAMP DEFAULT NOW()
        )
    """))
    s.execute(text("""
        CREATE TABLE IF NOT EXISTS scenario_rwis (
            id SERIAL PRIMARY KEY,
            station_id VARCHAR(20) NOT NULL,
            obs_dt TIMESTAMP NOT NULL,
            road_temp NUMERIC(5,1),
            air_temp NUMERIC(5,1),
            humidity NUMERIC(5,1),
            wind_speed NUMERIC(5,1),
            rain_yn VARCHAR(1) DEFAULT 'N',
            visibility_m INTEGER,
            road_condition VARCHAR(20) DEFAULT 'DRY',
            created_at TIMESTAMP DEFAULT NOW()
        )
    """))
    print("  [OK] 시계열 테이블 생성")


def seed_smart_metering(s):
    """스마트미터링 E2E: 소스→구성→작업→카탈로그→유통"""
    src_id = uid()
    cfg_id = uid()
    job_id = uid()
    ds_id = uid()
    dist_id = uid()

    # 수집 소스
    s.execute(text("""
        INSERT INTO collection_data_source (id, source_name, source_type, db_type, connection_host, connection_port, status, created_at)
        VALUES (:id, :name, 'KAFKA', 'KAFKA', 'kafka:9092', 9092, 'ACTIVE', :now)
        ON CONFLICT DO NOTHING
    """), {"id": str(src_id), "name": "FA망_스마트미터링_Kafka", "now": now()})

    # 데이터셋 구성
    col_mapping = json.dumps([
        {"name": "meter_id", "type": "VARCHAR(20)", "kr": "미터ID", "pk": True},
        {"name": "read_dt", "type": "TIMESTAMP", "kr": "측정일시", "pk": True},
        {"name": "usage_kwh", "type": "NUMERIC(10,2)", "kr": "전력사용량(kWh)"},
        {"name": "flow_m3", "type": "NUMERIC(10,3)", "kr": "유량(m3)"},
        {"name": "pressure_kpa", "type": "NUMERIC(8,2)", "kr": "압력(kPa)"},
        {"name": "temp_c", "type": "NUMERIC(5,1)", "kr": "온도(C)"},
        {"name": "voltage_v", "type": "NUMERIC(6,1)", "kr": "전압(V)"},
        {"name": "current_a", "type": "NUMERIC(6,2)", "kr": "전류(A)"},
        {"name": "power_factor", "type": "NUMERIC(4,2)", "kr": "역률"},
        {"name": "status", "type": "VARCHAR(10)", "kr": "상태"},
    ], ensure_ascii=False)

    s.execute(text("""
        INSERT INTO collection_dataset_config (id, dataset_name, source_id, source_table, column_mapping, target_classification_id, target_grade_id, status, created_at)
        VALUES (:id, :name, :src, 'topic_smart_metering', :cols, 1, 2, 'ACTIVE', :now)
        ON CONFLICT DO NOTHING
    """), {"id": str(cfg_id), "name": "스마트미터링_실시간_데이터", "src": str(src_id), "cols": col_mapping, "now": now()})

    # 수집 작업
    s.execute(text("""
        INSERT INTO collection_job (id, dataset_config_id, job_status, started_at, finished_at, total_rows, success_rows, error_rows)
        VALUES (:id, :cfg, 'SUCCESS', :start, :end, 10080, 10080, 0)
        ON CONFLICT DO NOTHING
    """), {"id": str(job_id), "cfg": str(cfg_id), "start": now(hours_ago=1), "end": now()})

    # 카탈로그 데이터셋
    s.execute(text("""
        INSERT INTO catalog_dataset (id, dataset_name, dataset_name_kr, description, source_system, owner_department,
            data_format, row_count, size_bytes, refresh_frequency, classification_id, grade_id, status, tags, created_at)
        VALUES (:id, 'smart_metering_realtime', :kr, :desc, 'FA망_스마트미터링', '수자원부',
            'IoT', 10080, 5242880, 'REALTIME', 1, 2, 'ACTIVE', :tags, :now)
        ON CONFLICT DO NOTHING
    """), {
        "id": str(ds_id), "kr": "스마트미터링 실시간 데이터",
        "desc": "FA망 스마트미터링 IoT 센서에서 10분 간격으로 수집되는 전력/유량/압력/온도 실시간 데이터. 광역 상수도 관망의 계측 지점별 측정값을 포함합니다.",
        "tags": json.dumps(["IoT", "스마트미터링", "실시간", "유량", "전력"]), "now": now()
    })

    # 카탈로그 컬럼
    cols = [
        ("meter_id", "미터ID", "VARCHAR", 20, True, False),
        ("read_dt", "측정일시", "TIMESTAMP", None, True, False),
        ("usage_kwh", "전력사용량(kWh)", "NUMERIC", 10, False, True),
        ("flow_m3", "유량(m3)", "NUMERIC", 10, False, True),
        ("pressure_kpa", "압력(kPa)", "NUMERIC", 8, False, True),
        ("temp_c", "온도(C)", "NUMERIC", 5, False, True),
        ("voltage_v", "전압(V)", "NUMERIC", 6, False, True),
        ("current_a", "전류(A)", "NUMERIC", 6, False, True),
        ("power_factor", "역률", "NUMERIC", 4, False, True),
        ("status", "상태", "VARCHAR", 10, False, True),
    ]
    for i, (name, kr, dtype, length, pk, nullable) in enumerate(cols):
        s.execute(text("""
            INSERT INTO catalog_column (id, dataset_id, column_name, column_name_kr, data_type, length, is_pk, is_nullable, sort_order)
            VALUES (:id, :ds, :name, :kr, :dtype, :len, :pk, :null, :sort)
            ON CONFLICT DO NOTHING
        """), {"id": str(uid()), "ds": str(ds_id), "name": name, "kr": kr, "dtype": dtype,
               "len": length, "pk": pk, "null": nullable, "sort": i})

    # 유통 등록
    s.execute(text("""
        INSERT INTO distribution_dataset (id, dataset_id, distribution_name, classification_id, grade_id,
            is_downloadable, allowed_formats, requires_approval, status, created_at)
        VALUES (:id, :ds, :name, 1, 2, true, :fmts, false, 'ACTIVE', :now)
        ON CONFLICT DO NOTHING
    """), {"id": str(dist_id), "ds": str(ds_id), "name": "스마트미터링 실시간 데이터",
           "fmts": json.dumps(["CSV", "JSON"]), "now": now()})

    # 시계열 데이터 (7일, 10분간격 = 1,008건 x 5미터)
    meters = ["MTR-G81-001", "MTR-G81-002", "MTR-SH-001", "MTR-BW-001", "MTR-AY-001"]
    batch = []
    for m_idx, meter in enumerate(meters):
        for i in range(1008):
            dt = now(minutes_ago=i*10)
            hour = dt.hour
            base_kwh = 15 + 10 * math.sin(hour / 24 * 2 * math.pi) + random.uniform(-2, 2)
            batch.append({
                "meter_id": meter, "read_dt": dt,
                "usage_kwh": round(max(0, base_kwh), 2),
                "flow_m3": round(random.uniform(0.5, 5.0), 3),
                "pressure_kpa": round(random.uniform(250, 450), 2),
                "temp_c": round(random.uniform(8, 25), 1),
                "voltage_v": round(random.uniform(218, 222), 1),
                "current_a": round(random.uniform(5, 30), 2),
                "power_factor": round(random.uniform(0.85, 0.99), 2),
                "status": "NORMAL" if random.random() > 0.02 else "WARNING",
            })

    for row in batch:
        s.execute(text("""
            INSERT INTO scenario_smart_metering (meter_id, read_dt, usage_kwh, flow_m3, pressure_kpa, temp_c, voltage_v, current_a, power_factor, status)
            VALUES (:meter_id, :read_dt, :usage_kwh, :flow_m3, :pressure_kpa, :temp_c, :voltage_v, :current_a, :power_factor, :status)
        """), row)

    IDS["smart_dataset"] = ds_id
    print(f"  [OK] 스마트미터링: {len(batch)}건 시계열 데이터")


def seed_rwis(s):
    """RWIS E2E: 소스→구성→작업→카탈로그→유통"""
    src_id = uid()
    cfg_id = uid()
    job_id = uid()
    ds_id = uid()
    dist_id = uid()

    # 수집 소스 (기상청 API)
    s.execute(text("""
        INSERT INTO collection_data_source (id, source_name, source_type, connection_host, status, created_at)
        VALUES (:id, :name, 'API', 'https://apihub.kma.go.kr', 'ACTIVE', :now)
        ON CONFLICT DO NOTHING
    """), {"id": str(src_id), "name": "DMZ망_기상청_RWIS_API", "now": now()})

    col_mapping = json.dumps([
        {"name": "station_id", "type": "VARCHAR(20)", "kr": "관측소ID", "pk": True},
        {"name": "obs_dt", "type": "TIMESTAMP", "kr": "관측일시", "pk": True},
        {"name": "road_temp", "type": "NUMERIC(5,1)", "kr": "노면온도(C)"},
        {"name": "air_temp", "type": "NUMERIC(5,1)", "kr": "기온(C)"},
        {"name": "humidity", "type": "NUMERIC(5,1)", "kr": "습도(%)"},
        {"name": "wind_speed", "type": "NUMERIC(5,1)", "kr": "풍속(m/s)"},
        {"name": "rain_yn", "type": "VARCHAR(1)", "kr": "강우여부"},
        {"name": "visibility_m", "type": "INTEGER", "kr": "시정(m)"},
    ], ensure_ascii=False)

    s.execute(text("""
        INSERT INTO collection_dataset_config (id, dataset_name, source_id, source_table, column_mapping, target_classification_id, target_grade_id, status, created_at)
        VALUES (:id, :name, :src, 'api/rwis/observations', :cols, 1, 3, 'ACTIVE', :now)
        ON CONFLICT DO NOTHING
    """), {"id": str(cfg_id), "name": "RWIS_도로기상_관측데이터", "src": str(src_id), "cols": col_mapping, "now": now()})

    s.execute(text("""
        INSERT INTO collection_job (id, dataset_config_id, job_status, started_at, finished_at, total_rows, success_rows, error_rows)
        VALUES (:id, :cfg, 'SUCCESS', :start, :end, 5040, 5040, 0)
        ON CONFLICT DO NOTHING
    """), {"id": str(job_id), "cfg": str(cfg_id), "start": now(hours_ago=2), "end": now(hours_ago=1)})

    s.execute(text("""
        INSERT INTO catalog_dataset (id, dataset_name, dataset_name_kr, description, source_system, owner_department,
            data_format, row_count, size_bytes, refresh_frequency, classification_id, grade_id, status, tags, created_at)
        VALUES (:id, 'rwis_road_weather', :kr, :desc, 'DMZ망_기상청', '수자원부',
            'API', 5040, 2621440, 'HOURLY', 1, 3, 'ACTIVE', :tags, :now)
        ON CONFLICT DO NOTHING
    """), {
        "id": str(ds_id), "kr": "RWIS 도로기상 관측 데이터",
        "desc": "기상청 도로기상관측시스템(RWIS)에서 수집되는 도로 노면온도, 기온, 습도, 풍속, 강우, 시정 데이터. DMZ망 API 연계로 1시간 간격 수집.",
        "tags": json.dumps(["RWIS", "기상", "도로", "API", "공개데이터"]), "now": now()
    })

    cols = [
        ("station_id", "관측소ID", "VARCHAR", 20, True, False),
        ("obs_dt", "관측일시", "TIMESTAMP", None, True, False),
        ("road_temp", "노면온도(C)", "NUMERIC", 5, False, True),
        ("air_temp", "기온(C)", "NUMERIC", 5, False, True),
        ("humidity", "습도(%)", "NUMERIC", 5, False, True),
        ("wind_speed", "풍속(m/s)", "NUMERIC", 5, False, True),
        ("rain_yn", "강우여부", "VARCHAR", 1, False, True),
        ("visibility_m", "시정(m)", "INTEGER", None, False, True),
    ]
    for i, (name, kr, dtype, length, pk, nullable) in enumerate(cols):
        s.execute(text("""
            INSERT INTO catalog_column (id, dataset_id, column_name, column_name_kr, data_type, length, is_pk, is_nullable, sort_order)
            VALUES (:id, :ds, :name, :kr, :dtype, :len, :pk, :null, :sort)
            ON CONFLICT DO NOTHING
        """), {"id": str(uid()), "ds": str(ds_id), "name": name, "kr": kr, "dtype": dtype,
               "len": length, "pk": pk, "null": nullable, "sort": i})

    s.execute(text("""
        INSERT INTO distribution_dataset (id, dataset_id, distribution_name, classification_id, grade_id,
            is_downloadable, allowed_formats, requires_approval, status, created_at)
        VALUES (:id, :ds, :name, 1, 3, true, :fmts, false, 'ACTIVE', :now)
        ON CONFLICT DO NOTHING
    """), {"id": str(dist_id), "ds": str(ds_id), "name": "RWIS 도로기상 관측 데이터",
           "fmts": json.dumps(["CSV", "JSON", "API"]), "now": now()})

    # 시계열 데이터 (7일, 10분간격 = 1,008건 x 5관측소)
    stations = ["RWIS-01-서울", "RWIS-02-대전", "RWIS-03-대구", "RWIS-04-부산", "RWIS-05-광주"]
    batch = []
    for st in stations:
        for i in range(1008):
            dt = now(minutes_ago=i*10)
            hour = dt.hour
            base_temp = 12 + 8 * math.sin((hour - 6) / 24 * 2 * math.pi) + random.uniform(-2, 2)
            rain = "Y" if random.random() < 0.1 else "N"
            batch.append({
                "station_id": st, "obs_dt": dt,
                "road_temp": round(base_temp + random.uniform(-3, 5), 1),
                "air_temp": round(base_temp, 1),
                "humidity": round(random.uniform(30, 95), 1),
                "wind_speed": round(random.uniform(0, 15), 1),
                "rain_yn": rain,
                "visibility_m": random.randint(200, 10000) if rain == "Y" else random.randint(5000, 20000),
                "road_condition": "WET" if rain == "Y" else "DRY",
            })

    for row in batch:
        s.execute(text("""
            INSERT INTO scenario_rwis (station_id, obs_dt, road_temp, air_temp, humidity, wind_speed, rain_yn, visibility_m, road_condition)
            VALUES (:station_id, :obs_dt, :road_temp, :air_temp, :humidity, :wind_speed, :rain_yn, :visibility_m, :road_condition)
        """), row)

    IDS["rwis_dataset"] = ds_id
    print(f"  [OK] RWIS: {len(batch)}건 시계열 데이터")


if __name__ == "__main__":
    run()
