"""표준 사전 엑셀 데이터 초기 임포트 스크립트"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import engine, async_session, Base
from app.services.import_service import import_words, import_domains, import_terms, import_codes

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "docs", "K-water 데이터 품질", "01. 데이터표준"
)

FILES = {
    "word": os.path.join(DATA_DIR, "표준 데이터 조회_K-water데이터표준_단어사전.xlsx"),
    "domain": os.path.join(DATA_DIR, "표준 데이터 조회_K-water데이터표준_도메인사전.xlsx"),
    "term": os.path.join(DATA_DIR, "표준 데이터 조회_K-water데이터표준_용어사전.xlsx"),
    "code": os.path.join(DATA_DIR, "표준 데이터 조회_K-water데이터표준_코드사전.xlsx"),
}


async def main():
    print(f"Database: {settings.DATABASE_URL}")
    print(f"Data dir: {DATA_DIR}")
    print()

    for name, path in FILES.items():
        if not os.path.exists(path):
            print(f"[SKIP] {name}: 파일 없음 - {path}")
        else:
            print(f"[OK]   {name}: {path}")
    print()

    async with async_session() as db:
        # 1. 단어사전
        print("=" * 60)
        print("1. 단어사전 임포트 시작...")
        try:
            result = await import_words(db, FILES["word"])
            await db.commit()
            print(f"   완료: {result}")
        except Exception as e:
            await db.rollback()
            print(f"   에러: {e}")

        # 2. 도메인사전
        print("2. 도메인사전 임포트 시작...")
        try:
            result = await import_domains(db, FILES["domain"])
            await db.commit()
            print(f"   완료: {result}")
        except Exception as e:
            await db.rollback()
            print(f"   에러: {e}")

        # 3. 용어사전
        print("3. 용어사전 임포트 시작...")
        try:
            result = await import_terms(db, FILES["term"])
            await db.commit()
            print(f"   완료: {result}")
        except Exception as e:
            await db.rollback()
            print(f"   에러: {e}")

        # 4. 코드사전
        print("4. 코드사전 임포트 시작...")
        try:
            result = await import_codes(db, FILES["code"])
            await db.commit()
            print(f"   완료: {result}")
        except Exception as e:
            await db.rollback()
            print(f"   에러: {e}")

    print()
    print("=" * 60)
    print("임포트 완료!")


if __name__ == "__main__":
    asyncio.run(main())
