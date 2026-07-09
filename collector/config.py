import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    data_api_key: str
    supabase_url: str
    supabase_service_key: str
    # 활용신청한 나라장터 API 오퍼레이션에 맞춰 변경할 수 있습니다.
    g2b_base_url: str = (
        "https://apis.data.go.kr/1230000/ad/BidPublicInfoService"
        "/getBidPblancListInfoThngPPSSrch"
    )
    page_size: int = 100
    request_timeout: int = 30

    @classmethod
    def from_env(cls) -> "Config":
        required = {
            "DATA_GO_KR_API_KEY": os.getenv("DATA_GO_KR_API_KEY", ""),
            "SUPABASE_URL": os.getenv("SUPABASE_URL", ""),
            "SUPABASE_SERVICE_ROLE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise RuntimeError(f"필수 환경변수가 없습니다: {', '.join(missing)}")
        return cls(
            data_api_key=required["DATA_GO_KR_API_KEY"],
            supabase_url=required["SUPABASE_URL"].rstrip("/"),
            supabase_service_key=required["SUPABASE_SERVICE_ROLE_KEY"],
            g2b_base_url=os.getenv("G2B_BASE_URL") or cls.g2b_base_url,
        )
