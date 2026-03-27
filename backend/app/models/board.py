"""게시판 모델 (공지사항, 질의응답, FAQ)"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.models.base import AuditMixin, new_uuid


class BoardPost(AuditMixin, Base):
    """게시판 게시글"""
    __tablename__ = "board_post"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="게시글ID")
    board_type = Column(String(20), nullable=False, comment="게시판유형 (NOTICE/QNA/FAQ)")
    title = Column(String(500), nullable=False, comment="제목")
    content = Column(Text, nullable=False, comment="내용")
    author_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="SET NULL"), comment="작성자ID")
    author_name = Column(String(100), comment="작성자명")
    view_count = Column(Integer, default=0, comment="조회수")
    is_pinned = Column(Boolean, default=False, comment="상단고정여부")
    status = Column(String(20), default="ACTIVE", comment="상태 (ACTIVE/INACTIVE)")
    # FAQ 전용
    faq_category = Column(String(100), comment="FAQ카테고리")
    # QNA 전용
    answer_content = Column(Text, comment="답변내용")
    answer_author_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="SET NULL"), comment="답변자ID")
    answer_author_name = Column(String(100), comment="답변자명")
    answered_at = Column(DateTime, comment="답변일시")

    __table_args__ = (
        Index("ix_board_post_type", "board_type"),
        Index("ix_board_post_author", "author_id"),
        Index("ix_board_post_pinned", "is_pinned"),
        {"comment": "게시판게시글"},
    )


class BoardAttachment(Base):
    """게시판 첨부파일"""
    __tablename__ = "board_attachment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="첨부파일ID")
    post_id = Column(UUID(as_uuid=True), ForeignKey("board_post.id", ondelete="CASCADE"), nullable=False, comment="게시글ID")
    file_name = Column(String(500), nullable=False, comment="원본파일명")
    stored_name = Column(String(500), nullable=False, comment="저장파일명")
    file_size = Column(Integer, comment="파일크기")
    content_type = Column(String(200), comment="MIME타입")
    uploaded_at = Column(DateTime, default=datetime.now, comment="업로드일시")

    __table_args__ = (
        Index("ix_board_attach_post", "post_id"),
        {"comment": "게시판첨부파일"},
    )
