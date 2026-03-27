from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class StdWord(Base):
    """단어사전"""
    __tablename__ = "std_word"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="단어ID")
    word_name = Column(String(200), nullable=False, comment="단어명")
    english_name = Column(String(200), nullable=False, comment="영문명")
    english_meaning = Column(String(500), comment="영문의미")
    attr_classifier = Column(String(100), comment="속성분류어")
    synonyms = Column(Text, comment="동의어")
    description = Column(Text, comment="설명")
    status = Column(String(20), default="ACTIVE", comment="상태 (ACTIVE/INACTIVE/PENDING)")

    created_by = Column(Integer, comment="생성자ID")
    created_at = Column(DateTime, default=datetime.now, comment="생성일시")
    updated_by = Column(Integer, comment="수정자ID")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="수정일시")
    is_deleted = Column(Boolean, default=False, comment="삭제여부")

    __table_args__ = (
        Index("ix_std_word_name", "word_name"),
        Index("ix_std_word_eng", "english_name"),
        Index("ix_std_word_status", "status"),
        Index("uq_std_word", "word_name", "english_name", unique=True),
        Index("ix_std_word_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "단어사전"},
    )


class StdDomain(Base):
    """도메인사전"""
    __tablename__ = "std_domain"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="도메인ID")
    domain_group = Column(String(50), nullable=False, comment="도메인그룹")
    domain_name = Column(String(200), nullable=False, comment="도메인명")
    domain_code = Column(String(100), nullable=False, unique=True, comment="도메인코드명")
    data_type = Column(String(50), nullable=False, comment="데이터유형")
    length = Column(Integer, comment="길이")
    decimal_places = Column(Integer, default=0, comment="소수점")
    data_format = Column(String(200), comment="데이터형식")
    valid_values = Column(Text, comment="유효값목록")
    characteristics = Column(Text, comment="특징정보")
    description = Column(Text, comment="설명")
    status = Column(String(20), default="ACTIVE", comment="상태")

    created_by = Column(Integer, comment="생성자ID")
    created_at = Column(DateTime, default=datetime.now, comment="생성일시")
    updated_by = Column(Integer, comment="수정자ID")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="수정일시")
    is_deleted = Column(Boolean, default=False, comment="삭제여부")

    __table_args__ = (
        Index("ix_std_domain_group", "domain_group"),
        Index("ix_std_domain_code", "domain_code"),
        Index("ix_std_domain_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "도메인사전"},
    )


class StdTerm(Base):
    """용어사전"""
    __tablename__ = "std_term"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="용어ID")
    term_name = Column(String(300), nullable=False, comment="용어명")
    english_name = Column(String(300), nullable=False, comment="영문명")
    english_meaning = Column(String(500), comment="영문의미")
    domain_code = Column(String(100), comment="도메인코드명 (ref: std_domain.domain_code)")
    term_classifier = Column(String(100), comment="용어특성분류기")
    domain_group = Column(String(50), comment="도메인그룹")
    data_type = Column(String(50), comment="데이터유형")
    length = Column(Integer, comment="길이")
    decimal_places = Column(Integer, default=0, comment="소수점")
    data_format = Column(String(200), comment="데이터형식")
    valid_values = Column(Text, comment="유효값목록")
    characteristics = Column(Text, comment="특징정보")
    description = Column(Text, comment="설명")
    status = Column(String(20), default="ACTIVE", comment="상태")

    created_by = Column(Integer, comment="생성자ID")
    created_at = Column(DateTime, default=datetime.now, comment="생성일시")
    updated_by = Column(Integer, comment="수정자ID")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="수정일시")
    is_deleted = Column(Boolean, default=False, comment="삭제여부")

    __table_args__ = (
        Index("ix_std_term_name", "term_name"),
        Index("ix_std_term_eng", "english_name"),
        Index("ix_std_term_domain", "domain_code"),
        Index("ix_std_term_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "용어사전"},
    )


class StdCode(Base):
    """코드사전"""
    __tablename__ = "std_code"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="코드ID_PK")
    code_group = Column(String(100), nullable=False, comment="코드그룹")
    system_name = Column(String(200), comment="시스템명")
    table_name = Column(String(200), comment="테이블명")
    code_group_name = Column(String(200), nullable=False, comment="코드그룹명")
    code_type = Column(String(50), comment="코드구분")
    seq_no = Column(Integer, comment="순번")
    code_id = Column(String(100), nullable=False, comment="코드ID")
    code_value = Column(String(200), comment="코드값")
    code_value_name = Column(String(300), comment="코드값명")
    sort_order = Column(Integer, default=0, comment="정렬순서")
    parent_code_name = Column(String(200), comment="부모코드명")
    parent_code_value = Column(String(200), comment="부모코드값")
    description = Column(Text, comment="설명")
    effective_date = Column(Date, comment="등록일자")
    expiration_date = Column(Date, comment="적용종료일자")
    status = Column(String(20), default="ACTIVE", comment="상태")

    created_by = Column(Integer, comment="생성자ID")
    created_at = Column(DateTime, default=datetime.now, comment="생성일시")
    updated_by = Column(Integer, comment="수정자ID")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="수정일시")
    is_deleted = Column(Boolean, default=False, comment="삭제여부")

    __table_args__ = (
        Index("ix_std_code_group", "code_group"),
        Index("ix_std_code_id", "code_id"),
        Index("ix_std_code_parent", "parent_code_name", "parent_code_value"),
        Index("ix_std_code_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "코드사전"},
    )


class StdRequest(Base):
    """표준 변경 신청"""
    __tablename__ = "std_request"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="신청ID")
    request_type = Column(String(20), nullable=False, comment="신청유형 (WORD/DOMAIN/TERM/COMMON_CODE/LIST_CODE)")
    action_type = Column(String(20), nullable=False, comment="작업유형 (CREATE/MODIFY/DELETE)")
    request_data = Column(JSONB, nullable=False, comment="신청데이터")
    validation_result = Column(String(20), comment="검증결과 (PASS/FAIL/PENDING)")
    validation_message = Column(Text, comment="검증메시지")
    status = Column(String(20), default="PENDING", comment="신청상태 (PENDING/APPROVED/REJECTED)")

    requested_by = Column(Integer, comment="신청자ID")
    requested_at = Column(DateTime, default=datetime.now, comment="신청일시")
    reviewed_by = Column(Integer, comment="검토자ID")
    reviewed_at = Column(DateTime, comment="검토일시")
    review_comment = Column(Text, comment="검토의견")

    __table_args__ = (
        {"comment": "표준변경신청"},
    )


class StdRequestHistory(Base):
    """표준변경이력"""
    __tablename__ = "std_request_history"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="변경이력ID")
    request_id = Column(Integer, ForeignKey("std_request.id", ondelete="CASCADE"), nullable=False, comment="신청ID")
    action = Column(String(20), comment="수행작업 (STATUS_CHANGE/DATA_MODIFY)")
    old_status = Column(String(20), comment="이전상태")
    new_status = Column(String(20), comment="변경상태")
    comment = Column(Text, comment="의견")
    changed_by = Column(Integer, comment="변경자ID")
    changed_at = Column(DateTime, default=datetime.now, comment="변경일시")

    __table_args__ = (
        Index("ix_std_req_hist_req", "request_id"),
        {"comment": "표준변경이력"},
    )
