from datetime import datetime
import unittest

from config import Config
from g2b_client import G2BClient
from scorer import analyze_bid


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "response": {
                "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE"},
                "body": {
                    "totalCount": 2,
                    "items": [
                        {"bidNtceNo": "R26BK00000001", "bidNtceOrd": "000", "prtcptPsblRgnNm": "서울특별시"},
                        {"bidNtceNo": "R26BK00000001", "bidNtceOrd": "000", "prtcptPsblRgnNm": "경기도"},
                    ],
                },
            }
        }


class FakeSession:
    def get(self, *args, **kwargs):
        return FakeResponse()


class RegionTests(unittest.TestCase):
    def test_g2b_participation_regions_are_grouped_by_notice(self):
        client = G2BClient(Config(
            data_api_key="test",
            supabase_url="https://example.supabase.co",
            supabase_service_key="test",
        ))
        client.session = FakeSession()
        regions = client.participation_regions(
            datetime(2026, 11, 11), datetime(2026, 11, 12)
        )
        self.assertEqual(
            regions[("R26BK00000001", "000")], ["서울특별시", "경기도"]
        )

    def test_scorer_marks_region_restriction(self):
        analysis = analyze_bid({
            "raw_data": {"participation_regions": ["서울특별시"]},
            "matched_keywords": ["서버"],
        })
        self.assertEqual(analysis["region_limit"], "서울특별시")
        self.assertTrue(any("지역 제한" in risk for risk in analysis["risk_factors"]))

    def test_empty_official_region_result_means_nationwide(self):
        analysis = analyze_bid({"raw_data": {"participation_regions": []}})
        self.assertEqual(analysis["region_limit"], "전국")

    def test_missing_region_data_is_not_assumed_nationwide(self):
        analysis = analyze_bid({"raw_data": {}})
        self.assertEqual(analysis["region_limit"], "확인 필요")

    def test_list_region_judgment_basis_is_marked_as_restricted(self):
        analysis = analyze_bid({
            "raw_data": {"rgnLmtBidLocplcJdgmBssNm": "본사소재지"}
        })
        self.assertIn("지역제한", analysis["region_limit"])

    def test_region_analysis_keeps_deadline_scoring(self):
        analysis = analyze_bid({
            "deadline_at": "2026-11-20T10:00:00+09:00",
            "raw_data": {"participation_regions": []},
        })
        self.assertEqual(len(analysis["score_breakdown"]), 7)


if __name__ == "__main__":
    unittest.main()
