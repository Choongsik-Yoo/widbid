import unittest

from bidpage_client import BidpageClient
from config import Config
from normalizer import normalize, normalize_bidpage


class BidpageCollectorTest(unittest.TestCase):
    def setUp(self):
        self.config = Config(
            data_api_key="test",
            supabase_url="https://example.supabase.co",
            supabase_service_key="test",
        )

    def test_g2b_repost_uses_same_canonical_identity(self):
        g2b = normalize({
            "bidNtceNo": "R26BK01819904",
            "bidNtceOrd": "000",
            "bidNtceNm": "컴퓨터 구매",
            "bsnsDivNm": "물품",
        })
        repost = normalize_bidpage({
            "bidpage_bid_no": "2026111030886",
            "bidpage_bid_seq": "0",
            "official_bid_no": "R26BK01819904",
            "official_bid_order": "000",
            "title": "컴퓨터 구매",
            "bid_type": "물품",
            "detail_url": "https://guro.bidpage.co.kr/mypage/detail",
        })
        identity = lambda bid: (
            bid["canonical_source"], bid["bid_no"],
            bid["bid_order"], bid["bid_type"],
        )
        self.assertEqual(identity(g2b), identity(repost))
        self.assertEqual(repost["source_record"]["source_system"], "bidpage")

    def test_non_g2b_notice_keeps_bidpage_identity(self):
        bid = normalize_bidpage({
            "bidpage_bid_no": "2026111050346",
            "bidpage_bid_seq": "0",
            "official_bid_no": "S0030-20-20261110-00003",
            "title": "민간 전산장비 구매",
            "detail_url": "https://guro.bidpage.co.kr/mypage/detail",
        })
        self.assertEqual(bid["canonical_source"], "bidpage")
        self.assertEqual(bid["bid_no"], "S0030-20-20261110-00003")

    def test_parse_list_extracts_g2b_fields_without_credentials(self):
        html = """
        <table>
          <thead><tr>
            <th>공고명/공고번호</th><th>공고기관</th><th>기초금액</th>
            <th>추정가격</th><th>입력일</th><th>투찰마감일시</th><th>개찰일시</th>
          </tr></thead>
          <tbody><tr>
            <td><a href="/mypage/mypage_bid_contents.htm?BidNo=2026111030886&amp;BidNoSeq=0">GPU 서버 구매</a>
                조달청 물품 R26BK01819904-000 호</td>
            <td>테스트기관</td><td>110,000,000원</td><td>100,000,000원</td>
            <td>2026-11-10 09:15</td><td>2026-11-14 10:00</td><td>2026-11-14 11:00</td>
          </tr></tbody>
        </table>
        """
        rows = BidpageClient(self.config).parse_list(html)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["official_bid_no"], "R26BK01819904")
        self.assertEqual(rows[0]["official_bid_order"], "000")
        self.assertEqual(rows[0]["notice_agency"], "나라장터")
        self.assertEqual(rows[0]["base_amount"], 110000000)
        self.assertEqual(rows[0]["deadline_at"], "2026-11-14 10:00:00")

    def test_parse_legacy_table_combines_amounts_and_two_digit_dates(self):
        html = """
        <table>
          <tr><th>공고명 공고번호</th><th>공고기관</th>
              <th>기초금액 추정가격</th><th>입력일</th>
              <th>투찰 마감일시</th><th>개찰일시 참가신청마감일</th></tr>
          <tr><td><a href="/mypage/mypage_bid_contents.htm?BidNo=1&amp;BidNoSeq=0">서버 구매</a>
              조달청 물품 R26BK01819904-000 호</td><td>테스트기관</td>
              <td>465,000,000 422,727,273</td><td>26-11-10 00-00-00</td>
              <td>26-11-24 10:00</td><td>26-11-24 11:00 26-11-23 18:00</td></tr>
        </table>
        """
        row = BidpageClient(self.config).parse_list(html)[0]
        self.assertEqual(row["base_amount"], 465000000)
        self.assertEqual(row["estimated_amount"], 422727273)
        self.assertEqual(row["posted_at"], "2026-11-10 00:00:00")
        self.assertEqual(row["deadline_at"], "2026-11-24 10:00:00")
        self.assertEqual(row["opening_at"], "2026-11-24 11:00:00")
        self.assertEqual(
            row["participation_deadline_at"], "2026-11-23 18:00:00"
        )

    def test_parse_detail_uses_explicit_agency_and_schedule_fields(self):
        html = """
        <table>
          <tr><th>공고기관(발주처)</th><td>테스트 발주기관</td>
              <th>수요기관(수요처)</th><td>테스트 수요기관</td></tr>
          <tr><th>투찰마감일시</th><td>2026-11-16 12:00:00</td></tr>
          <tr><th>참가등록마감일</th><td>2026-11-16 10:00:00</td></tr>
          <tr><th>입찰(개찰) 일시</th><td>2026-11-18 14:00:00</td></tr>
        </table>
        """
        detail = BidpageClient.parse_detail(html)
        self.assertEqual(detail["agency"], "테스트 발주기관")
        self.assertEqual(detail["demand_agency"], "테스트 수요기관")
        self.assertEqual(detail["deadline_at"], "2026-11-16 12:00:00")
        self.assertEqual(
            detail["participation_deadline_at"], "2026-11-16 10:00:00"
        )
        self.assertEqual(detail["opening_at"], "2026-11-18 14:00:00")


if __name__ == "__main__":
    unittest.main()
