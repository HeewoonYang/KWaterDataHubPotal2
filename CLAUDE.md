# K-water 데이터허브 포털 프로젝트

## 프로젝트 개요
- K-water 클라우드 데이터 에코시스템의 데이터허브 포털 웹 화면
- Frontend: Vue 3 (Composition API + TypeScript)
- Backend: Python (FastAPI)

## 시스템 아키텍처 범위 (이 범위를 벗어나는 기능은 구현하지 않는다)

```
┌─ Physical 계층 (데이터 원천) ─────────────────────────────────────┐
│  RDBMS / NoSQL / Cloud / Kafka·실시간IoT / 문서·매뉴얼(표준)      │
├─────────────────────────────────────────────────────────────────────┤
│  AI DB Automation          Metadata Manager       Data Integration │
│  ├ Multi Data 연결         ├ 데이터카탈로그/검색/표준  ├ In-Database ML   │
│  ├ 메타데이터 증강         └ 데이터계보/거버넌스      ├ ETL/AI Model     │
│  ├ 데이터 그래프                                    └ MLOps(AutoML)   │
│  └ 데이터 온톨로지 생성                                              │
├─ Domain 계층 ───────────────────────────────────────────────────────┤
│  Ontology Manager          NLQL (Text-to-SQL)      Data Hub 저장소  │
│  ├ 추출/생성               ├ T2SQL Agent            ├ 수집DB          │
│  ├ 지식그래프              ├ sLLM / 상용LLM          └ 분석DB          │
│  ├ 편집/관리               └ VLM                                     │
│  └ DataSource 연결         [Graph DB]  [GPU DB]                      │
├─ Dynamic 계층 ──────────────────────────────────────────────────────┤
│  OLAP/Mart    RCA & What-If    Data Event         Agent Builder     │
│  ├ 큐브/피봇   ├ 인과관계       ├ 감시/알람/모니터링  ├ 감시/알람       │
│  └ Mart        └ 시뮬레이션     └ SOP               ├ Agentic AI     │
│                                                    └ Physical AI    │
│                    AI Application Builder              (Digital Twin)│
├─ Application 계층 ──────────────────────────────────────────────────┤
│  AI 허브(데이터허브)포털     App Market              연계 서비스      │
│  ├ 종합대시보드             ├ 제조/금융 App          ├ AI API / MCP   │
│  ├ 검색포털                ├ 물류/수자원 App        ├ DT API / A2A   │
│  ├ 기업서비스              └                       └                │
│  ├ 인증 / API관리                                                   │
│  └ 기업협력                                                         │
├─ 보안 계층 (좌측) ──────────────────────────────────────────────────┤
│  인증/인가(SSO/RBAC) / 데이터보안(암호화/마스킹)                      │
│  네트워크보안(WAF/VPN) / 규정준수(감사/GDPR)                          │
├─ 모니터링 & 관제 (우측, Ops) ───────────────────────────────────────┤
│  시스템 모니터링(Infra/Resource) / App 모니터링(APM/Log)              │
│  보안 모니터링(SIEM/Threat) / Biz 모니터링(KPI/Alarm)                │
└─────────────────────────────────────────────────────────────────────┘
```

**본 포털이 담당하는 범위:**

1. **Application 계층 (직접 구현)**
   - 종합대시보드, 검색포털, 데이터카탈로그, 지식그래프/온톨로지, 데이터리니지
   - 데이터 표준/품질/분류 관리 (Metadata Manager 연동)
   - 데이터 수집/정제/저장/유통 관리 UI (Data Integration 설정)
   - 사용자/역할/접근제어 관리, 감사 로그
   - 실시간 모니터링 (RWIS/HDAPS/GIOS/스마트미터링 뷰)
   - AI 검색 (NLQL 연동 UI)

2. **각 계층의 관리/모니터링 UI (포털에서 제공)**
   - 연계 서비스 관리: AI API / MCP / DT API / A2A 연동 현황 조회, 설정, 상태 모니터링
   - 온톨로지 매니저 모니터링: Graph DB 상태, 클래스/속성/관계 현황, 동기화 이력
   - App 모니터링: APM 현황 조회, API 호출 로그, 에러 로그, 응답시간 대시보드
   - 보안 모니터링: 접근 감사 로그, 비정상 접근 탐지 현황, 보안 이벤트 조회
   - 시스템 모니터링: 인프라 상태(서버/DB/Redis 등) 헬스체크, 리소스 사용률 조회
   - Data Event 모니터링: 데이터 이벤트 감시/알람 현황, SOP 연동 상태

3. **보안 계층 관리 UI**
   - 인증/인가 설정 (SSO/RBAC 관리)
   - 데이터 보안 정책 (암호화/마스킹/비식별화 설정)
   - 감사/규정준수 리포트

**본 포털이 담당하지 않는 범위 (엔진/런타임 자체 구현 금지):**
- Physical 계층 엔진: Kafka 클러스터 운영, DB 엔진 설치, 클라우드 인프라 프로비저닝
- Domain 계층 엔진: Graph DB(Neo4j) 코어, GPU DB 코어, LLM 모델 학습/파인튜닝/서빙
- Dynamic 계층 엔진: OLAP 큐브 엔진, RCA 시뮬레이션 코어, Agent Builder 런타임 코어
- App Market: 제조/금융/물류/수자원 개별 App (별도 프로젝트)
- 모니터링 Ops 도구 자체: Grafana/Prometheus/SIEM 도구 설치 및 운영 (단, **조회 UI**는 포털에서 제공)

## 핵심 규칙

### 문서 관리
- 모든 생성되는 문서는 `docs/` 폴더에 저장한다.
- PRD(`docs/PRD_데이터허브포털.md`), TRD(`docs/TRD_데이터허브포털.md`) 문서는 포털이 업데이트될 때마다 항상 최신의 내용으로 업데이트한다.
- PRD/TRD 수정 시 변경이 필요한 섹션만 찾아서 부분 수정한다. 전체를 다시 작성하지 않는다.

### 디자인 기준
- 일반 사용자 포털: `index.html` 디자인 (상단 GNB + 서브탭 구조)
- 관리자 화면: `kwater_portal.html` 디자인 (좌측 Accordion 사이드바 + 상단 GNB)
- 정의된 디자인을 준수하고, 정의되지 않은 디자인의 경우 최대한 비슷하게 적용한다.
- **아이콘**: 모든 아이콘은 `@ant-design/icons-vue` (Ant Design Icons)만 사용한다. 이모지 및 다른 아이콘 라이브러리 사용 금지.
- **그리드 엑셀 다운로드**: 모든 AG Grid 상단에 텍스트 버튼 대신 `FileExcelOutlined` 아이콘 버튼으로 표시한다.
- **반응형 웹**: PC와 태블릿 해상도에 대응하는 반응형으로 구현한다. 모바일은 지원 대상에서 제외한다.
  - PC: 1280px 이상 (기준 해상도)
  - 태블릿: 768px ~ 1279px
  - 768px 미만(모바일)은 고려하지 않는다.

### 백엔드 미구현 화면 표시 규칙
- 백엔드 API가 연동되지 않고 프론트엔드 하드코딩/mock 데이터만 사용하는 화면은 **제목에 `*`를 붙여** 구분한다.
- 예: `온톨로지 관리*`, `HDAPS 수력발전 모니터링*`
- 백엔드 API가 실제 연동(DB 조회/저장 동작 확인)되면 해당 화면의 `<h2>` 제목에서 `*`를 제거하고, 위 목록에서도 삭제한다.
- 현재 `*` 표시 화면 목록:
  - `지식그래프 / 온톨로지*` — Canvas 프론트 전용
  - `온톨로지 관리*` — 클래스/속성/Cypher 전체 하드코딩
  - ~~`데이터 리니지(계보)*`~~ — **DB 연동 완료 (2026-03-31)**: catalog_lineage 테이블 기반 18노드/20엣지 그래프
  - `RWIS 모니터링*` — 측정 서비스 하드코딩
  - `HDAPS 수력발전 모니터링*` — 전체 하드코딩
  - `GIOS 지하수정보 모니터링*` — 전체 하드코딩
  - `스마트미터링 모니터링*` — 전체 하드코딩
  - `위젯 관리*` — 전체 하드코딩
  - `도메인 수집현황*` — 도메인별 테이블/컬럼 수집 설정 mock

  - `온톨로지 메타 증강*` — DDL/프로시저/문서 추출 mock
  - `비정형 문서 인제스트*` — 매뉴얼/절차서/연보/지침 mock
  - `데이터패브릭 현황*` — NL쿼리/T2SQL/GPU DB 현황 mock
  - `LLM/T2SQL 설정*` — LLM 모델 설정 mock
  - `GPU DB 데이터셋*` — GPU DB 데이터셋 라이프사이클 mock
  - `MindsDB 연동*` — MindsDB 예측 모델 mock
  - `분석DB 데이터셋*` — 분석DB 승격 데이터셋 mock
  - `라이프사이클 정책*` — GPU/분석DB 라이프사이클 정책 mock

### 작업 실행
- 프롬프트 질의 실행 시 한번에 실행이 불가할 경우 계획을 세워 분할 후 순차 실행한다.
- **코드 수정 완료 후 항상 `docker compose up -d --build` 로 Docker 이미지를 재빌드하여 반영한다.** (수정 후 빌드 누락 금지)
- **메뉴 변경 시 반드시 동기화**: router/index.ts, PortalLayout.vue(GNB+서브메뉴맵+dashboardPaths), SiteMap.vue, CLAUDE.md 모두 갱신한다.
- `규칙(...)` 형식의 프롬프트가 주어지면, 괄호 안의 내용을 CLAUDE.md, PRD, TRD에 모두 반영한다.

### 배포/런타임 전제 (K8s First)
- **본 포털은 Kubernetes(`datahub` 네임스페이스) 위에서 구동되는 것을 전제로 설계·구현한다.** Docker Compose는 로컬 개발 편의용일 뿐, 모든 설계 결정은 K8s 프로덕션 배포를 1차 기준으로 한다.
- 12-factor / Cloud Native 원칙을 준수한다. 아래 원칙을 위반하는 코드는 받지 않는다:
  1. **Stateless 컨테이너**: 로컬 파일시스템·프로세스 메모리에 세션·캐시·업로드 파일을 보관하지 않는다. 파일 저장은 반드시 오브젝트 스토리지(MinIO/S3), 캐시/세션은 Redis, 영속 데이터는 Postgres를 사용한다. `/app/uploads/` 같은 로컬 디렉토리 쓰기 신규 코드 금지.
  2. **설정은 환경변수로 주입**: 비밀/엔드포인트/호스트/플래그는 전부 env (ConfigMap/Secret) 에서 읽는다. 코드나 이미지에 하드코딩 금지. Pydantic `Settings`를 통해 로드한다. 필수값(JWT_SECRET_KEY, DB/Redis/Object Storage 자격증명)은 기본값 없이 미지정 시 부팅 실패하게 둔다.
  3. **멀티 레플리카 친화**: 모든 백엔드 기능은 backend pod가 2개 이상일 때도 정상 동작해야 한다(Sticky session 금지, 인메모리 락·카운터 금지). 잡·스케줄은 Celery + Redis 브로커로 위임한다.
  4. **Probe 분리**: 헬스체크는 `/livez`(프로세스 생존), `/readyz`(DB `SELECT 1` + Redis `PING` + 필수 의존성 검증) 를 분리해 제공한다. 새 API를 추가할 때 의존성이 늘면 `/readyz`에도 반영한다.
  5. **Graceful shutdown**: FastAPI `lifespan`에서 DB engine dispose, Redis/httpx 클라이언트 close를 수행한다. 장시간 작업은 SIGTERM에서 취소·재스케줄되도록 구현한다.
  6. **구조화 로깅**: 로그는 stdout에 JSON으로 출력하고 `X-Request-ID`를 correlation id로 전파한다. 파일 로거·print 금지.
  7. **관찰 가능성 hook**: 신규 외부 호출(HTTP/DB/Redis/Celery task)은 OpenTelemetry 자동계측 또는 Prometheus 메트릭에 포함될 수 있도록 표준 클라이언트(httpx, SQLAlchemy, celery)를 통해 호출한다. 커스텀 소켓·스레드 금지.
- **컨테이너 이미지 규칙**:
  - Dockerfile은 multi-stage 빌드, non-root 유저(`USER appuser`), `HEALTHCHECK` 포함을 기본으로 한다.
  - `--reload` 등 개발 옵션은 이미지 기본 `CMD`에 포함하지 않는다. 로컬 핫리로드가 필요하면 `docker-compose.yml`의 `command:` 로 오버라이드한다.
  - 이미지 태그는 `:latest` 금지. 커밋 해시 또는 `vX.Y.Z` 불변 태그를 사용한다.
- **K8s 매니페스트 규칙**:
  - 새 Deployment/StatefulSet은 반드시 다음을 포함한다: `resources.requests/limits`, `readinessProbe` + `livenessProbe` + `startupProbe`, `securityContext: {runAsNonRoot: true, allowPrivilegeEscalation: false}`, `terminationGracePeriodSeconds: 45` 이상, `preStop` 훅.
  - 복수 레플리카가 가능한 워크로드는 `PodDisruptionBudget`, `topologySpreadConstraints`/`podAntiAffinity`를 함께 추가한다.
  - 평문 Secret 값을 `k8s/secret.yaml`에 커밋하지 않는다. Sealed Secrets 또는 External Secrets Operator를 사용하고, 저장소에는 `<REDACTED>` 플레이스홀더만 남긴다.
  - 신규 기능이 새로운 환경 변수를 요구하면 `backend/app/config.py`, `.env.example`, `k8s/configmap.yaml`(또는 `secret.yaml`), `docker-compose.yml`을 **모두** 동기화한다.
- **HPA/스케일링**: API(backend)는 CPU 기반 HPA, Celery worker는 Redis 큐 길이(KEDA) 기반 스케일을 기본 전략으로 한다. 새 워커 타입을 추가하면 해당 HPA/Scaler 매니페스트도 같이 추가한다.
- **파일·스토리지**: 업로드/다운로드는 `backend/app/core/object_storage.py` 추상화(`object_storage.put_object`, `get_object`, `stream_object`, `delete_object`)만 사용한다. `open(path, "wb")`로 업로드 파일을 로컬 디스크에 쓰는 신규 코드는 금지한다.
- **마이그레이션**: 스키마 변경은 Alembic에서 관리하고, K8s에는 `Job`/`initContainer`로 `alembic upgrade head`가 자동 적용되는 경로를 유지한다.
- **CORS/네트워크**: 운영 CORS 허용 도메인을 ConfigMap에 명시한다. `CORS_ORIGINS=["*"]` 형태는 개발 환경에만 허용한다.

### 폐쇄망(Air-Gap) 이전 전제
- **본 포털은 인터넷망에서 개발 후 수공 폐쇄망 K8s 환경으로 반복 이전되는 것을 전제로 설계·구현한다.** 모든 신규 코드는 폐쇄망에서도 수정 없이 동작해야 한다.
- **외부 URL 하드코딩 절대 금지**: 서비스 코드(`backend/app/services/`, 라우터, 스키마 등)에 외부 도메인 URL을 문자열 리터럴로 작성하지 않는다. 반드시 `backend/app/config.py` 에 환경변수로 선언하고 `settings.XXX` 로 참조한다.
  - 예시(금지): `endpoint="https://api.kwater.or.kr/..."`
  - 예시(허용): `endpoint=settings.DISTRIBUTION_API_ENDPOINT`
  - 신규 환경변수 추가 시 **4곳 동시 갱신**: `backend/app/config.py` + `.env.example` + `k8s/configmap.yaml`(또는 `secret.yaml`) + `docker-compose.yml`
- **외부 CDN/스크립트 의존 금지**: 프론트/백엔드 어느 쪽이든 외부 CDN(jsdelivr, unpkg, Google Fonts 등)을 런타임에 로드하지 않는다.
  - FastAPI Swagger UI 는 운영(`DEBUG=false`)에서 `backend/app/static/` 의 로컬 번들로 서빙한다 (`main.py` custom `/docs`, `/redoc`).
  - 신규 번들이 필요하면 `backend/app/static/` 에 파일을 추가하고 import.sh 가 배치하도록 한다.
- **빌드 시 외부 다운로드 우회 가능하게 작성**: Dockerfile에서 `curl`/`wget`으로 외부 파일을 받는 경우, **반드시 로컬 vendor 파일 우선** → 없으면 원격 다운로드 fallback 패턴으로 작성한다.
  - 예시: Oracle Instant Client — `backend/vendor/*.zip` 존재 시 복사, 없으면 curl 다운로드 ([Dockerfile](backend/Dockerfile) 참조)
  - npm/pip 등 신규 외부 아티팩트 도입 시 동일 패턴 적용
- **Docker 이미지 외부 레지스트리 참조 최소화**: 신규 이미지(postgres, redis, minio, kafka, neo4j 등) 추가 시 `docker-compose.yml` 과 `k8s/*.yaml` 양쪽에 이미지명을 명시하고, 이전 스크립트(`scripts/airgap-export.sh`)의 `INFRA_IMAGES` 배열에 추가한다.
- **이전 자동화 스크립트 유지**: 폐쇄망 이전은 다음 2개 스크립트로 수행한다. 새로운 의존성/이미지/정적파일이 생기면 **반드시 스크립트도 함께 갱신**한다.
  - [scripts/airgap-export.sh](scripts/airgap-export.sh) — 인터넷망에서 1회 실행: 이미지 save + 정적파일 + vendor 수집 → `tar.gz` 패키지 생성
  - [scripts/airgap-patch-k8s.sh](scripts/airgap-patch-k8s.sh) — 폐쇄망에서 1회 실행: K8s yaml 의 이미지 레지스트리·도메인·TLS issuer 일괄 치환
- **폐쇄망 이전 대상 환경변수 (ConfigMap에서 오버라이드)**:
  - `DATABASE_URL` / `DATABASE_URL_SYNC` — 수공 내부 PostgreSQL
  - `REDIS_URL` — 내부 Redis
  - `OBJECT_STORAGE_ENDPOINT` — 내부 MinIO/S3
  - `CORS_ORIGINS` — 폐쇄망 도메인만 허용 (와일드카드 금지)
  - `SAML_SP_ENTITY_ID` / `SAML_SP_ACS_URL` / `SAML_IDP_ENTITY_ID` / `SAML_IDP_SSO_URL` — 내부 IdP
  - `ERP_API_URL` / `ERP_API_KEY` — 내부 ERP
  - `DISTRIBUTION_API_ENDPOINT` — 내부 유통 API
  - `OPENMETADATA_URL` — 내부 OpenMetadata (미사용 시 빈 값)
- **폐쇄망 K8s 매니페스트 규칙**:
  - `k8s/ingress.yaml` 의 `cert-manager.io/cluster-issuer` 는 인터넷망 기본값 `letsencrypt-prod` 를 유지하되, 폐쇄망 배포 시 `airgap-patch-k8s.sh` 로 내부 CA ClusterIssuer 로 치환한다.
  - K8s 이미지는 `registry.kwater.or.kr/...` 형태의 내부 레지스트리 경로를 기본으로 하고, 필요 시 `airgap-patch-k8s.sh --registry <주소>` 로 실제 주소를 주입한다.
  - `imagePullSecrets` 는 폐쇄망 레지스트리가 인증을 요구할 때만 수동 추가한다.
- **로컬 파일시스템 쓰기 금지는 폐쇄망에서도 동일**: 업로드/캐시/세션은 전부 MinIO/Redis 로 간다. 폐쇄망에서도 MinIO 는 `k8s/minio.yaml` 로 함께 배포된다.

### 요구사항 준수
- 요구사항이 빠짐없이 적용되어야 한다. (기능, 비기능 모두)
- 기능 요구사항: `REQ-DHUB-ALL-MERGED.md`, `데이터허브포털_메뉴구성서_v5_전체요구사항.xlsx`
- 비기능 요구사항: `KWDP-SD-AN-02-요구사항추적표-v0.83.xlsx` (REQ-SIR/DAR/PER/TER/SER/COR)
- 원본 요구사항 문서 경로: `D:\00_수공프로젝트\20260325_데이터허브포털 구현\`

## 메뉴 구성 (10개 대분류, 웹 화면 34개+)
- 시스템관리, 사용자관리, 포털, 데이터표준, 데이터수집, 데이터정제, 데이터저장, 데이터유통, FA망이전, 운영관리
- 상세 메뉴 구성은 `docs/PRD_데이터허브포털.md` 참조

### 사용자 포털 GNB 메뉴 명칭
- **대시보드** (구: 메인홈) → 서브메뉴: 대시보드, 위젯 설정, 시각화 갤러리 설정, 위젯 관리, 갤러리 콘텐츠 관리
- 데이터카탈로그 → 서브메뉴: 데이터 카탈로그, 데이터 리니지, 데이터 장바구니
- **실시간모니터링** → 서브메뉴: RWIS, HDAPS, GIOS, Smart Metering
- 데이터유통 → 서브메뉴: 유통 데이터 목록, 데이터 신청, 데이터 다운로드
- AI검색
- 마이페이지 → 서브메뉴: 내 프로필, 내 데이터, 알림 설정
- 게시판: 공지사항, 질의응답, FAQ (/portal/board/*)
- **GNB에서 '메인홈'이 아닌 '대시보드'로 표기** (관련 사이트맵 동기화 필수)

## 기술 스택
- Frontend: Vue 3, Vite, Vue Router, Pinia, Axios, ECharts, AG Grid, Element Plus, @ant-design/icons-vue
- Backend: FastAPI, SQLAlchemy, Alembic, Celery, Redis
- DB: PostgreSQL, OpenMetadata 연동
- 메시징: Kafka
- 배포: Docker, Kubernetes, Nginx

## DB 표준화 규칙 (「공공기관 데이터베이스 표준화 지침」 행안부고시 제2023-18호 준수)

### 모델 파일 위치
- `backend/app/models/` 하위 도메인별 분리 (system, user, standard, catalog, collection, cleansing, storage, distribution, portal, operation, board, classification, meta_model, quality, audit)
- 공통 믹스인: `backend/app/models/base.py` → `AuditMixin` (created_by, created_at, updated_by, updated_at, is_deleted)

### 한글 메타데이터 필수
- **모든 테이블**: `__table_args__`에 `comment="한글테이블명"` 필수
- **모든 컬럼**: `Column(..., comment="한글컬럼설명")` 필수. 유효값이 있으면 `comment="상태 (ACTIVE/INACTIVE)"` 형식으로 명시
- 신규 테이블/컬럼 추가 시 한글 comment 누락 금지

### 정규화 원칙
- **JSONB에 ID 배열 저장 금지** → 중간(junction) 테이블로 M:N 관계 분리
  - 기존 deprecated JSONB 컬럼은 하위호환을 위해 유지하되, comment에 `(deprecated, use {중간테이블명})` 표기
  - 서비스 코드는 **Dual Write** 전략: 저장 시 JSONB + 중간 테이블 동시, 조회 시 중간 테이블 우선 → JSONB fallback
- 기존 중간 테이블 목록:
  - `cleansing_job_rule` (정제작업↔규칙)
  - `distribution_request_dataset` (유통신청↔데이터셋)
  - `distribution_fusion_source` (융합모델↔원본데이터셋)
  - `distribution_api_key_endpoint` (API키↔엔드포인트)
  - `catalog_dataset_tag` (데이터셋↔태그)

### Foreign Key 규칙
- **모든 FK에 `ondelete` 반드시 지정**:
  - `CASCADE`: 부모-자식 관계 (게시글→첨부파일, 데이터셋→컬럼메타, 변환모델→매핑 등)
  - `SET NULL`: 참조/연관 관계 (데이터셋→소유자, 로그→사용자 등)
  - 자기참조(self-reference): `SET NULL`
- ondelete 없는 FK 추가 금지

### 인덱스 규칙
- `is_deleted` 컬럼이 있는 테이블에 부분 인덱스 필수:
  ```python
  Index("ix_{tablename}_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false"))
  ```
- 자주 조회되는 FK 컬럼에 일반 인덱스 추가
- 복합 유니크 제약은 `Index("uq_...", "col1", "col2", unique=True)` 형태

### 표준코드 체계
- 공통코드는 `std_code` 테이블에서 관리 (code_group → code_id → code_value)
- 단어사전(`std_word`), 도메인사전(`std_domain`), 용어사전(`std_term`), 코드사전(`std_code`) 4종 관리
- 신규 상태/유형 코드 추가 시 `std_code`에도 등록

### 마이그레이션 규칙
- Alembic으로 관리: `docker compose exec -T backend bash -c "cd /app && PYTHONPATH=/app alembic revision --autogenerate -m '설명'"`
- 적용: `docker compose exec -T backend bash -c "cd /app && PYTHONPATH=/app alembic upgrade head"`
- 모델 변경 후 반드시 마이그레이션 생성 → 적용 → Docker 재빌드

## 백엔드 공통 패턴

### API 응답 형식
- 단건: `APIResponse[T]` → `{"success": true, "message": "OK", "data": {...}}`
- 목록(페이징): `PageResponse[T]` → `{"items": [...], "total": N, "page": 1, "page_size": 20, "total_pages": N}`
- 스키마 정의: `backend/app/schemas/` (common.py, portal.py, admin.py)

### 서비스 레이어 구조
- API 라우터(`api/v1/`) → 서비스(`services/`) → 모델(`models/`)
- 라우터에 비즈니스 로직 작성 금지, 반드시 서비스 레이어 분리
- 비동기 DB 세션: `AsyncSession` + `select()` 문법 사용

### 인증/인가
- JWT 토큰 기반 (`app/core/auth.py`)
- `CurrentUser = Depends(get_current_user)` 로 현재 사용자 주입
- 역할 기반 접근제어: `role_code` (SYS_ADMIN, DATA_ADMIN, EMPLOYEE, PARTNER, ENGINEER)

### Docker 접속 정보
- PostgreSQL: `localhost:5433` / DB: `datahub` / User: `datahub` / PW: `datahub`
- Backend API: `localhost:8088/api/v1/`
- Frontend Dev: `localhost:5173` / Prod: `localhost:8088`
