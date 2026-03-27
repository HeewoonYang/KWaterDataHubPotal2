import math
from typing import Type

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base
from app.models.standard import StdCode, StdDomain, StdRequest, StdTerm, StdWord
from app.schemas.common import PageRequest, PageResponse


async def _paginated_query(
    db: AsyncSession,
    model: Type[Base],
    params: PageRequest,
    search_columns: list | None = None,
) -> PageResponse:
    """공통 페이지네이션 조회"""
    query = select(model).where(model.is_deleted == False)

    # 상태 필터
    if params.status:
        query = query.where(model.status == params.status)

    # 검색
    if params.search and search_columns:
        conditions = [col.ilike(f"%{params.search}%") for col in search_columns]
        query = query.where(or_(*conditions))

    # 전체 건수
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # 정렬
    if params.sort_by and hasattr(model, params.sort_by):
        col = getattr(model, params.sort_by)
        query = query.order_by(col.desc() if params.sort_order == "desc" else col.asc())
    else:
        query = query.order_by(model.id.desc())

    # 페이지네이션
    offset = (params.page - 1) * params.page_size
    query = query.offset(offset).limit(params.page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    return PageResponse(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
        total_pages=math.ceil(total / params.page_size) if params.page_size > 0 else 0,
    )


# ── 단어사전 ──
async def get_words(db: AsyncSession, params: PageRequest) -> PageResponse:
    return await _paginated_query(
        db, StdWord, params,
        search_columns=[StdWord.word_name, StdWord.english_name, StdWord.english_meaning],
    )


async def get_word(db: AsyncSession, word_id: int) -> StdWord | None:
    result = await db.execute(
        select(StdWord).where(StdWord.id == word_id, StdWord.is_deleted == False)
    )
    return result.scalar_one_or_none()


async def create_word(db: AsyncSession, data: dict) -> StdWord:
    word = StdWord(**data)
    db.add(word)
    await db.flush()
    await db.refresh(word)
    return word


async def update_word(db: AsyncSession, word_id: int, data: dict) -> StdWord | None:
    word = await get_word(db, word_id)
    if not word:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(word, key, value)
    await db.flush()
    await db.refresh(word)
    return word


async def delete_word(db: AsyncSession, word_id: int) -> bool:
    word = await get_word(db, word_id)
    if not word:
        return False
    word.is_deleted = True
    await db.flush()
    return True


# ── 도메인사전 ──
async def get_domains(db: AsyncSession, params: PageRequest) -> PageResponse:
    return await _paginated_query(
        db, StdDomain, params,
        search_columns=[StdDomain.domain_name, StdDomain.domain_code, StdDomain.domain_group],
    )


async def get_domain(db: AsyncSession, domain_id: int) -> StdDomain | None:
    result = await db.execute(
        select(StdDomain).where(StdDomain.id == domain_id, StdDomain.is_deleted == False)
    )
    return result.scalar_one_or_none()


async def create_domain(db: AsyncSession, data: dict) -> StdDomain:
    domain = StdDomain(**data)
    db.add(domain)
    await db.flush()
    await db.refresh(domain)
    return domain


async def update_domain(db: AsyncSession, domain_id: int, data: dict) -> StdDomain | None:
    domain = await get_domain(db, domain_id)
    if not domain:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(domain, key, value)
    await db.flush()
    await db.refresh(domain)
    return domain


async def delete_domain(db: AsyncSession, domain_id: int) -> bool:
    domain = await get_domain(db, domain_id)
    if not domain:
        return False
    domain.is_deleted = True
    await db.flush()
    return True


# ── 용어사전 ──
async def get_terms(db: AsyncSession, params: PageRequest) -> PageResponse:
    return await _paginated_query(
        db, StdTerm, params,
        search_columns=[StdTerm.term_name, StdTerm.english_name, StdTerm.domain_code],
    )


async def get_term(db: AsyncSession, term_id: int) -> StdTerm | None:
    result = await db.execute(
        select(StdTerm).where(StdTerm.id == term_id, StdTerm.is_deleted == False)
    )
    return result.scalar_one_or_none()


async def create_term(db: AsyncSession, data: dict) -> StdTerm:
    term = StdTerm(**data)
    db.add(term)
    await db.flush()
    await db.refresh(term)
    return term


async def update_term(db: AsyncSession, term_id: int, data: dict) -> StdTerm | None:
    term = await get_term(db, term_id)
    if not term:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(term, key, value)
    await db.flush()
    await db.refresh(term)
    return term


async def delete_term(db: AsyncSession, term_id: int) -> bool:
    term = await get_term(db, term_id)
    if not term:
        return False
    term.is_deleted = True
    await db.flush()
    return True


# ── 코드사전 ──
async def get_codes(db: AsyncSession, params: PageRequest) -> PageResponse:
    return await _paginated_query(
        db, StdCode, params,
        search_columns=[StdCode.code_group, StdCode.code_group_name, StdCode.code_id, StdCode.code_value_name],
    )


async def get_code(db: AsyncSession, code_id: int) -> StdCode | None:
    result = await db.execute(
        select(StdCode).where(StdCode.id == code_id, StdCode.is_deleted == False)
    )
    return result.scalar_one_or_none()


async def create_code(db: AsyncSession, data: dict) -> StdCode:
    code = StdCode(**data)
    db.add(code)
    await db.flush()
    await db.refresh(code)
    return code


async def update_code(db: AsyncSession, code_id: int, data: dict) -> StdCode | None:
    code = await get_code(db, code_id)
    if not code:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(code, key, value)
    await db.flush()
    await db.refresh(code)
    return code


async def delete_code(db: AsyncSession, code_id: int) -> bool:
    code = await get_code(db, code_id)
    if not code:
        return False
    code.is_deleted = True
    await db.flush()
    return True


# ── 표준 신청 ──
async def get_requests(db: AsyncSession, params: PageRequest) -> PageResponse:
    query = select(StdRequest)
    if params.status:
        query = query.where(StdRequest.status == params.status)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(StdRequest.id.desc())
    offset = (params.page - 1) * params.page_size
    query = query.offset(offset).limit(params.page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    return PageResponse(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
        total_pages=math.ceil(total / params.page_size) if params.page_size > 0 else 0,
    )


async def create_request(db: AsyncSession, data: dict) -> StdRequest:
    req = StdRequest(**data)
    db.add(req)
    await db.flush()
    await db.refresh(req)
    return req


async def approve_request(db: AsyncSession, request_id: int, reviewer_id: int, comment: str | None = None) -> StdRequest | None:
    from datetime import datetime
    result = await db.execute(select(StdRequest).where(StdRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        return None
    req.status = "APPROVED"
    req.reviewed_by = reviewer_id
    req.reviewed_at = datetime.now()
    req.review_comment = comment
    await db.flush()
    await db.refresh(req)
    return req


async def reject_request(db: AsyncSession, request_id: int, reviewer_id: int, comment: str | None = None) -> StdRequest | None:
    from datetime import datetime
    result = await db.execute(select(StdRequest).where(StdRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        return None
    req.status = "REJECTED"
    req.reviewed_by = reviewer_id
    req.reviewed_at = datetime.now()
    req.review_comment = comment
    await db.flush()
    await db.refresh(req)
    return req
