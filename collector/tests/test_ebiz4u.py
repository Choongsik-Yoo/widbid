from datetime import datetime
import unittest

from config import Config
from ebiz4u_client import Ebiz4uClient
from normalizer import (
    canonical_ebiz4u_bid_no,
    normalize_bidpage,
    normalize_ebiz4u,
)


class Ebiz4uCollectorTest(unittest.TestCase):
    def setUp(self):
        self.config = Config(
            data_api_key="test",
            supabase_url="https://example.supabase.co",
            supabase_service_key="test",
        )

    def test_canonical_number_matches_bidpage_display_number(self):
        self.assertEqual(
            canonical_ebiz4u_bid_no("S0030202026111200045"),
            "S0030-20-20261112-00045",
        )
        direct = normalize_ebiz4u({
            "rfq_no": "S0030202026111200045",
            "title": "PC 구매",
            "bid_type": "물품",
        })
        repost = normalize_bidpage({
            "bidpage_bid_no": "202611120045",
            "official_bid_no": "S0030-20-20261112-00045",
            "title": "PC 구매",
            "bid_type": "물품",
        })
        identity = lambda bid: (
            bid["canonical_source"], bid["bid_no"],
            bid["bid_order"], bid["bid_type"],
        )
        self.assertEqual(identity(direct), identity(repost))
        self.assertEqual(direct["source_record"]["source_system"], "ebiz4u")
        self.assertEqual(repost["source_record"]["source_system"], "bidpage")

    def test_alphanumeric_ebiz4u_prefix_is_supported(self):
        self.assertEqual(
            canonical_ebiz4u_bid_no("A01MM202026111200001"),
            "A01MM-20-20261112-00001",
        )

    def test_parse_public_list(self):
        html = """
        <table>
          <tr><th>입찰명</th><th>구매담당</th><th>공고일</th><th>마감일</th><th>상태</th></tr>
          <tr>
            <td><a href="javascript:doView('S0030202026111200045','u.ebiz4u')">
              <span class="subject">성균관대학교산학협력단</span>[컴퓨터] iMac 구매
            </a></td>
            <td>담당자</td><td>2026-11-12<span>14:37</span></td>
            <td>2026-11-13<span>13:00</span></td><td>견적공고중</td>
          </tr>
        </table>
        """
        item = Ebiz4uClient(self.config).parse_list(html)[0]
        self.assertEqual(item["rfq_no"], "S0030202026111200045")
        self.assertEqual(item["agency"], "성균관대학교산학협력단")
        self.assertEqual(item["title"], "[컴퓨터] iMac 구매")
        self.assertEqual(item["posted_at"], "2026-11-12 14:37:00")
        self.assertEqual(item["deadline_at"], "2026-11-13 13:00:00")
        self.assertIn("rfqNo=S0030202026111200045", item["detail_url"])

    def test_parse_public_detail(self):
        html = """
        <table>
          <tr><td>입찰초청서번호</td><td>S0030202026111200045</td>
              <td>게시일시</td><td>2026-11-12 14:37</td></tr>
          <tr><td>입찰명</td><td>iMac 구매</td></tr>
          <tr><td>입찰종류1</td><td>일반경쟁입찰</td>
              <td>입찰종류2</td><td>일반경쟁</td></tr>
          <tr><td>입찰 마감일시</td><td>2026-11-13 13:00</td></tr>
          <tr><td>비고</td><td>현장 납품 필수</td></tr>
          <tr><td>구매사</td><td>성균관대학교</td></tr>
        </table>
        <table>
          <tr><td colspan="5">물품 내용</td></tr>
          <tr><td>물품명</td><td>모델명</td><td>수량</td><td>납품요구일</td><td>납품장소</td></tr>
          <tr><td>PC</td><td>iMac</td><td>1.00</td><td>2026-11-25</td><td>연구실</td></tr>
        </table>
        """
        detail = Ebiz4uClient.parse_detail(html)
        self.assertEqual(detail["rfq_no"], "S0030202026111200045")
        self.assertEqual(detail["agency"], "성균관대학교")
        self.assertEqual(detail["deadline_at"], "2026-11-13 13:00:00")
        self.assertEqual(detail["contract_method"], "일반경쟁입찰 / 일반경쟁")
        self.assertEqual(detail["notice_text"], "현장 납품 필수")
        self.assertEqual(detail["items"][0]["model"], "iMac")


if __name__ == "__main__":
    unittest.main()
