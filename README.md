# WithBid AI

나라장터 입찰공고를 키워드로 수집하고, 회사 조건에 맞춰 적합도를 평가하며,
검토 상태와 관심 공고를 관리하는 GitHub Pages 기반 웹앱입니다.

## 주요 기능

- 대시보드 요약
- 공고 검색, 필터, 정렬
- 공고 상세정보 및 적합도 근거
- 관심 공고와 담당자 메모
- 업무 상태 관리
- 검색어 그룹과 회사 기준 관리
- 매일 오전 8시(KST) 자동수집
- Supabase PostgreSQL 연동

## 빠른 실행

별도 빌드 없이 저장소 루트를 정적 웹서버로 열 수 있습니다.

```bash
python -m http.server 8080
```

브라우저에서 `http://localhost:8080`으로 접속합니다. Supabase 설정이 없으면
내장된 데모 데이터와 브라우저 localStorage를 사용합니다.

## Supabase 연결

1. Supabase 프로젝트를 만듭니다.
2. SQL Editor에서 `supabase/migrations/001_initial_schema.sql`을 실행합니다.
3. `config.example.js`를 `config.js`로 복사합니다.
4. 공개용 Supabase URL과 anon key를 입력합니다.
5. GitHub 저장소 Settings → Secrets and variables → Actions에 다음 값을 등록합니다.

```text
DATA_GO_KR_API_KEY
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
```

`SUPABASE_SERVICE_ROLE_KEY`와 공공데이터 API 키는 절대 웹 파일에 넣지 마세요.

## GitHub Pages 배포

1. 이 프로젝트를 GitHub 저장소에 push합니다.
2. 권장 방식은 저장소 Settings → Pages → Source를 `GitHub Actions`로 선택하는 것입니다.
3. Actions 탭에서 `Deploy GitHub Pages`를 실행합니다.
4. 배포 주소는 `https://<아이디>.github.io/<저장소명>/`입니다.

Pages Source가 `Deploy from a branch`로 설정되어 있어도 루트 `index.html`이
앱을 직접 실행합니다. 첫 화면에 README가 나온다면 GitHub 저장소의 기본
브랜치 루트에 `index.html`, `app.js`, `styles.css`가 있는지 확인하세요.

## 자동수집

`.github/workflows/collect-bids.yml`은 매일 23:00 UTC, 즉 다음 날 오전
8시 KST에 실행됩니다. GitHub Actions의 스케줄은 수 분 늦게 시작될 수 있습니다.

수집기는 공공데이터포털의 나라장터 입찰공고정보서비스를 사용하도록 만들어져
있으며, 실제 API의 오퍼레이션 경로가 발급받은 활용신청과 다르면
`collector/config.py`의 URL을 조정해야 합니다.

## 구조

```text
index.html, app.js    GitHub Pages 웹앱
collector/            나라장터 자동수집기
supabase/migrations/  데이터베이스 스키마와 RLS
.github/workflows/    배포·수집 자동화
docs/                 운영 문서
```

## 주의

AI 분석은 최종 법률·입찰 판단이 아닙니다. 공고 상세 화면의 나라장터 원문과
첨부문서를 담당자가 반드시 확인해야 합니다.
