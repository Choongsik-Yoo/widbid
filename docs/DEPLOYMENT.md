# 배포 체크리스트

## 1. Supabase

- 새 Supabase 프로젝트 생성
- SQL Editor에서 `supabase/migrations/001_initial_schema.sql` 실행
- Project URL 복사
- anon public key 복사
- service_role key 복사

## 2. 공공데이터포털

- 조달청 나라장터 입찰공고정보서비스 활용신청
- 일반 인증키(Encoding 또는 Decoding 여부 확인) 발급
- 실제 활용신청 오퍼레이션 URL 확인

## 3. GitHub 저장소 설정

Settings → Secrets and variables → Actions에 등록:

### Secrets

| 이름 | 값 |
|---|---|
| `DATA_GO_KR_API_KEY` | 공공데이터포털 인증키 |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service_role 키 |
| `SUPABASE_ANON_KEY` | Supabase anon 키 |

### Variables

| 이름 | 값 |
|---|---|
| `SUPABASE_URL` | `https://xxxx.supabase.co` |
| `G2B_BASE_URL` | 활용신청한 나라장터 API 오퍼레이션 URL |

`G2B_BASE_URL`을 등록하지 않으면 수집기 기본 URL을 사용합니다.

## 4. GitHub Pages

- Settings → Pages
- Source: GitHub Actions(권장)
- Actions → Deploy GitHub Pages → Run workflow

`Deploy from a branch`를 사용한다면 Branch는 `main`, Folder는 `/(root)`로
선택합니다. 루트 `index.html`이 앱을 직접 실행합니다.

## 5. 최초 수집

- Actions → Collect G2B bids
- Run workflow
- 실행 로그와 Supabase `collection_runs` 확인
- 대시보드에서 실제 공고 표시 확인

## 6. 운영 확인

- 오전 8시 이후 `collection_runs` 성공 여부 확인
- 정정공고가 갱신되는지 확인
- 나라장터 원문 링크 확인
- 마감일과 금액이 원문과 일치하는지 표본 검사
- API 요청 제한과 실패율 확인

## 현재 MVP 범위

현재 수집기는 기본 공고정보와 키워드 매칭까지 구현되어 있습니다. 첨부파일
다운로드, HWP/PDF 파싱, AI 분석 실행은 데이터베이스와 화면 구조만 준비되어
있으며 다음 개발 단계에서 수집 파이프라인에 연결해야 합니다.
