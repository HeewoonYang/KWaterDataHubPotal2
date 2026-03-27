# K-water 데이터허브 포털 프로젝트

## 프로젝트 개요
- K-water 클라우드 데이터 에코시스템의 데이터허브 포털 웹 화면
- Frontend: Vue 3 (Composition API + TypeScript)
- Backend: Python (FastAPI)

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

### 작업 실행
- 프롬프트 질의 실행 시 한번에 실행이 불가할 경우 계획을 세워 분할 후 순차 실행한다.
- 코드 수정 완료 후 Docker 컨테이너가 실행 중이면 `docker compose up -d --build` 로 이미지를 재빌드하여 반영한다.
- `규칙(...)` 형식의 프롬프트가 주어지면, 괄호 안의 내용을 CLAUDE.md, PRD, TRD에 모두 반영한다.

### 요구사항 준수
- 요구사항이 빠짐없이 적용되어야 한다. (기능, 비기능 모두)
- 기능 요구사항: `REQ-DHUB-ALL-MERGED.md`, `데이터허브포털_메뉴구성서_v5_전체요구사항.xlsx`
- 비기능 요구사항: `KWDP-SD-AN-02-요구사항추적표-v0.83.xlsx` (REQ-SIR/DAR/PER/TER/SER/COR)
- 원본 요구사항 문서 경로: `D:\00_수공프로젝트\20260325_데이터허브포털 구현\`

## 메뉴 구성 (10개 대분류, 웹 화면 34개+)
- 시스템관리, 사용자관리, 포털, 데이터표준, 데이터수집, 데이터정제, 데이터저장, 데이터유통, FA망이전, 운영관리
- 상세 메뉴 구성은 `docs/PRD_데이터허브포털.md` 참조

### 사용자 포털 GNB 메뉴 명칭
- **대시보드** (구: 메인홈) → 서브메뉴: 대시보드, 위젯 설정, 시각화 갤러리 설정, 위젯 관리, 갤러리 콘텐츠 관리 (목록보기/차트보기 탭, 콘텐츠 생성 → D&D 시각화)
- 데이터카탈로그 → 서브메뉴: 카탈로그 탐색, 데이터 검색
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
