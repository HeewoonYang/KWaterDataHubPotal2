"""AI 검색 서비스 (1단계: 키워드 기반 검색)"""
import re
import uuid
from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import CatalogDataset
from app.models.operation import OperationAiQueryLog
from app.models.portal import PortalVisualizationChart
from app.schemas.portal import AiChartResult, AiDatasetResult, AiSearchResponse

# 불용어
STOPWORDS = {"은", "는", "이", "가", "을", "를", "의", "에", "에서", "으로", "로", "와", "과", "도", "만", "부터", "까지", "보다", "에게", "한테", "께", "라", "다", "요", "것", "수", "등", "및", "또는", "그", "이런", "저런", "어떤", "모든", "각", "좀", "잘", "더", "덜", "매우", "아주", "너무", "정말", "진짜", "약", "대략", "최근", "관련", "데이터", "정보", "현황", "목록", "조회", "확인", "알려줘", "보여줘", "찾아줘"}

SUGGESTIONS = [
    "최근 등록된 수자원 데이터는?",
    "댐 수위 데이터의 컬럼 정보 알려줘",
    "수질 관련 공개 데이터 목록",
    "전력 사용량 데이터 다운로드 방법",
    "IoT 센서 데이터 수집 현황",
    "환경영향평가 보고서 검색",
    "하천 유량 데이터 최신 현황",
    "GIS 공간 데이터 목록",
]


def extract_keywords(query: str) -> list[str]:
    # 간단한 키워드 추출: 한글/영문 단어 분리 → 불용어 제거
    words = re.findall(r"[가-힣a-zA-Z0-9]+", query)
    return [w for w in words if w not in STOPWORDS and len(w) > 1]


async def search(db: AsyncSession, query: str, user_id=None) -> AiSearchResponse:
    keywords = extract_keywords(query)

    if not keywords:
        return AiSearchResponse(answer="검색어를 더 구체적으로 입력해주세요.", datasets=[])

    # ILIKE 검색
    conditions = []
    for kw in keywords:
        like = f"%{kw}%"
        conditions.append(CatalogDataset.dataset_name.ilike(like))
        conditions.append(CatalogDataset.dataset_name_kr.ilike(like))
        conditions.append(CatalogDataset.description.ilike(like))

    rows = (await db.execute(
        select(CatalogDataset)
        .where(CatalogDataset.status == "ACTIVE")
        .where(or_(*conditions))
        .order_by(CatalogDataset.created_at.desc())
        .limit(5)
    )).scalars().all()

    datasets = [
        AiDatasetResult(id=r.id, name=r.dataset_name, description=r.description, data_format=r.data_format)
        for r in rows
    ]

    # 요약 생성
    if datasets:
        names = ", ".join(d.name for d in datasets[:3])
        answer = f"'{' '.join(keywords)}' 관련 데이터셋 {len(datasets)}건을 찾았습니다: {names}"
        if len(datasets) > 3:
            answer += f" 외 {len(datasets)-3}건"
    else:
        answer = f"'{' '.join(keywords)}' 관련 데이터셋을 찾지 못했습니다. 다른 키워드로 검색해보세요."

    # 로그 기록
    if user_id:
        db.add(OperationAiQueryLog(
            id=uuid.uuid4(), user_id=user_id, query_text=query,
            query_type="NATURAL_LANGUAGE", response_text=answer,
            model_name="keyword-search-v1", token_count=len(query),
            response_time_ms=50, queried_at=datetime.now(),
        ))

    # 관련 차트 조회
    charts: list[AiChartResult] = []
    if datasets:
        dataset_ids = [d.id for d in datasets]
        chart_rows = (await db.execute(
            select(PortalVisualizationChart, CatalogDataset.dataset_name)
            .outerjoin(CatalogDataset, PortalVisualizationChart.dataset_id == CatalogDataset.id)
            .where(
                PortalVisualizationChart.dataset_id.in_(dataset_ids),
                PortalVisualizationChart.is_deleted == False,
            )
            .order_by(PortalVisualizationChart.created_at.desc())
            .limit(5)
        )).all()
        charts = [
            AiChartResult(
                id=c[0].id, chart_name=c[0].chart_name, chart_type=c[0].chart_type,
                dataset_id=c[0].dataset_id, dataset_name=c[1], created_at=c[0].created_at,
            )
            for c in chart_rows
        ]
        if charts:
            chart_names = ", ".join(c.chart_name for c in charts[:3])
            answer += f"\n\n관련 시각화 차트 {len(charts)}건도 있습니다: {chart_names}"

    return AiSearchResponse(answer=answer, datasets=datasets, charts=charts)


async def get_suggestions() -> list[str]:
    return SUGGESTIONS
