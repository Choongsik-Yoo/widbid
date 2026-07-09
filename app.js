const CONFIG = window.WITHBID_CONFIG || {};

const STATUS = [
  "신규", "검토중", "참여가능", "조건확인필요", "대표승인필요",
  "제안/견적준비", "투찰완료", "낙찰", "미선정", "제외", "보류"
];

const SCORE_ITEMS = [
  ["품목 적합도", 25], ["금액 적합도", 15], ["인증 충족", 20],
  ["지역 조건", 10], ["납품기한", 10], ["실적 조건", 10], ["위험요소", 10]
];

const CHECKLIST = [
  "취급 가능한 품목인가", "예산 범위가 적절한가", "필수 인증을 보유했는가",
  "지역 제한을 충족하는가", "실적 조건을 충족하는가", "납품기한 대응이 가능한가",
  "제조사 공급확약서 발급이 가능한가", "공동수급 여부를 확인했는가",
  "제출서류를 준비할 수 있는가", "특수조건·현장설치 조건을 확인했는가",
  "담당자 검토가 완료되었는가", "대표 승인이 완료되었는가"
];

const demoBids = [
  {
    id: "demo-1", bidNo: "R26BK01624350-000", title: "고성능 컴퓨터서버 구매",
    agency: "한국과학기술원", demandAgency: "한국과학기술원", category: "물품",
    contractMethod: "제한경쟁", bidMethod: "전자입찰", amount: 185000000,
    postedAt: "2026-07-09T08:43:00+09:00", deadlineAt: "2026-07-20T10:00:00+09:00",
    openingAt: "2026-07-20T11:00:00+09:00", region: "전국", score: 92,
    status: "검토중", certifications: ["정보통신공사업"], documents: ["사업자등록증", "물품공급확약서"],
    requirements: ["중소기업자", "해당 물품 납품 가능 업체"], risks: ["직접생산확인 대상 품목 여부 확인 필요"],
    summary: "GPU 연산용 고성능 서버를 구매하는 물품 입찰입니다. 품목과 예산은 회사 취급 범위에 부합하며 인증 조건의 최종 확인이 필요합니다.",
    sourceUrl: "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R26BK01624350&bidPbancOrd=000",
    keywords: ["서버", "GPU 서버", "컴퓨터"],
    breakdown: [25, 14, 17, 10, 10, 8, 8]
  },
  {
    id: "demo-2", bidNo: "R26BK01623889-000", title: "컴퓨터공학과 융합안전공학과 컴퓨터 구입",
    agency: "울산과학대학교 산학협력단", demandAgency: "울산과학대학교",
    category: "물품", contractMethod: "일반경쟁", bidMethod: "전자입찰", amount: 240000000,
    postedAt: "2026-07-08T17:02:00+09:00", deadlineAt: "2026-07-16T11:00:00+09:00",
    openingAt: "2026-07-16T12:00:00+09:00", region: "전국", score: 82,
    status: "신규", certifications: ["중소기업확인서"], documents: ["사업자등록증", "법인등기부등본"],
    requirements: ["중소기업자", "컴퓨터 납품 가능 업체"], risks: ["제조사 공급확약서 필요"],
    summary: "교육용 데스크톱과 모니터를 일괄 납품하는 공고입니다. 취급 품목에는 부합하지만 제조사 공급확약서 발급 가능 여부를 확인해야 합니다.",
    sourceUrl: "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R26BK01623889&bidPbancOrd=000",
    keywords: ["컴퓨터", "PC", "모니터"],
    breakdown: [25, 15, 15, 10, 8, 5, 4]
  },
  {
    id: "demo-3", bidNo: "R26BK01621451-000", title: "네트워크 장비 유지보수 및 교체",
    agency: "식품의약품안전처", demandAgency: "식품의약품안전처",
    category: "용역", contractMethod: "제한경쟁", bidMethod: "전자입찰", amount: 60000000,
    postedAt: "2026-07-08T15:01:00+09:00", deadlineAt: "2026-07-20T10:00:00+09:00",
    openingAt: "2026-07-20T11:00:00+09:00", region: "서울", score: 55,
    status: "조건확인필요", certifications: ["정보통신공사업"], documents: ["실적증명서"],
    requirements: ["서울특별시 소재 업체", "최근 3년 유사실적 1억 원 이상"],
    risks: ["지역 제한 확인 필요", "유사실적 기준 미달 가능성"],
    summary: "네트워크 장비 교체와 유지보수를 포함하는 용역입니다. 지역 및 실적 조건이 있어 담당자 확인이 필요합니다.",
    sourceUrl: "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R26BK01621451&bidPbancOrd=000",
    keywords: ["네트워크", "유지보수"],
    breakdown: [20, 14, 12, 3, 8, 2, 0]
  },
  {
    id: "demo-4", bidNo: "R26BK01622851-000", title: "전자칠판 및 교육용 기자재 구매",
    agency: "단국대학교 산학협력단", demandAgency: "단국대학교",
    category: "물품", contractMethod: "지명경쟁", bidMethod: "전자입찰", amount: 98000000,
    postedAt: "2026-07-07T13:08:00+09:00", deadlineAt: "2026-07-11T10:00:00+09:00",
    openingAt: "2026-07-11T11:00:00+09:00", region: "전국", score: 74,
    status: "참여가능", certifications: ["중소기업확인서"], documents: ["물품공급확약서"],
    requirements: ["전자칠판 납품 및 설치 가능 업체"], risks: ["현장설치 일정 확인 필요"],
    summary: "강의실 전자칠판과 주변기기를 납품·설치하는 공고입니다. 취급 품목과 예산이 적합하며 설치 일정을 확인해야 합니다.",
    sourceUrl: "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R26BK01622851&bidPbancOrd=000",
    keywords: ["전자칠판", "교육 기자재"],
    breakdown: [23, 14, 14, 10, 6, 4, 3]
  }
];

const state = {
  route: location.hash.slice(1) || "/dashboard",
  bids: [],
  search: "",
  category: "전체",
  status: "전체",
  score: "전체",
  due: "전체",
  saved: JSON.parse(localStorage.getItem("withbid-saved") || "[]"),
  notes: JSON.parse(localStorage.getItem("withbid-notes") || "{}"),
  checks: JSON.parse(localStorage.getItem("withbid-checks") || "{}"),
  keywordGroups: JSON.parse(localStorage.getItem("withbid-keywords") || "null") || [
    { name: "PC·컴퓨터", keywords: ["컴퓨터", "PC", "데스크톱", "노트북", "랩탑"] },
    { name: "서버·고성능장비", keywords: ["서버", "SERVER", "GPU 서버", "워크스테이션", "딥러닝"] },
    { name: "전산장비", keywords: ["전산장비", "전산기기", "전산설비", "시스템 장비"] },
    { name: "네트워크·스토리지", keywords: ["네트워크", "스토리지", "NAS", "SAN", "방화벽", "스위치"] },
    { name: "교육·강의장비", keywords: ["전자칠판", "인터랙티브 화이트보드", "LED 전광판"] }
  ]
};

const escapeHtml = (value = "") => String(value).replace(/[&<>"']/g, char => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
}[char]));

const money = value => value ? `${Number(value).toLocaleString("ko-KR")}원` : "-";
const date = value => value ? new Intl.DateTimeFormat("ko-KR", { dateStyle: "medium" }).format(new Date(value)) : "-";
const dateTime = value => value ? new Intl.DateTimeFormat("ko-KR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "-";
const daysUntil = value => Math.ceil((new Date(value).getTime() - Date.now()) / 86400000);

function splitBidNumber(bidNo, bidOrder) {
  const normalized = String(bidNo || "").trim().toUpperCase().replace(/\s+/g, "");
  const match = normalized.match(/^(R\d{2}BK\d+)(?:-(\d{1,3}))?$/);
  const number = match ? match[1] : normalized.replace(/-\d{1,3}$/, "");
  const embeddedOrder = match?.[2];
  const order = String(bidOrder ?? embeddedOrder ?? "000").replace(/\D/g, "").padStart(3, "0").slice(-3);
  return { number, order };
}

function formatBidNumber(bidNo, bidOrder) {
  const { number, order } = splitBidNumber(bidNo, bidOrder);
  return `${number}-${order}`;
}

function g2bDetailUrl(bidNo, bidOrder) {
  const { number, order } = splitBidNumber(bidNo, bidOrder);
  const query = new URLSearchParams({ bidPbancNo: number, bidPbancOrd: order });
  return `https://www.g2b.go.kr/link/PNPE027_01/single/?${query.toString()}`;
}

function scoreBadge(score) {
  if (score >= 90) return ["적극 검토", "badge-green"];
  if (score >= 70) return ["참여 가능", "badge-blue"];
  if (score >= 50) return ["확인 필요", "badge-amber"];
  return ["제외 권장", "badge-red"];
}

function statusBadge(status) {
  if (["참여가능", "낙찰"].includes(status)) return "badge-green";
  if (["조건확인필요", "대표승인필요", "제안/견적준비"].includes(status)) return "badge-amber";
  if (["제외", "미선정"].includes(status)) return "badge-red";
  if (["신규", "검토중"].includes(status)) return "badge-blue";
  return "badge-gray";
}

function persist() {
  localStorage.setItem("withbid-saved", JSON.stringify(state.saved));
  localStorage.setItem("withbid-notes", JSON.stringify(state.notes));
  localStorage.setItem("withbid-checks", JSON.stringify(state.checks));
  localStorage.setItem("withbid-keywords", JSON.stringify(state.keywordGroups));
}

async function loadBids() {
  if (!CONFIG.supabaseUrl || !CONFIG.supabaseAnonKey) {
    state.bids = demoBids;
    return;
  }
  try {
    const response = await fetch(
      `${CONFIG.supabaseUrl}/rest/v1/bids?select=*,bid_analyses(*)&order=posted_at.desc`,
      { headers: { apikey: CONFIG.supabaseAnonKey, Authorization: `Bearer ${CONFIG.supabaseAnonKey}` } }
    );
    if (!response.ok) throw new Error(`Supabase ${response.status}`);
    const rows = await response.json();
    state.bids = rows.map(mapSupabaseBid);
  } catch (error) {
    console.warn("Supabase 연결 실패, 데모 데이터를 사용합니다.", error);
    state.bids = demoBids;
  }
}

function mapSupabaseBid(row) {
  const analysis = Array.isArray(row.bid_analyses) ? row.bid_analyses[0] : row.bid_analyses || {};
  return {
    id: row.id, bidNo: formatBidNumber(row.bid_no, row.bid_order), title: row.title, agency: row.agency,
    demandAgency: row.demand_agency, category: row.bid_type, contractMethod: row.contract_method,
    bidMethod: row.bid_method, amount: row.estimated_amount || row.base_amount,
    postedAt: row.posted_at, deadlineAt: row.deadline_at, openingAt: row.opening_at,
    region: analysis.region_limit || "전국", score: analysis.fit_score || 0,
    status: row.status || "신규", certifications: analysis.required_certifications || [],
    documents: analysis.required_documents || [], requirements: analysis.qualification_requirements || [],
    risks: analysis.risk_factors || [], summary: analysis.summary || "분석 대기 중입니다.",
    sourceUrl: g2bDetailUrl(row.bid_no, row.bid_order), keywords: row.matched_keywords || [],
    breakdown: analysis.score_breakdown || [0, 0, 0, 0, 0, 0, 0]
  };
}

function layout(content) {
  const routes = [
    ["/dashboard", "▦", "대시보드"], ["/bids", "⌕", "공고 검색"],
    ["/saved", "★", "관심 공고"], ["/workflow", "⇄", "업무 보드"],
    ["/settings", "⚙", "설정"]
  ];
  return `
    <div class="app-shell">
      <header class="topbar">
        <button class="mobile-menu" data-action="menu">☰</button>
        <div class="brand">WithBid <span>AI</span></div>
        <div>공공입찰 분석 시스템</div>
        <div class="topbar-meta">${CONFIG.supabaseUrl ? "Supabase 연결됨" : "데모 모드"} · ${date(new Date())}</div>
      </header>
      <div class="layout">
        <aside class="sidebar" id="sidebar">
          ${routes.map(([path, icon, label]) => `
            <button class="nav-button ${state.route.startsWith(path) ? "active" : ""}" data-route="${path}">
              <span>${icon}</span><span>${label}</span>
            </button>`).join("")}
        </aside>
        <main class="main">${content}</main>
      </div>
    </div>`;
}

function header(title, description, action = "") {
  return `<div class="page-header"><div><h1>${title}</h1><p>${description}</p></div>${action}</div>`;
}

function bidRows(bids) {
  if (!bids.length) return `<tr><td colspan="9" class="empty">조건에 맞는 공고가 없습니다.</td></tr>`;
  return bids.map(bid => {
    const [label, color] = scoreBadge(bid.score);
    return `<tr>
      <td><span class="score">${bid.score}</span><br><span class="badge ${color}">${label}</span></td>
      <td><button class="title-link" data-route="/bids/${bid.id}">${escapeHtml(bid.title)}</button><br>
        <small>${escapeHtml(bid.bidNo)}</small></td>
      <td>${escapeHtml(bid.agency)}</td>
      <td>${money(bid.amount)}</td>
      <td>${date(bid.deadlineAt)}<br><small>D${daysUntil(bid.deadlineAt) >= 0 ? "-" : "+"}${Math.abs(daysUntil(bid.deadlineAt))}</small></td>
      <td>${escapeHtml(bid.region)}</td>
      <td><span class="badge ${statusBadge(bid.status)}">${escapeHtml(bid.status)}</span></td>
      <td><button class="btn btn-secondary" data-action="save" data-id="${bid.id}">${state.saved.includes(bid.id) ? "★" : "☆"}</button></td>
    </tr>`;
  }).join("");
}

function bidTable(bids) {
  return `<div class="table-wrap"><table>
    <thead><tr><th>적합도</th><th>공고명</th><th>발주기관</th><th>예산</th><th>마감일</th><th>지역</th><th>상태</th><th>관심</th></tr></thead>
    <tbody>${bidRows(bids)}</tbody>
  </table></div>`;
}

function dashboard() {
  const due7 = state.bids.filter(b => daysUntil(b.deadlineAt) >= 0 && daysUntil(b.deadlineAt) <= 7).length;
  const fit = state.bids.filter(b => b.score >= 70).length;
  const review = state.bids.filter(b => b.risks.length || b.status === "조건확인필요").length;
  return layout(`
    ${header("대시보드", "오늘 확인해야 할 공고와 업무 현황입니다.",
      `<button class="btn btn-primary" data-route="/bids">공고 검색</button>`)}
    ${!CONFIG.supabaseUrl ? `<div class="notice">현재 데모 데이터로 실행 중입니다. 실제 운영 전 Supabase와 나라장터 API를 연결하세요.</div>` : ""}
    <section class="cards">
      <article class="metric"><div class="metric-label">전체 공고</div><div class="metric-value">${state.bids.length}</div><div class="metric-note">수집된 공고</div></article>
      <article class="metric"><div class="metric-label">마감 7일 이내</div><div class="metric-value">${due7}</div><div class="metric-note">우선 확인 필요</div></article>
      <article class="metric"><div class="metric-label">참여 가능성 높음</div><div class="metric-value">${fit}</div><div class="metric-note">70점 이상</div></article>
      <article class="metric"><div class="metric-label">조건 확인 필요</div><div class="metric-value">${review}</div><div class="metric-note">위험요소 포함</div></article>
      <article class="metric"><div class="metric-label">관심 공고</div><div class="metric-value">${state.saved.length}</div><div class="metric-note">담당자 저장</div></article>
    </section>
    <section class="panel">
      <div class="panel-title"><h2>우선 검토 공고</h2><button class="btn btn-secondary" data-route="/bids">전체 보기</button></div>
      ${bidTable([...state.bids].sort((a,b) => b.score-a.score).slice(0,5))}
    </section>
    <div class="footer-note">AI 분석은 참고자료입니다. 참여 결정 전 나라장터 원문과 첨부문서를 반드시 확인하세요.</div>
  `);
}

function filteredBids() {
  const q = state.search.trim().toLowerCase();
  return state.bids.filter(b => {
    const haystack = [b.title, b.bidNo, b.agency, b.demandAgency, ...b.keywords].join(" ").toLowerCase();
    const due = daysUntil(b.deadlineAt);
    return (!q || haystack.includes(q))
      && (state.category === "전체" || b.category === state.category)
      && (state.status === "전체" || b.status === state.status)
      && (state.score === "전체" || (state.score === "70+" ? b.score >= 70 : b.score < 70))
      && (state.due === "전체" || (state.due === "7" ? due >= 0 && due <= 7 : due >= 0 && due <= 3));
  }).sort((a,b) => b.score-a.score);
}

function bidsPage() {
  return layout(`
    ${header("공고 검색", "키워드와 업무조건으로 나라장터 공고를 찾습니다.")}
    <section class="panel">
      <div class="filters">
        <input class="field" id="search" value="${escapeHtml(state.search)}" placeholder="공고명, 기관, 공고번호, 키워드">
        <select class="select" id="category">
          ${["전체","물품","용역","공사","외자"].map(x => `<option ${state.category===x?"selected":""}>${x}</option>`).join("")}
        </select>
        <select class="select" id="filter-status">
          ${["전체",...STATUS].map(x => `<option ${state.status===x?"selected":""}>${x}</option>`).join("")}
        </select>
        <select class="select" id="score">
          <option ${state.score==="전체"?"selected":""} value="전체">전체 점수</option>
          <option ${state.score==="70+"?"selected":""} value="70+">70점 이상</option>
          <option ${state.score==="under"?"selected":""} value="under">70점 미만</option>
        </select>
        <select class="select" id="due">
          <option value="전체">전체 마감일</option><option value="3" ${state.due==="3"?"selected":""}>3일 이내</option>
          <option value="7" ${state.due==="7"?"selected":""}>7일 이내</option>
        </select>
        <button class="btn btn-primary" data-action="search">검색</button>
      </div>
      <div class="panel-title"><h2>검색 결과 ${filteredBids().length}건</h2><span>적합도 높은 순</span></div>
      ${bidTable(filteredBids())}
    </section>
  `);
}

function detailPage(id) {
  const bid = state.bids.find(b => b.id === id);
  if (!bid) return layout(`${header("공고 없음", "해당 공고를 찾을 수 없습니다.")}<button class="btn btn-primary" data-route="/bids">목록으로</button>`);
  const [scoreLabel, scoreColor] = scoreBadge(bid.score);
  const checks = state.checks[id] || [];
  return layout(`
    ${header(escapeHtml(bid.title), `${escapeHtml(bid.bidNo)} · ${escapeHtml(bid.category)}`,
      `<button class="btn btn-secondary" data-route="/bids">목록으로</button>`)}
    <div class="detail-grid">
      <div>
        <section class="panel">
          <div class="panel-title"><h2>기본 정보</h2><a class="btn btn-primary" href="${escapeHtml(g2bDetailUrl(bid.bidNo))}" target="_blank" rel="noopener">나라장터 원문 ↗</a></div>
          <dl class="info-grid">
            ${[
              ["발주기관", bid.agency], ["수요기관", bid.demandAgency], ["예산", money(bid.amount)],
              ["공고일", dateTime(bid.postedAt)], ["입찰마감", dateTime(bid.deadlineAt)], ["개찰일", dateTime(bid.openingAt)],
              ["계약방법", bid.contractMethod], ["입찰방식", bid.bidMethod], ["지역", bid.region]
            ].map(([k,v]) => `<div class="info"><dt>${k}</dt><dd>${escapeHtml(v)}</dd></div>`).join("")}
          </dl>
        </section>
        <section class="panel"><h2>AI 요약</h2><p class="summary">${escapeHtml(bid.summary)}</p>
          <div class="evidence">분석 결과는 참고용입니다. 최종 판단은 공고 원문과 첨부파일을 기준으로 하세요.</div>
        </section>
        <section class="panel"><h2>조건 추출 결과</h2>
          <h3>참가 자격</h3><ul>${bid.requirements.map(x => `<li>${escapeHtml(x)}</li>`).join("") || "<li>추출된 조건 없음</li>"}</ul>
          <h3>필요 인증</h3><p>${bid.certifications.map(x => `<span class="keyword-chip">${escapeHtml(x)}</span>`).join("") || "없음"}</p>
          <h3>제출 서류</h3><p>${bid.documents.map(x => `<span class="keyword-chip">${escapeHtml(x)}</span>`).join("") || "없음"}</p>
          <h3>위험 요소</h3><ul class="risk-list">${bid.risks.map(x => `<li>⚠ ${escapeHtml(x)}</li>`).join("") || "<li>특이 위험요소 없음</li>"}</ul>
        </section>
        <section class="panel"><h2>담당자 체크리스트</h2>
          <div class="checklist">${CHECKLIST.map((item,i) => `<label class="check-item">
            <input type="checkbox" data-action="check" data-id="${id}" data-index="${i}" ${checks.includes(i)?"checked":""}>
            <span>${item}</span></label>`).join("")}</div>
        </section>
      </div>
      <aside>
        <section class="panel">
          <h2>적합도</h2>
          <div class="score-ring" style="--score:${bid.score}"><strong>${bid.score}</strong></div>
          <p style="text-align:center"><span class="badge ${scoreColor}">${scoreLabel}</span></p>
          <div class="score-breakdown">${SCORE_ITEMS.map(([name,max],i) => {
            const value = bid.breakdown[i] || 0;
            return `<div class="score-row"><span>${name}</span><span class="bar"><span style="width:${value/max*100}%"></span></span><b>${value}</b></div>`;
          }).join("")}</div>
        </section>
        <section class="panel"><h2>업무 처리</h2>
          <label>상태</label>
          <select class="select" id="detail-status" data-id="${id}">
            ${STATUS.map(x => `<option ${bid.status===x?"selected":""}>${x}</option>`).join("")}
          </select>
          <br><br><label>담당자 메모</label>
          <textarea class="textarea" id="memo" data-id="${id}" placeholder="검토 내용과 확인할 사항을 입력하세요.">${escapeHtml(state.notes[id] || "")}</textarea>
          <button class="btn btn-primary" style="width:100%;margin-top:10px" data-action="save-detail" data-id="${id}">저장</button>
          <button class="btn btn-secondary" style="width:100%;margin-top:8px" data-action="save" data-id="${id}">${state.saved.includes(id)?"★ 관심 공고 해제":"☆ 관심 공고 저장"}</button>
        </section>
      </aside>
    </div>
  `);
}

function savedPage() {
  const bids = state.bids.filter(b => state.saved.includes(b.id));
  return layout(`${header("관심 공고", "저장한 공고와 검토 상태를 관리합니다.")}<section class="panel">${bidTable(bids)}</section>`);
}

function workflowPage() {
  const groups = ["신규", "검토중", "조건확인필요", "참여가능", "대표승인필요", "제안/견적준비"];
  return layout(`
    ${header("업무 보드", "공고 검토부터 투찰 준비까지의 진행 상태입니다.")}
    <div class="settings-grid">${groups.map(status => {
      const bids = state.bids.filter(b => b.status === status);
      return `<section class="panel"><div class="panel-title"><h2>${status}</h2><span class="badge ${statusBadge(status)}">${bids.length}건</span></div>
        ${bids.length ? bids.map(b => `<div style="border-top:1px solid var(--line);padding:12px 0">
          <button class="title-link" data-route="/bids/${b.id}">${escapeHtml(b.title)}</button>
          <div style="margin-top:7px"><span class="score">${b.score}점</span> · ${date(b.deadlineAt)}</div></div>`).join("") : `<div class="empty">공고 없음</div>`}
      </section>`;
    }).join("")}</div>
  `);
}

function settingsPage() {
  return layout(`
    ${header("설정", "검색어와 회사 평가 기준을 관리합니다.")}
    <div class="settings-grid">
      <section class="panel"><div class="panel-title"><h2>검색어 그룹</h2><button class="btn btn-primary" data-action="add-keyword">그룹 추가</button></div>
        ${state.keywordGroups.map((g,i) => `<div style="border-top:1px solid var(--line);padding:14px 0">
          <strong>${escapeHtml(g.name)}</strong><div>${g.keywords.map(k => `<span class="keyword-chip">${escapeHtml(k)}</span>`).join("")}</div>
          <button class="btn btn-danger" data-action="delete-keyword" data-index="${i}" style="margin-top:8px">삭제</button>
        </div>`).join("")}
      </section>
      <section class="panel"><h2>회사 평가 기준</h2>
        <p>보유 인증</p><div><span class="keyword-chip">중소기업확인서</span><span class="keyword-chip">직접생산확인증명서</span><span class="keyword-chip">정보통신공사업</span></div>
        <p>취급 품목</p><div><span class="keyword-chip">PC·노트북</span><span class="keyword-chip">서버</span><span class="keyword-chip">네트워크</span><span class="keyword-chip">전자칠판</span></div>
        <p>가능 지역</p><div><span class="keyword-chip">전국</span><span class="keyword-chip">서울·수도권</span></div>
        <p class="footer-note">실제 운영에서는 이 항목을 Supabase의 company_profiles와 관련 테이블에서 관리합니다.</p>
      </section>
      <section class="panel"><h2>적합도 배점</h2>
        ${SCORE_ITEMS.map(([name,max]) => `<div class="score-row" style="grid-template-columns:1fr 90px"><span>${name}</span><b>${max}점</b></div>`).join("")}
      </section>
      <section class="panel"><h2>자동수집</h2>
        <dl class="info-grid" style="grid-template-columns:1fr 1fr"><div class="info"><dt>실행 시각</dt><dd>매일 08:00 KST</dd></div>
        <div class="info"><dt>실행 방식</dt><dd>GitHub Actions</dd></div><div class="info"><dt>데이터 원천</dt><dd>나라장터 API</dd></div>
        <div class="info"><dt>현재 연결</dt><dd>${CONFIG.supabaseUrl?"운영":"데모"}</dd></div></dl>
      </section>
    </div>
  `);
}

function render() {
  state.route = location.hash.slice(1) || "/dashboard";
  let page;
  if (state.route === "/dashboard") page = dashboard();
  else if (state.route === "/bids") page = bidsPage();
  else if (state.route.startsWith("/bids/")) page = detailPage(state.route.split("/")[2]);
  else if (state.route === "/saved") page = savedPage();
  else if (state.route === "/workflow") page = workflowPage();
  else if (state.route === "/settings") page = settingsPage();
  else page = dashboard();
  document.querySelector("#app").innerHTML = page;
}

document.addEventListener("click", event => {
  const route = event.target.closest("[data-route]")?.dataset.route;
  if (route) { location.hash = route; return; }
  const target = event.target.closest("[data-action]");
  if (!target) return;
  const { action, id, index } = target.dataset;
  if (action === "menu") document.querySelector("#sidebar")?.classList.toggle("open");
  if (action === "save") {
    state.saved = state.saved.includes(id) ? state.saved.filter(x => x !== id) : [...state.saved, id];
    persist(); render();
  }
  if (action === "search") {
    state.search = document.querySelector("#search").value;
    state.category = document.querySelector("#category").value;
    state.status = document.querySelector("#filter-status").value;
    state.score = document.querySelector("#score").value;
    state.due = document.querySelector("#due").value;
    render();
  }
  if (action === "save-detail") {
    const bid = state.bids.find(x => x.id === id);
    bid.status = document.querySelector("#detail-status").value;
    state.notes[id] = document.querySelector("#memo").value;
    persist(); render();
  }
  if (action === "check") {
    const i = Number(index);
    const current = state.checks[id] || [];
    state.checks[id] = target.checked ? [...new Set([...current, i])] : current.filter(x => x !== i);
    persist();
  }
  if (action === "add-keyword") {
    const name = prompt("새 검색어 그룹 이름을 입력하세요.");
    if (!name) return;
    const keywords = prompt("검색어를 쉼표로 구분해 입력하세요.")?.split(",").map(x => x.trim()).filter(Boolean) || [];
    state.keywordGroups.push({ name, keywords }); persist(); render();
  }
  if (action === "delete-keyword" && confirm("이 검색어 그룹을 삭제할까요?")) {
    state.keywordGroups.splice(Number(index), 1); persist(); render();
  }
});

window.addEventListener("hashchange", render);

await loadBids();
render();
