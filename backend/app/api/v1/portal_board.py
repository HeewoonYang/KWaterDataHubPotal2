"""포털 게시판 API (공지사항, 질의응답, FAQ)"""
import math
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user, get_current_user_optional
from app.database import get_db
from app.models.board import BoardAttachment, BoardPost
from app.schemas.common import APIResponse, PageResponse

router = APIRouter()

UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── 공지사항 ──
@router.get("/notices")
async def list_notices(
    page: int = 1, page_size: int = 10, search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(BoardPost).where(BoardPost.board_type == "NOTICE", BoardPost.status == "ACTIVE", BoardPost.is_deleted == False)
    if search:
        query = query.where(or_(BoardPost.title.ilike(f"%{search}%"), BoardPost.content.ilike(f"%{search}%")))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (page - 1) * page_size
    rows = (await db.execute(
        query.order_by(BoardPost.is_pinned.desc(), BoardPost.created_at.desc()).offset(offset).limit(page_size)
    )).scalars().all()

    items = [_post_to_dict(r) for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size,
                        total_pages=math.ceil(total / page_size) if page_size else 0)


@router.get("/notices/{post_id}")
async def get_notice(post_id: str, db: AsyncSession = Depends(get_db)):
    post = await _get_post(db, post_id, "NOTICE")
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
    post.view_count = (post.view_count or 0) + 1
    attachments = await _get_attachments(db, post.id)
    result = _post_to_dict(post)
    result["attachments"] = [{"id": str(a.id), "file_name": a.file_name, "file_size": a.file_size} for a in attachments]
    return APIResponse(data=result)


@router.post("/notices")
async def create_notice(
    title: str = Form(...), content: str = Form(...), is_pinned: bool = Form(False),
    files: list[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    post = BoardPost(
        id=uuid.uuid4(), board_type="NOTICE", title=title, content=content,
        author_id=user.id, author_name=user.name, is_pinned=is_pinned,
        status="ACTIVE", created_at=datetime.now(),
    )
    db.add(post)
    await db.flush()
    await _save_files(db, post.id, files)
    return APIResponse(data=_post_to_dict(post), message="공지사항이 등록되었습니다")


@router.put("/notices/{post_id}")
async def update_notice(
    post_id: str, title: str = Form(...), content: str = Form(...), is_pinned: bool = Form(False),
    files: list[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    post = await _get_post(db, post_id, "NOTICE")
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
    post.title = title
    post.content = content
    post.is_pinned = is_pinned
    post.updated_at = datetime.now()
    post.updated_by = user.id
    if files:
        await _save_files(db, post.id, files)
    return APIResponse(data=_post_to_dict(post), message="수정되었습니다")


@router.delete("/notices/{post_id}")
async def delete_notice(post_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    post = await _get_post(db, post_id, "NOTICE")
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
    post.is_deleted = True
    return APIResponse(message="삭제되었습니다")


# ── 질의응답 ──
@router.get("/qna")
async def list_qna(
    page: int = 1, page_size: int = 10, search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(BoardPost).where(BoardPost.board_type == "QNA", BoardPost.status == "ACTIVE", BoardPost.is_deleted == False)
    if search:
        query = query.where(or_(BoardPost.title.ilike(f"%{search}%"), BoardPost.content.ilike(f"%{search}%")))
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (page - 1) * page_size
    rows = (await db.execute(query.order_by(BoardPost.created_at.desc()).offset(offset).limit(page_size))).scalars().all()
    items = [_post_to_dict(r) for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size,
                        total_pages=math.ceil(total / page_size) if page_size else 0)


@router.get("/qna/{post_id}")
async def get_qna(post_id: str, db: AsyncSession = Depends(get_db)):
    post = await _get_post(db, post_id, "QNA")
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
    post.view_count = (post.view_count or 0) + 1
    attachments = await _get_attachments(db, post.id)
    result = _post_to_dict(post)
    result["attachments"] = [{"id": str(a.id), "file_name": a.file_name, "file_size": a.file_size} for a in attachments]
    return APIResponse(data=result)


@router.post("/qna")
async def create_qna(
    title: str = Form(...), content: str = Form(...),
    files: list[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    post = BoardPost(
        id=uuid.uuid4(), board_type="QNA", title=title, content=content,
        author_id=user.id, author_name=user.name, status="ACTIVE", created_at=datetime.now(),
    )
    db.add(post)
    await db.flush()
    await _save_files(db, post.id, files)
    return APIResponse(data=_post_to_dict(post), message="질문이 등록되었습니다")


@router.put("/qna/{post_id}/answer")
async def answer_qna(
    post_id: str, answer: str = Form(...),
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    post = await _get_post(db, post_id, "QNA")
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
    post.answer_content = answer
    post.answer_author_id = user.id
    post.answer_author_name = user.name
    post.answered_at = datetime.now()
    return APIResponse(message="답변이 등록되었습니다")


# ── FAQ ──
@router.get("/faq")
async def list_faq(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(BoardPost).where(BoardPost.board_type == "FAQ", BoardPost.status == "ACTIVE", BoardPost.is_deleted == False)
    if category:
        query = query.where(BoardPost.faq_category == category)
    rows = (await db.execute(query.order_by(BoardPost.faq_category, BoardPost.created_at.desc()))).scalars().all()
    return APIResponse(data=[_post_to_dict(r) for r in rows])


@router.post("/faq")
async def create_faq(
    title: str = Form(...), content: str = Form(...), category: str = Form("일반"),
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    post = BoardPost(
        id=uuid.uuid4(), board_type="FAQ", title=title, content=content,
        faq_category=category, author_id=user.id, author_name=user.name,
        status="ACTIVE", created_at=datetime.now(),
    )
    db.add(post)
    return APIResponse(message="FAQ가 등록되었습니다")


# ── 첨부파일 다운로드 ──
@router.get("/attachments/{attachment_id}/download")
async def download_attachment(attachment_id: str, db: AsyncSession = Depends(get_db)):
    att = (await db.execute(select(BoardAttachment).where(BoardAttachment.id == uuid.UUID(attachment_id)))).scalar_one_or_none()
    if not att:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    file_path = os.path.join(UPLOAD_DIR, att.stored_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="파일이 서버에 없습니다")
    return FileResponse(file_path, filename=att.file_name, media_type=att.content_type or "application/octet-stream")


# ── 디스크 용량 ──
@router.get("/disk-usage")
async def get_disk_usage():
    import shutil
    total, used, free = shutil.disk_usage("/")
    return APIResponse(data={
        "total_gb": round(total / (1024**3), 1),
        "used_gb": round(used / (1024**3), 1),
        "free_gb": round(free / (1024**3), 1),
        "usage_pct": round(used / total * 100, 1),
    })


# ── 헬퍼 ──
def _post_to_dict(p: BoardPost) -> dict:
    return {
        "id": str(p.id), "board_type": p.board_type, "title": p.title, "content": p.content,
        "author_name": p.author_name, "view_count": p.view_count or 0,
        "is_pinned": p.is_pinned, "faq_category": p.faq_category,
        "answer_content": p.answer_content, "answer_author_name": p.answer_author_name,
        "answered_at": p.answered_at.strftime("%Y-%m-%d %H:%M") if p.answered_at else None,
        "created_at": p.created_at.strftime("%Y-%m-%d") if p.created_at else None,
        "status": p.status,
    }


async def _get_post(db: AsyncSession, post_id: str, board_type: str) -> BoardPost | None:
    return (await db.execute(
        select(BoardPost).where(BoardPost.id == uuid.UUID(post_id), BoardPost.board_type == board_type, BoardPost.is_deleted == False)
    )).scalar_one_or_none()


async def _get_attachments(db: AsyncSession, post_id) -> list:
    return (await db.execute(select(BoardAttachment).where(BoardAttachment.post_id == post_id))).scalars().all()


async def _save_files(db: AsyncSession, post_id, files: list[UploadFile]):
    for f in files:
        if not f.filename:
            continue
        stored = f"{uuid.uuid4().hex}_{f.filename}"
        path = os.path.join(UPLOAD_DIR, stored)
        content = await f.read()
        with open(path, "wb") as fp:
            fp.write(content)
        db.add(BoardAttachment(
            id=uuid.uuid4(), post_id=post_id, file_name=f.filename,
            stored_name=stored, file_size=len(content), content_type=f.content_type,
        ))
