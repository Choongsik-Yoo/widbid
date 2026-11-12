# WithBid AI

나라장터 입찰공고를 키워드로 수집하고 회사 조건에 맞춰 적합도를 평가하며, 관심 공고와 업무 진행 상태를 팀이 함께 관리하는 GitHub Pages 기반 웹앱입니다.

- 운영 사이트: https://choongsik-yoo.github.io/widbid/
- 프런트엔드: 정적 HTML, CSS, JavaScript
- 데이터베이스·인증: Supabase PostgreSQL, Google OAuth
- 수집기: Python, 나라장터 API, 로그인 기반 Bidpage 및 eBiz4u 공개공고 수집
- 자동화: QNAP NAS, GitHub Actions

QNAP NAS 운영 시에는 `collector/Dockerfile`로 생성한 ARM64 이미지를 Container
Station에서 실행할 수 있습니다. 컨테이너는 한국 시간 매일 오전 8시에 수집하며,
최초 실행 시 한 번 즉시 수집합니다. NAS 배포 파일은 `deploy/nas`에 있습니다.

## 주요 기능

- 대시보드 요약과 공고 검색·필터·정렬
- 공고 상세정보와 적합도 근거
- 관심 공고, 상태, 메모, 담당자, 체크리스트 공동 저장
- 6열 업무 보드
- 검색어 그룹과 회사 평가 기준 관리
- 관리자 전용 사용자 허용 목록 관리
- 매일 오전 8시(KST) 나라장터 공고 자동 수집

## 운영 구성

웹앱은 GitHub Pages에 배포되며, 배포 시 GitHub Actions가 저장소 변수와 secret으로 `config.js`를 생성합니다. 운영용 Supabase URL이나 키를 저장소 파일에 직접 커밋하지 않습니다.

필요한 GitHub 설정은 다음과 같습니다.

| 종류 | 이름 | 용도 |
| --- | --- | --- |
| Variable | `SUPABASE_URL` | 웹앱과 수집기가 사용하는 Supabase 프로젝트 URL |
| Variable | `G2B_BASE_URL` | 나라장터 API 기본 URL |
| Secret | `SUPABASE_ANON_KEY` | 브라우저용 Supabase anon key |
| Secret | `SUPABASE_SERVICE_ROLE_KEY` | 수집기용 service role key |
| Secret | `DATA_GO_KR_API_KEY` | 공공데이터포털 API 키 |
| Variable | `BIDPAGE_ENABLED` | Bidpage 수집 사용 여부 (`true`/`false`) |
| Variable | `BIDPAGE_BASE_URL` | `https://guro.bidpage.co.kr` |
| Variable | `BIDPAGE_TLS_SHA256` | Bidpage 서버 인증서 SHA-256 지문 |
| Secret | `BIDPAGE_USERNAME` | Bidpage 로그인 아이디 |
| Secret | `BIDPAGE_PASSWORD` | Bidpage 로그인 비밀번호 |
| Variable | `EBIZ4U_ENABLED` | eBiz4u 공개공고 직접 수집 여부 (`true`/`false`) |
| Variable | `EBIZ4U_BASE_URL` | `https://www.ebiz4u.co.kr` |

Bidpage 로그인 정보는 저장소 파일이나 GitHub Variable이 아니라 반드시
Repository Secret으로 등록합니다. 수집기는 비밀번호와 세션 쿠키를 로그나
Supabase 원본 데이터에 기록하지 않습니다. `BIDPAGE_ENABLED`가 `true`일 때만
로그인을 시도하며, Bidpage 장애 시 나라장터 수집은 계속되고 실행 결과는
`partial`로 기록됩니다.

Bidpage 서버의 인증서 체인 검증이 실패하는 환경에서는 TLS 검증을 끄지 않고
`BIDPAGE_TLS_SHA256`에 등록된 서버 인증서 지문을 대조합니다. 인증서가 갱신되어
지문이 달라지면 수집을 중단하므로 새 인증서를 확인한 뒤 Variable을 갱신해야 합니다.

Bidpage 이용 권한과 운영사 약관의 범위 안에서만 이 기능을 사용해야 합니다.

eBiz4u 수집기는 공개 공고 목록과 공개 상세 페이지를 직접 조회하므로 로그인
정보가 필요하지 않습니다. Bidpage 목록에 함께 표시되는 eBiz4u 공고는 Bidpage
수집 단계에서 제외하고 eBiz4u 전용 수집기만 처리합니다. 기존에 Bidpage 출처로
저장된 eBiz4u 공고는 고유번호를 정규화하여 직접 수집 공고와 통합합니다. NAS
배포에서는 `EBIZ4U_ENABLED=true`가 기본으로 지정됩니다.

Bidpage의 기타 민간·기관 공고는 상세 원문 프레임에 실제 기관 URL이 명시된
경우 해당 URL을 공고 바로가기 주소로 저장합니다. 개별 원문 주소가 제공되지
않는 공고는 잘못된 주소를 추정하지 않고 Bidpage 상세 주소를 대체 경로로
유지합니다.

Supabase의 Google provider와 URL Configuration에는 운영 사이트 URL 및 OAuth callback에 사용되는 URL이 등록되어 있어야 합니다. 로그인한 Google 계정은 `allowed_users`에 활성 상태로 등록된 경우에만 데이터를 조회할 수 있습니다.

## 데이터베이스 migration

`supabase/migrations`의 SQL은 다음 순서로 적용합니다.

1. `001_initial_schema.sql`: 공고, 분석, 키워드, 개인 저장 데이터 기본 스키마
2. `002_data_api_grants.sql`: 기존 프로젝트의 Data API 권한 보강
3. `002_update_keyword_groups.sql`: 검색어 그룹과 키워드 보강
4. `003_team_auth_and_shared_work.sql`: 허용 사용자, 팀 공동 상태, 체크리스트, 활동 기록 및 RLS 정책
5. `004_correct_budget_and_bid_datetimes.sql`: 배정예산 컬럼 추가 및 기존 공고의 KST 일시 복원
6. `005_add_bid_sources.sql`: 복수 공고 출처와 공식 공고번호 기반 중복 제거
7. `006_add_notice_agency_and_participation_deadline.sql`: 공고기관 및 참가신청마감일 저장
8. `007_add_ebiz4u_source_identity.sql`: 기존 Bidpage의 eBiz4u 공고를 직접 수집 출처와 통합

운영 프로젝트에는 배포 전에 최신 migration까지 순서대로 적용해야 합니다. 이미 적용한 migration 파일은 수정하는 대신 새 번호의 migration을 추가합니다.

## GitHub Actions

- `Validate project`: Python 수집기 컴파일, 공고번호 정규화, JavaScript 구문, 필수 웹 파일을 검사합니다.
- `Deploy GitHub Pages`: `main`의 웹 자산이 바뀌면 Pages에 배포합니다.
- `Collect G2B bids`: 매일 `23:00 UTC`(한국 시간 오전 8시)에 나라장터, 활성화된 Bidpage 및 eBiz4u 공고를 수집하며 수동 실행도 지원합니다.

배포 문제를 확인할 때는 Actions에서 `Validate project`와 `Deploy GitHub Pages`가 모두 성공했는지 확인한 뒤, 운영 사이트의 `app.js`가 `main`과 일치하는지 점검합니다.

## 로컬 확인

정적 파일이므로 별도 빌드 과정은 없습니다. OAuth redirect와 Supabase 연결을 포함한 전체 동작은 등록된 URL에서 확인해야 합니다.

```bash
node --check app.js
python -m compileall -q collector
```

로컬 화면만 확인하려면 저장소 루트에서 정적 HTTP 서버를 실행합니다. 실제 Supabase를 연결할 때는 로컬 전용 `config.js`를 사용하고 운영 key나 service role key를 커밋하지 마세요.
