"""표준사전 CRUD API"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import APIResponse, PageRequest, PageResponse
from app.schemas.standard import (
    StdCodeCreate, StdCodeResponse, StdCodeUpdate,
    StdDomainCreate, StdDomainResponse, StdDomainUpdate,
    StdRequestCreate, StdRequestResponse,
    StdTermCreate, StdTermResponse, StdTermUpdate,
    StdWordCreate, StdWordResponse, StdWordUpdate,
)
from app.services import standard_service, import_service

router = APIRouter()


# ── 단어사전 ──
@router.get("/words", response_model=PageResponse[StdWordResponse])
async def list_words(
    page: int = 1, page_size: int = 20, search: str | None = None,
    sort_by: str | None = None, sort_order: str = "asc", status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    params = PageRequest(page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order, status=status)
    return await standard_service.get_words(db, params)


@router.get("/words/{word_id}", response_model=APIResponse[StdWordResponse])
async def get_word(word_id: int, db: AsyncSession = Depends(get_db)):
    word = await standard_service.get_word(db, word_id)
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    return APIResponse(data=word)


@router.post("/words", response_model=APIResponse[StdWordResponse])
async def create_word(body: StdWordCreate, db: AsyncSession = Depends(get_db)):
    word = await standard_service.create_word(db, body.model_dump())
    return APIResponse(data=word, message="Created")


@router.put("/words/{word_id}", response_model=APIResponse[StdWordResponse])
async def update_word(word_id: int, body: StdWordUpdate, db: AsyncSession = Depends(get_db)):
    word = await standard_service.update_word(db, word_id, body.model_dump(exclude_unset=True))
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    return APIResponse(data=word, message="Updated")


@router.delete("/words/{word_id}", response_model=APIResponse)
async def delete_word(word_id: int, db: AsyncSession = Depends(get_db)):
    if not await standard_service.delete_word(db, word_id):
        raise HTTPException(status_code=404, detail="Word not found")
    return APIResponse(message="Deleted")


# ── 도메인사전 ──
@router.get("/domains", response_model=PageResponse[StdDomainResponse])
async def list_domains(
    page: int = 1, page_size: int = 20, search: str | None = None,
    sort_by: str | None = None, sort_order: str = "asc", status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    params = PageRequest(page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order, status=status)
    return await standard_service.get_domains(db, params)


@router.get("/domains/{domain_id}", response_model=APIResponse[StdDomainResponse])
async def get_domain(domain_id: int, db: AsyncSession = Depends(get_db)):
    domain = await standard_service.get_domain(db, domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return APIResponse(data=domain)


@router.post("/domains", response_model=APIResponse[StdDomainResponse])
async def create_domain(body: StdDomainCreate, db: AsyncSession = Depends(get_db)):
    domain = await standard_service.create_domain(db, body.model_dump())
    return APIResponse(data=domain, message="Created")


@router.put("/domains/{domain_id}", response_model=APIResponse[StdDomainResponse])
async def update_domain(domain_id: int, body: StdDomainUpdate, db: AsyncSession = Depends(get_db)):
    domain = await standard_service.update_domain(db, domain_id, body.model_dump(exclude_unset=True))
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return APIResponse(data=domain, message="Updated")


@router.delete("/domains/{domain_id}", response_model=APIResponse)
async def delete_domain(domain_id: int, db: AsyncSession = Depends(get_db)):
    if not await standard_service.delete_domain(db, domain_id):
        raise HTTPException(status_code=404, detail="Domain not found")
    return APIResponse(message="Deleted")


# ── 용어사전 ──
@router.get("/terms", response_model=PageResponse[StdTermResponse])
async def list_terms(
    page: int = 1, page_size: int = 20, search: str | None = None,
    sort_by: str | None = None, sort_order: str = "asc", status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    params = PageRequest(page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order, status=status)
    return await standard_service.get_terms(db, params)


@router.get("/terms/{term_id}", response_model=APIResponse[StdTermResponse])
async def get_term(term_id: int, db: AsyncSession = Depends(get_db)):
    term = await standard_service.get_term(db, term_id)
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    return APIResponse(data=term)


@router.post("/terms", response_model=APIResponse[StdTermResponse])
async def create_term(body: StdTermCreate, db: AsyncSession = Depends(get_db)):
    term = await standard_service.create_term(db, body.model_dump())
    return APIResponse(data=term, message="Created")


@router.put("/terms/{term_id}", response_model=APIResponse[StdTermResponse])
async def update_term(term_id: int, body: StdTermUpdate, db: AsyncSession = Depends(get_db)):
    term = await standard_service.update_term(db, term_id, body.model_dump(exclude_unset=True))
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    return APIResponse(data=term, message="Updated")


@router.delete("/terms/{term_id}", response_model=APIResponse)
async def delete_term(term_id: int, db: AsyncSession = Depends(get_db)):
    if not await standard_service.delete_term(db, term_id):
        raise HTTPException(status_code=404, detail="Term not found")
    return APIResponse(message="Deleted")


# ── 코드사전 ──
@router.get("/codes", response_model=PageResponse[StdCodeResponse])
async def list_codes(
    page: int = 1, page_size: int = 20, search: str | None = None,
    sort_by: str | None = None, sort_order: str = "asc", status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    params = PageRequest(page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order, status=status)
    return await standard_service.get_codes(db, params)


@router.get("/codes/{code_id}", response_model=APIResponse[StdCodeResponse])
async def get_code(code_id: int, db: AsyncSession = Depends(get_db)):
    code = await standard_service.get_code(db, code_id)
    if not code:
        raise HTTPException(status_code=404, detail="Code not found")
    return APIResponse(data=code)


@router.post("/codes", response_model=APIResponse[StdCodeResponse])
async def create_code(body: StdCodeCreate, db: AsyncSession = Depends(get_db)):
    code = await standard_service.create_code(db, body.model_dump())
    return APIResponse(data=code, message="Created")


@router.put("/codes/{code_id}", response_model=APIResponse[StdCodeResponse])
async def update_code(code_id: int, body: StdCodeUpdate, db: AsyncSession = Depends(get_db)):
    code = await standard_service.update_code(db, code_id, body.model_dump(exclude_unset=True))
    if not code:
        raise HTTPException(status_code=404, detail="Code not found")
    return APIResponse(data=code, message="Updated")


@router.delete("/codes/{code_id}", response_model=APIResponse)
async def delete_code(code_id: int, db: AsyncSession = Depends(get_db)):
    if not await standard_service.delete_code(db, code_id):
        raise HTTPException(status_code=404, detail="Code not found")
    return APIResponse(message="Deleted")


# ── 임포트/익스포트 ──
@router.post("/import", response_model=APIResponse)
async def import_excel(
    file: UploadFile = File(...),
    dict_type: str = Query(..., description="word|domain|term|code"),
    db: AsyncSession = Depends(get_db),
):
    import tempfile, os
    suffix = os.path.splitext(file.filename)[1] if file.filename else ".xlsx"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        importers = {
            "word": import_service.import_words,
            "domain": import_service.import_domains,
            "term": import_service.import_terms,
            "code": import_service.import_codes,
        }
        if dict_type not in importers:
            raise HTTPException(status_code=400, detail=f"Invalid dict_type: {dict_type}")

        result = await importers[dict_type](db, tmp_path)
        return APIResponse(data=result, message=f"Import {dict_type} completed")
    finally:
        os.unlink(tmp_path)


@router.get("/export")
async def export_excel(
    dict_type: str = Query(..., description="word|domain|term|code"),
    db: AsyncSession = Depends(get_db),
):
    if dict_type not in ("word", "domain", "term", "code"):
        raise HTTPException(status_code=400, detail=f"Invalid dict_type: {dict_type}")

    output = await import_service.export_to_excel(db, dict_type)
    filename = f"std_{dict_type}_export.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ── 표준 신청 ──
@router.get("/requests", response_model=PageResponse[StdRequestResponse])
async def list_requests(
    page: int = 1, page_size: int = 20, status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    params = PageRequest(page=page, page_size=page_size, status=status)
    return await standard_service.get_requests(db, params)


@router.post("/requests", response_model=APIResponse[StdRequestResponse])
async def create_request(body: StdRequestCreate, db: AsyncSession = Depends(get_db)):
    req = await standard_service.create_request(db, body.model_dump())
    return APIResponse(data=req, message="Request submitted")


@router.put("/requests/{request_id}/approve", response_model=APIResponse[StdRequestResponse])
async def approve_request(request_id: int, comment: str | None = None, db: AsyncSession = Depends(get_db)):
    req = await standard_service.approve_request(db, request_id, reviewer_id=1, comment=comment)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return APIResponse(data=req, message="Approved")


@router.put("/requests/{request_id}/reject", response_model=APIResponse[StdRequestResponse])
async def reject_request(request_id: int, comment: str | None = None, db: AsyncSession = Depends(get_db)):
    req = await standard_service.reject_request(db, request_id, reviewer_id=1, comment=comment)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return APIResponse(data=req, message="Rejected")
