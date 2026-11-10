import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Config:
    data_api_key: str
    supabase_url: str
    supabase_service_key: str = field(repr=False)
    # 활용신청한 나라장터 API 오퍼레이션에 맞춰 변경할 수 있습니다.
    g2b_base_url: str = (
        "https://apis.data.go.kr/1230000/ad/BidPublicInfoService"
        "/getBidPblancListInfoThngPPSSrch"
    )
    page_size: int = 100
    request_timeout: int = 30
    bidpage_enabled: bool = False
    bidpage_username: str = field(default="", repr=False)
    bidpage_password: str = field(default="", repr=False)
    bidpage_base_url: str = "https://guro.bidpage.co.kr"
    bidpage_page_size: int = 100
    bidpage_max_pages: int = 20

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
        bidpage_enabled = os.getenv("BIDPAGE_ENABLED", "").strip().lower() in {
            "1", "true", "yes", "on"
        }
        bidpage_username = os.getenv("BIDPAGE_USERNAME", "")
        bidpage_password = os.getenv("BIDPAGE_PASSWORD", "")
        if bidpage_enabled and (not bidpage_username or not bidpage_password):
            raise RuntimeError(
                "BIDPAGE_ENABLED=true이면 BIDPAGE_USERNAME과 "
                "BIDPAGE_PASSWORD가 필요합니다."
            )
        return cls(
            data_api_key=required["DATA_GO_KR_API_KEY"],
            supabase_url=required["SUPABASE_URL"].rstrip("/"),
            supabase_service_key=required["SUPABASE_SERVICE_ROLE_KEY"],
            g2b_base_url=os.getenv("G2B_BASE_URL") or cls.g2b_base_url,
            bidpage_enabled=bidpage_enabled,
            bidpage_username=bidpage_username,
            bidpage_password=bidpage_password,
            bidpage_base_url=(
                os.getenv("BIDPAGE_BASE_URL") or cls.bidpage_base_url
            ).rstrip("/"),
            bidpage_page_size=int(os.getenv("BIDPAGE_PAGE_SIZE", "100")),
            bidpage_max_pages=int(os.getenv("BIDPAGE_MAX_PAGES", "20")),
        )
