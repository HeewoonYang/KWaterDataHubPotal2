from datetime import date, datetime

from pydantic import BaseModel


# ── 단어사전 ──
class StdWordBase(BaseModel):
    word_name: str
    english_name: str
    english_meaning: str | None = None
    attr_classifier: str | None = None
    synonyms: str | None = None
    description: str | None = None
    status: str = "ACTIVE"


class StdWordCreate(StdWordBase):
    pass


class StdWordUpdate(BaseModel):
    word_name: str | None = None
    english_name: str | None = None
    english_meaning: str | None = None
    attr_classifier: str | None = None
    synonyms: str | None = None
    description: str | None = None
    status: str | None = None


class StdWordResponse(StdWordBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── 도메인사전 ──
class StdDomainBase(BaseModel):
    domain_group: str
    domain_name: str
    domain_code: str
    data_type: str
    length: int | None = None
    decimal_places: int | None = 0
    data_format: str | None = None
    valid_values: str | None = None
    characteristics: str | None = None
    description: str | None = None
    status: str = "ACTIVE"


class StdDomainCreate(StdDomainBase):
    pass


class StdDomainUpdate(BaseModel):
    domain_group: str | None = None
    domain_name: str | None = None
    domain_code: str | None = None
    data_type: str | None = None
    length: int | None = None
    decimal_places: int | None = None
    data_format: str | None = None
    valid_values: str | None = None
    characteristics: str | None = None
    description: str | None = None
    status: str | None = None


class StdDomainResponse(StdDomainBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── 용어사전 ──
class StdTermBase(BaseModel):
    term_name: str
    english_name: str
    english_meaning: str | None = None
    domain_code: str | None = None
    term_classifier: str | None = None
    domain_group: str | None = None
    data_type: str | None = None
    length: int | None = None
    decimal_places: int | None = 0
    data_format: str | None = None
    valid_values: str | None = None
    characteristics: str | None = None
    description: str | None = None
    status: str = "ACTIVE"


class StdTermCreate(StdTermBase):
    pass


class StdTermUpdate(BaseModel):
    term_name: str | None = None
    english_name: str | None = None
    english_meaning: str | None = None
    domain_code: str | None = None
    term_classifier: str | None = None
    domain_group: str | None = None
    data_type: str | None = None
    length: int | None = None
    decimal_places: int | None = None
    data_format: str | None = None
    valid_values: str | None = None
    characteristics: str | None = None
    description: str | None = None
    status: str | None = None


class StdTermResponse(StdTermBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── 코드사전 ──
class StdCodeBase(BaseModel):
    code_group: str
    system_name: str | None = None
    table_name: str | None = None
    code_group_name: str
    code_type: str | None = None
    seq_no: int | None = None
    code_id: str
    code_value: str | None = None
    code_value_name: str | None = None
    sort_order: int | None = 0
    parent_code_name: str | None = None
    parent_code_value: str | None = None
    description: str | None = None
    effective_date: date | None = None
    expiration_date: date | None = None
    status: str = "ACTIVE"


class StdCodeCreate(StdCodeBase):
    pass


class StdCodeUpdate(BaseModel):
    code_group: str | None = None
    system_name: str | None = None
    table_name: str | None = None
    code_group_name: str | None = None
    code_type: str | None = None
    seq_no: int | None = None
    code_id: str | None = None
    code_value: str | None = None
    code_value_name: str | None = None
    sort_order: int | None = None
    parent_code_name: str | None = None
    parent_code_value: str | None = None
    description: str | None = None
    effective_date: date | None = None
    expiration_date: date | None = None
    status: str | None = None


class StdCodeResponse(StdCodeBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── 표준 신청 ──
class StdRequestCreate(BaseModel):
    request_type: str  # WORD/DOMAIN/TERM/COMMON_CODE/LIST_CODE
    action_type: str  # CREATE/MODIFY/DELETE
    request_data: dict


class StdRequestResponse(BaseModel):
    id: int
    request_type: str
    action_type: str
    request_data: dict
    validation_result: str | None = None
    validation_message: str | None = None
    status: str
    requested_by: int | None = None
    requested_at: datetime | None = None
    reviewed_by: int | None = None
    reviewed_at: datetime | None = None
    review_comment: str | None = None

    model_config = {"from_attributes": True}
