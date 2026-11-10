from __future__ import annotations

import logging
import re
import ssl
import time
from datetime import datetime
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter

from config import Config

log = logging.getLogger(__name__)


class BidpageAuthenticationError(RuntimeError):
    pass


class FingerprintAdapter(HTTPAdapter):
    """CA 체인이 불완전한 서버를 인증서 지문으로 안전하게 검증합니다."""

    def __init__(self, fingerprint: str) -> None:
        self.fingerprint = fingerprint.replace(":", "").upper()
        if not re.fullmatch(r"[0-9A-F]{64}", self.fingerprint):
            raise ValueError("BIDPAGE_TLS_SHA256은 SHA-256 인증서 지문이어야 합니다.")
        super().__init__()

    def init_poolmanager(self, connections, maxsize, block=False, **kwargs):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        kwargs["ssl_context"] = context
        kwargs["assert_fingerprint"] = self.fingerprint
        kwargs["cert_reqs"] = ssl.CERT_NONE
        return super().init_poolmanager(connections, maxsize, block, **kwargs)

    def cert_verify(self, conn, url, verify, cert):
        conn.assert_fingerprint = self.fingerprint
        conn.cert_reqs = ssl.CERT_NONE
        conn.ca_certs = None
        conn.ca_cert_dir = None
        conn.ca_cert_data = None


def _text(node: Any) -> str:
    return " ".join(node.get_text(" ", strip=True).split()) if node else ""


def _money(text: str) -> int | None:
    match = re.search(r"(?:\d{1,3}(?:,\d{3})+|\d+)\s*원?", text)
    return int(match.group(0).replace(",", "").replace("원", "").strip()) if match else None


def _money_values(text: str) -> list[int]:
    return [
        int(value.replace(",", ""))
        for value in re.findall(r"\d{1,3}(?:,\d{3})+|\d{4,}", text)
    ]


def _date(text: str) -> str | None:
    match = re.search(
        r"(\d{2}|20\d{2})[./-]\s*(\d{1,2})[./-]\s*(\d{1,2})"
        r"(?:\s+(\d{1,2})[:-](\d{2})(?:[:-](\d{2}))?)?",
        text,
    )
    if not match:
        return None
    year, month, day, hour, minute, second = match.groups()
    if len(year) == 2:
        year = f"20{year}"
    return (
        f"{year}-{int(month):02d}-{int(day):02d} "
        f"{int(hour or 0):02d}:{int(minute or 0):02d}:{int(second or 0):02d}"
    )


def _dates(text: str) -> list[str]:
    results: list[str] = []
    pattern = re.compile(
        r"(?:\d{2}|20\d{2})[./-]\s*\d{1,2}[./-]\s*\d{1,2}"
        r"(?:\s+\d{1,2}[:-]\d{2}(?:[:-]\d{2})?)?"
    )
    for match in pattern.finditer(text):
        parsed = _date(match.group(0))
        if parsed:
            results.append(parsed)
    return results


def _value(cells: dict[str, str], *needles: str) -> str:
    for header, value in cells.items():
        normalized_header = re.sub(r"\s+", "", header)
        if any(re.sub(r"\s+", "", needle) in normalized_header for needle in needles):
            return value
    return ""


class BidpageClient:
    login_path = "/common/common_login.htm?RePage=%2Fmypage%2Fmypage_index.htm"
    list_path = "/mypage/mypage_index.htm"

    def __init__(self, config: Config) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "WithBidAI/1.0 (+authorized account collector)",
                "Accept-Language": "ko-KR,ko;q=0.9",
            }
        )
        if config.bidpage_tls_sha256:
            self.session.mount(
                f"{config.bidpage_base_url}/",
                FingerprintAdapter(config.bidpage_tls_sha256),
            )

    @staticmethod
    def _decode(response: requests.Response) -> str:
        if not response.encoding or response.encoding.lower() == "iso-8859-1":
            response.encoding = response.apparent_encoding or "utf-8"
        return response.text

    def _follow_script_redirects(self, response: requests.Response) -> requests.Response:
        for _ in range(5):
            html = self._decode(response)
            match = re.search(
                r"(?:location(?:\.href|\.replace)?\s*(?:=|\()\s*)['\"]([^'\"]+)",
                html,
                re.IGNORECASE,
            )
            if not match:
                return response
            response = self.session.get(
                urljoin(response.url, match.group(1)),
                timeout=self.config.request_timeout,
            )
            response.raise_for_status()
        return response

    def login(self) -> None:
        response = self.session.get(
            f"{self.config.bidpage_base_url}{self.login_path}",
            timeout=self.config.request_timeout,
        )
        response.raise_for_status()
        soup = BeautifulSoup(self._decode(response), "html.parser")
        form = soup.find("form", attrs={"name": "FLogin"})
        if not form:
            raise BidpageAuthenticationError("Bidpage 로그인 양식을 찾을 수 없습니다.")
        payload = {
            field.get("name"): field.get("value", "")
            for field in form.select("input[name]")
            if field.get("name")
        }
        payload.update(
            {
                "MemID": self.config.bidpage_username,
                "MemPW": self.config.bidpage_password,
            }
        )
        action = urljoin(response.url, form.get("action") or "/member/SslUp.php")
        response = self.session.post(
            action,
            data=payload,
            timeout=self.config.request_timeout,
        )
        response.raise_for_status()
        self._follow_script_redirects(response)

        check = self.session.get(
            f"{self.config.bidpage_base_url}{self.list_path}",
            timeout=self.config.request_timeout,
        )
        check.raise_for_status()
        html = self._decode(check)
        if 'name="FLogin"' in html or "회원로그인" in html:
            raise BidpageAuthenticationError(
                "Bidpage 로그인에 실패했습니다. GitHub Secret 값을 확인하세요."
            )
        log.info("Bidpage 로그인 완료")

    def parse_list(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for link in soup.select('a[href*="mypage_bid_contents.htm"]'):
            href = urljoin(
                f"{self.config.bidpage_base_url}{self.list_path}",
                link.get("href", ""),
            )
            query = parse_qs(urlparse(href).query)
            bidpage_no = (query.get("BidNo") or [""])[0]
            bidpage_seq = (query.get("BidNoSeq") or ["0"])[0]
            if not bidpage_no or (bidpage_no, bidpage_seq) in seen:
                continue
            seen.add((bidpage_no, bidpage_seq))
            row = link.find_parent("tr")
            if not row:
                continue
            table = row.find_parent("table")
            header_nodes = table.select("thead th") if table else []
            if table and not header_nodes:
                for candidate in table.find_all("tr"):
                    direct_headers = candidate.find_all("th", recursive=False)
                    if direct_headers:
                        header_nodes = direct_headers
                        break
            headers = [_text(node) for node in header_nodes]
            values = [_text(node) for node in row.find_all(["td", "th"], recursive=False)]
            cells = dict(zip(headers, values)) if len(headers) == len(values) else {}
            row_text = _text(row)

            g2b = re.search(r"(R\d{2}BK\d+)(?:-(\d{1,3}))?", row_text, re.I)
            official_no = g2b.group(1).upper() if g2b else ""
            official_order = (g2b.group(2) or "000") if g2b else "000"
            if not official_no:
                number_text = _value(cells, "공고명", "공고번호") or row_text
                candidates = re.findall(r"[A-Z]\w+(?:[-/]\w+){1,}|\d{8,}", number_text, re.I)
                official_no = next((value for value in candidates if value != bidpage_no), "")

            title_cell = _value(cells, "공고명")
            title = _text(link) or title_cell
            base_text = _value(cells, "기초금액")
            estimated_text = _value(cells, "추정가격")
            combined_amounts = _money_values(base_text) if base_text == estimated_text else []
            type_match = re.search(r"조달청\s*(공사|용역|물품|외자)", row_text)
            bid_type = (
                type_match.group(1) if type_match
                else _value(cells, "공고구분", "입찰구분") or "물품"
            )
            schedule_text = _value(cells, "개찰일")
            schedule_dates = _dates(schedule_text)
            notice_agency = (
                "나라장터" if g2b
                else _value(cells, "공고기관") or "Bidpage"
            )
            results.append(
                {
                    "bidpage_bid_no": bidpage_no,
                    "bidpage_bid_seq": bidpage_seq,
                    "official_bid_no": official_no,
                    "official_bid_order": official_order,
                    "title": title,
                    "notice_agency": notice_agency,
                    "agency": "",
                    "demand_agency": _value(cells, "수요기관"),
                    "bid_type": bid_type,
                    "base_amount": combined_amounts[0] if combined_amounts else _money(base_text),
                    "estimated_amount": (
                        combined_amounts[1] if len(combined_amounts) > 1
                        else _money(estimated_text) if estimated_text != base_text else None
                    ),
                    "posted_at": _date(_value(cells, "입력일", "공고일")),
                    "deadline_at": _date(_value(cells, "투찰마감", "입찰마감")),
                    "opening_at": schedule_dates[0] if schedule_dates else None,
                    "participation_deadline_at": (
                        schedule_dates[1] if len(schedule_dates) > 1 else None
                    ),
                    "detail_url": href,
                }
            )
        return results

    @staticmethod
    def parse_detail(html: str) -> dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")
        fields: dict[str, str] = {}
        for row in soup.find_all("tr"):
            cells = row.find_all(["th", "td"], recursive=False)
            for index, cell in enumerate(cells[:-1]):
                if cell.name != "th" or cells[index + 1].name != "td":
                    continue
                fields[re.sub(r"\s+", "", _text(cell))] = _text(cells[index + 1])

        def field_value(*labels: str) -> str:
            for label in labels:
                normalized = re.sub(r"\s+", "", label)
                for key, value in fields.items():
                    if normalized == key or normalized in key:
                        return value
            return ""

        return {
            "agency": field_value("공고기관(발주처)", "발주기관", "발주처"),
            "demand_agency": field_value("수요기관(수요처)", "수요기관", "수요처"),
            "deadline_at": _date(field_value("투찰마감일시", "입찰마감일시")),
            "opening_at": _date(field_value("입찰(개찰)일시", "개찰일시")),
            "participation_deadline_at": _date(
                field_value("참가등록마감일", "참가신청마감일")
            ),
        }

    def enrich_details(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        enriched: list[dict[str, Any]] = []
        for index, item in enumerate(items):
            try:
                response = self.session.get(
                    item["detail_url"], timeout=self.config.request_timeout
                )
                response.raise_for_status()
                details = self.parse_detail(self._decode(response))
                enriched.append({
                    **item,
                    **{key: value for key, value in details.items() if value},
                })
            except requests.RequestException as exc:
                log.warning(
                    "Bidpage 상세정보 수집 실패 (%s): %s",
                    item.get("bidpage_bid_no"), exc,
                )
                enriched.append(item)
            if index + 1 < len(items):
                time.sleep(0.15)
        return enriched

    def search(self, start_at: datetime, end_at: datetime) -> list[dict[str, Any]]:
        self.login()
        base_params = {
                "Mtype": "1",
                "Kind_type": "1",
                "rdoFindDate": "1",
                "txtSDate": start_at.strftime("%Y-%m-%d"),
                "txtEDate": end_at.strftime("%Y-%m-%d"),
                "lstViewList": str(self.config.bidpage_page_size),
        }
        results_by_id: dict[tuple[str, str], dict[str, Any]] = {}
        for page in range(1, self.config.bidpage_max_pages + 1):
            response = self.session.get(
                f"{self.config.bidpage_base_url}{self.list_path}",
                params={**base_params, "CurSelPage": str(page)},
                timeout=self.config.request_timeout,
            )
            response.raise_for_status()
            html = self._decode(response)
            if 'name="FLogin"' in html or "회원로그인" in html:
                raise BidpageAuthenticationError("Bidpage 세션이 만료되었습니다.")
            page_results = self.parse_list(html)
            for item in page_results:
                identity = (item["bidpage_bid_no"], item["bidpage_bid_seq"])
                results_by_id[identity] = item
            log.info("Bidpage 맞춤공고 %s페이지: %s건", page, len(page_results))

            next_page = page + 1
            soup = BeautifulSoup(html, "html.parser")
            has_next = any(
                re.search(rf"(?:[?&])CurSelPage={next_page}(?:&|$)", link.get("href", ""))
                for link in soup.find_all("a", href=True)
            )
            if not has_next:
                break

        results = list(results_by_id.values())
        log.info("Bidpage 맞춤공고 %s건 수집", len(results))
        return results
