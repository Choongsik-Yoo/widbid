const CONFIG = window.WITHBID_CONFIG || {};
const ADMIN_EMAIL = "csyoo22@gmail.com";
const AUTH_STORAGE_KEY = "withbid-auth-session";

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

const state = {
  route: location.hash.slice(1) || "/dashboard",
  bids: [],
  search: "",
  category: "전체",
  status: "전체",
  score: "전체",
  due: "전체",
  quickFilter: "",
  saved: [],
  notes: {},
  checks: {},
  assignments: {},
  user: null,
  session: null,
  allowedUsers: [],
  authReady: false,
  authError: "",
  connectionStatus: "loading",
  connectionError: "",
  keywordGroups: JSON.parse(localStorage.getItem("withbid-keywords") || "null") || [
    { name: "PC·컴퓨터", keywords: ["컴퓨터", "PC", "데스크톱", "노트북", "랩탑", "모니터"] },
    { name: "서버·고성능장비", keywords: ["서버", "SERVER", "GPU 서버", "워크스테이션", "딥러닝"] },
    { name: "전산장비", keywords: ["전산장비", "전산기기", "전산설비", "시스템 장비"] },
    { name: "네트워크·스토리지", keywords: ["네트워크", "스토리지", "NAS", "SAN", "방화벽", "스위치"] },
    { name: "교육·강의장비", keywords: ["전자칠판", "인터랙티브 화이트보드", "LED 전광판"] },
    { name: "기타", keywords: ["소프트웨어", "렌탈", "리스"] }
  ]
};

const pcGroup = state.keywordGroups.find(group => group.name === "PC·컴퓨터");
if (pcGroup && !pcGroup.keywords.includes("모니터")) pcGroup.keywords.push("모니터");
if (!state.keywordGroups.some(group => group.name === "기타")) {
  state.keywordGroups.push({ name: "기타", keywords: ["소프트웨어", "렌탈", "리스"] });
}
localStorage.setItem("withbid-keywords", JSON.stringify(state.keywordGroups));

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
  localStorage.setItem("withbid-keywords", JSON.stringify(state.keywordGroups));
}

function authHeaders(extra = {}) {
  return {
    apikey: CONFIG.supabaseAnonKey,
    Authorization: `Bearer ${state.session?.access_token || CONFIG.supabaseAnonKey}`,
    "Content-Type": "application/json",
    ...extra
  };
}

async function api(path, options = {}) {
  const response = await fetch(`${CONFIG.supabaseUrl}${path}`, {
    ...options,
    headers: authHeaders(options.headers || {})
  });
  if (!response.ok) throw new Error((await response.text()) || `Supabase ${response.status}`);
  if (response.status === 204) return null;
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}

function saveSession(session) {
  state.session = session;
  if (session) localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
  else localStorage.removeItem(AUTH_STORAGE_KEY);
}

function parseAuthCallback() {
  const params = new URLSearchParams(location.hash.slice(1));
  if (!params.get("access_token")) return false;
  saveSession({
    access_token: params.get("access_token"),
    refresh_token: params.get("refresh_token"),
    expires_at: Math.floor(Date.now() / 1000) + Number(params.get("expires_in") || 3600)
  });
  history.replaceState(null, "", `${location.pathname}${location.search}#/dashboard`);
  return true;
}

async function refreshSession() {
  if (!state.session?.refresh_token) return false;
  const response = await fetch(`${CONFIG.supabaseUrl}/auth/v1/token?grant_type=refresh_token`, {
    method: "POST",
    headers: { apikey: CONFIG.supabaseAnonKey, "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: state.session.refresh_token })
  });
  if (!response.ok) return false;
  const session = await response.json();
  saveSession({ ...session, expires_at: Math.floor(Date.now() / 1000) + session.expires_in });
  return true;
}

async function initAuth() {
  if (!CONFIG.supabaseUrl || !CONFIG.supabaseAnonKey) {
    state.authError = "Supabase 배포 설정이 없습니다.";
    state.authReady = true;
    return;
  }
  parseAuthCallback();
  if (!state.session) {
    try { saveSession(JSON.parse(localStorage.getItem(AUTH_STORAGE_KEY) || "null")); } catch { saveSession(null); }
  }
  if (state.session?.expires_at <= Math.floor(Date.now() / 1000) + 60 && !(await refreshSession())) saveSession(null);
  if (!state.session) { state.authReady = true; return; }
  try {
    state.user = await api("/auth/v1/user");
    const email = state.user.email.toLowerCase();
    const allowed = await api(`/rest/v1/allowed_users?email=eq.${encodeURIComponent(email)}&is_active=eq.true&select=*`);
    if (!allowed.length) throw new Error("관리자가 허용하지 않은 계정입니다.");
    state.user.profile = allowed[0];
  } catch (error) {
    state.authError = error.message;
    state.user = null;
    saveSession(null);
  }
  state.authReady = true;
}

function loginPage() {
  return `<main class="auth-screen"><section class="panel auth-card">
    <div class="brand">WithBid <span>AI</span></div>
    <h1>회사 계정 로그인</h1>
    <p>관리자가 등록한 Google 계정으로 로그인하세요.<br>관심 공고와 업무 진행 상황은 직원들과 공동으로 저장됩니다.</p>
    ${state.authError ? `<p class="error-text">${escapeHtml(state.authError)}</p>` : ""}
    <button class="btn btn-primary" data-action="login-google">Google 계정으로 로그인</button>
  </section></main>`;
}

function loginWithGoogle() {
  const redirectTo = `${location.origin}${location.pathname}`;
  location.href = `${CONFIG.supabaseUrl}/auth/v1/authorize?provider=google&redirect_to=${encodeURIComponent(redirectTo)}`;
}

async function logout() {
  if (state.session) await api("/auth/v1/logout", { method: "POST" }).catch(() => {});
  saveSession(null);
  state.user = null;
  state.saved = [];
  state.notes = {};
  state.checks = {};
  render();
}

async function loadBids() {
  if (!CONFIG.supabaseUrl || !CONFIG.supabaseAnonKey) {
    state.bids = [];
    state.connectionStatus = "config_missing";
    state.connectionError = "Supabase 배포 설정이 없습니다.";
    return;
  }
  try {
    const response = await fetch(
      `${CONFIG.supabaseUrl}/rest/v1/bids?select=*,bid_analyses(*)&order=posted_at.desc`,
      { headers: authHeaders() }
    );
    if (!response.ok) throw new Error(`Supabase ${response.status}`);
    const rows = await response.json();
    state.bids = rows.map(mapSupabaseBid);
    state.connectionStatus = "connected";
    state.connectionError = "";
  } catch (error) {
    console.error("Supabase 연결 실패", error);
    state.bids = [];
    state.connectionStatus = "error";
    state.connectionError = `실제 데이터 연결 실패: ${error.message}`;
  }
}

async function loadTeamData() {
  if (!state.user) return;
  const [bidStates, checklistRows, users] = await Promise.all([
    api("/rest/v1/team_bid_states?select=*"),
    api("/rest/v1/team_bid_checklists?is_checked=eq.true&select=*"),
    api("/rest/v1/allowed_users?is_active=eq.true&select=email,display_name,role,is_active&order=display_name.asc")
  ]);
  state.saved = bidStates.filter(row => row.is_saved).map(row => row.bid_id);
  state.notes = Object.fromEntries(bidStates.map(row => [row.bid_id, row.memo || ""]));
  state.assignments = Object.fromEntries(bidStates.map(row => [row.bid_id, row.assigned_email || ""]));
  state.checks = {};
  checklistRows.forEach(row => {
    (state.checks[row.bid_id] ||= []).push(Number(row.item_key));
  });
  bidStates.forEach(row => {
    const bid = state.bids.find(item => item.id === row.bid_id);
    if (bid) bid.status = row.status;
  });
  state.allowedUsers = users;
}

async function migrateLegacyLocalData() {
  const legacyKeys = ["withbid-saved", "withbid-notes", "withbid-checks"];
  if (!legacyKeys.some(key => localStorage.getItem(key))) return;
  let legacySaved = [], legacyNotes = {}, legacyChecks = {};
  try {
    legacySaved = JSON.parse(localStorage.getItem("withbid-saved") || "[]");
    legacyNotes = JSON.parse(localStorage.getItem("withbid-notes") || "{}");
    legacyChecks = JSON.parse(localStorage.getItem("withbid-checks") || "{}");
  } catch (error) {
    console.warn("기존 브라우저 업무 데이터 변환 실패", error);
  }
  const bidIds = new Set([...legacySaved, ...Object.keys(legacyNotes), ...Object.keys(legacyChecks)]);
  for (const bidId of bidIds) {
    if (!state.bids.some(bid => bid.id === bidId)) continue;
    if (legacySaved.includes(bidId)) state.saved = [...new Set([...state.saved, bidId])];
    if (!state.notes[bidId] && legacyNotes[bidId]) state.notes[bidId] = legacyNotes[bidId];
    await saveTeamBidState(bidId, { is_saved: state.saved.includes(bidId), memo: state.notes[bidId] || "" });
    for (const itemIndex of legacyChecks[bidId] || []) {
      await api("/rest/v1/team_bid_checklists?on_conflict=bid_id,item_key", {
        method: "POST",
        headers: { Prefer: "resolution=merge-duplicates,return=minimal" },
        body: JSON.stringify({ bid_id: bidId, item_key: String(itemIndex), item_label: CHECKLIST[itemIndex], is_checked: true, updated_by: state.user.email.toLowerCase(), updated_at: new Date().toISOString() })
      });
    }
  }
  legacyKeys.forEach(key => localStorage.removeItem(key));
  if (bidIds.size) await loadTeamData();
}

async function saveTeamBidState(bidId, changes) {
  const bid = state.bids.find(item => item.id === bidId);
  const payload = {
    bid_id: bidId,
    is_saved: state.saved.includes(bidId),
    status: bid?.status || "신규",
    memo: state.notes[bidId] || "",
    assigned_email: state.assignments[bidId] || null,
    updated_by: state.user.email.toLowerCase(),
    updated_at: new Date().toISOString(),
    ...changes
  };
  await api("/rest/v1/team_bid_states?on_conflict=bid_id", {
    method: "POST",
    headers: { Prefer: "resolution=merge-duplicates,return=minimal" },
    body: JSON.stringify(payload)
  });
  await logActivity(bidId, "bid_state_updated", changes);
}

async function logActivity(bidId, action, details = {}) {
  await api("/rest/v1/team_activity_log", {
    method: "POST",
    headers: { Prefer: "return=minimal" },
    body: JSON.stringify({ bid_id: bidId, actor_email: state.user.email.toLowerCase(), action, details })
  });
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
        <div class="user-menu"><span>${escapeHtml(state.user?.user_metadata?.full_name || state.user?.email || "")}</span><button class="btn btn-secondary" data-action="logout">로그아웃</button></div>
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
    ${state.connectionStatus === "config_missing" ? `<div class="notice">운영 DB 설정이 배포되지 않았습니다. 관리자에게 문의하세요.</div>` : ""}
    ${state.connectionStatus === "error" ? `<div class="notice">${escapeHtml(state.connectionError)}</div>` : ""}
    ${state.connectionStatus === "connected" && !state.bids.length ? `<div class="notice">운영 DB 연결은 정상입니다. 첫 나라장터 수집 작업이 완료되면 실제 공고가 표시됩니다.</div>` : ""}
    <section class="cards">
      <button class="metric metric-button" data-dashboard-filter="all"><div class="metric-label">전체 공고</div><div class="metric-value">${state.bids.length}</div><div class="metric-note">수집된 공고</div></button>
      <button class="metric metric-button" data-dashboard-filter="due7"><div class="metric-label">마감 7일 이내</div><div class="metric-value">${due7}</div><div class="metric-note">우선 확인 필요</div></button>
      <button class="metric metric-button" data-dashboard-filter="fit"><div class="metric-label">참여 가능성 높음</div><div class="metric-value">${fit}</div><div class="metric-note">70점 이상</div></button>
      <button class="metric metric-button" data-dashboard-filter="review"><div class="metric-label">조건 확인 필요</div><div class="metric-value">${review}</div><div class="metric-note">위험요소 포함</div></button>
      <button class="metric metric-button" data-dashboard-filter="saved"><div class="metric-label">관심 공고</div><div class="metric-value">${state.saved.length}</div><div class="metric-note">담당자 저장</div></button>
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
    const quickMatch = state.quickFilter !== "review"
      || b.risks.length > 0
      || b.status === "조건확인필요";
    return (!q || haystack.includes(q))
      && (state.category === "전체" || b.category === state.category)
      && (state.status === "전체" || b.status === state.status)
      && (state.score === "전체" || (state.score === "70+" ? b.score >= 70 : b.score < 70))
      && (state.due === "전체" || (state.due === "7" ? due >= 0 && due <= 7 : due >= 0 && due <= 3))
      && quickMatch;
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
          <br><br><label>담당자</label>
          <select class="select" id="assignee" data-id="${id}">
            <option value="">미지정</option>
            ${state.allowedUsers.map(user => `<option value="${escapeHtml(user.email)}" ${state.assignments[id] === user.email ? "selected" : ""}>${escapeHtml(user.display_name || user.email)}</option>`).join("")}
          </select>
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
  const newBids = state.bids.filter(bid => bid.status === "신규");
  const processingStatuses = ["검토중", "조건확인필요", "참여가능", "대표승인필요", "제안/견적준비"];
  const workflowPanel = (status, bids, extraClass = "") => `
    <section class="panel workflow-panel ${extraClass}">
      <div class="panel-title"><h2>${status}</h2><span class="badge ${statusBadge(status)}">${bids.length}건</span></div>
      <div class="workflow-items">
        ${bids.length ? bids.map(bid => `<article class="workflow-item">
          <button class="title-link" data-route="/bids/${bid.id}">${escapeHtml(bid.title)}</button>
          <div class="workflow-item-meta"><span class="score">${bid.score}점</span><span>${date(bid.deadlineAt)}</span></div>
        </article>`).join("") : `<div class="empty">공고 없음</div>`}
      </div>
    </section>`;
  return layout(`
    ${header("업무 보드", "공고 검토부터 투찰 준비까지의 진행 상태입니다.")}
    <div class="workflow-layout">
      ${workflowPanel("신규", newBids, "workflow-new")}
      <div class="workflow-processing" aria-label="업무 처리 단계">
        ${processingStatuses.map(status => workflowPanel(status, state.bids.filter(bid => bid.status === status))).join("")}
      </div>
    </div>
  `);
}

function settingsPage() {
  const isAdmin = state.user?.profile?.role === "admin" || state.user?.email?.toLowerCase() === ADMIN_EMAIL;
  return layout(`
    ${header("설정", "검색어와 회사 평가 기준을 관리합니다.")}
    <div class="settings-grid">
      <section class="panel"><div class="panel-title"><h2>검색어 그룹</h2></div>
        ${state.keywordGroups.map((g,i) => `<div style="border-top:1px solid var(--line);padding:14px 0">
          <strong>${escapeHtml(g.name)}</strong><div>${g.keywords.map(k => `<span class="keyword-chip">${escapeHtml(k)}</span>`).join("")}</div>
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
        <div class="info"><dt>현재 연결</dt><dd>${state.connectionStatus === "connected" ? "운영 DB" : "확인 필요"}</dd></div></dl>
      </section>
      ${isAdmin ? `<section class="panel"><div class="panel-title"><h2>사용 허용 계정</h2></div>
        <div class="filters" style="grid-template-columns:2fr 1fr auto">
          <input class="field" id="allowed-email" type="email" placeholder="직원 Google 이메일">
          <input class="field" id="allowed-name" placeholder="직원 이름">
          <button class="btn btn-primary" data-action="add-user">등록</button>
        </div>
        <table class="user-table"><tbody>${state.allowedUsers.map(user => `<tr><td>${escapeHtml(user.display_name || "-")}</td><td>${escapeHtml(user.email)}</td><td>${escapeHtml(user.role)}</td><td>${user.email === ADMIN_EMAIL ? "관리자" : `<button class="btn btn-danger" data-action="disable-user" data-email="${escapeHtml(user.email)}">비활성화</button>`}</td></tr>`).join("")}</tbody></table>
      </section>` : ""}
    </div>
  `);
}

function render() {
  if (!state.authReady) {
    document.querySelector("#app").innerHTML = `<main class="auth-screen"><section class="panel auth-card"><p>로그인 정보를 확인하고 있습니다.</p></section></main>`;
    return;
  }
  if (!state.user) {
    document.querySelector("#app").innerHTML = loginPage();
    return;
  }
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

document.addEventListener("click", async event => {
  const dashboardFilter = event.target.closest("[data-dashboard-filter]")?.dataset.dashboardFilter;
  if (dashboardFilter) {
    state.search = "";
    state.category = "전체";
    state.status = "전체";
    state.score = dashboardFilter === "fit" ? "70+" : "전체";
    state.due = dashboardFilter === "due7" ? "7" : "전체";
    state.quickFilter = dashboardFilter === "review" ? "review" : "";
    location.hash = dashboardFilter === "saved" ? "/saved" : "/bids";
    return;
  }
  const route = event.target.closest("[data-route]")?.dataset.route;
  if (route) { location.hash = route; return; }
  const target = event.target.closest("[data-action]");
  if (!target) return;
  const { action, id, index } = target.dataset;
  if (action === "login-google") { loginWithGoogle(); return; }
  if (action === "logout") { await logout(); return; }
  if (action === "menu") document.querySelector("#sidebar")?.classList.toggle("open");
  if (action === "save") {
    state.saved = state.saved.includes(id) ? state.saved.filter(x => x !== id) : [...state.saved, id];
    await saveTeamBidState(id, { is_saved: state.saved.includes(id) }); render();
  }
  if (action === "search") {
    state.search = document.querySelector("#search").value;
    state.category = document.querySelector("#category").value;
    state.status = document.querySelector("#filter-status").value;
    state.score = document.querySelector("#score").value;
    state.due = document.querySelector("#due").value;
    state.quickFilter = "";
    render();
  }
  if (action === "save-detail") {
    const bid = state.bids.find(x => x.id === id);
    bid.status = document.querySelector("#detail-status").value;
    state.notes[id] = document.querySelector("#memo").value;
    state.assignments[id] = document.querySelector("#assignee").value;
    await saveTeamBidState(id, { status: bid.status, memo: state.notes[id], assigned_email: state.assignments[id] || null }); render();
  }
  if (action === "check") {
    const i = Number(index);
    const current = state.checks[id] || [];
    state.checks[id] = target.checked ? [...new Set([...current, i])] : current.filter(x => x !== i);
    await api("/rest/v1/team_bid_checklists?on_conflict=bid_id,item_key", {
      method: "POST",
      headers: { Prefer: "resolution=merge-duplicates,return=minimal" },
      body: JSON.stringify({ bid_id: id, item_key: String(i), item_label: CHECKLIST[i], is_checked: target.checked, updated_by: state.user.email.toLowerCase(), updated_at: new Date().toISOString() })
    });
    await logActivity(id, "checklist_updated", { item: CHECKLIST[i], checked: target.checked });
  }
  if (action === "add-user") {
    const email = document.querySelector("#allowed-email").value.trim().toLowerCase();
    const displayName = document.querySelector("#allowed-name").value.trim();
    if (!email) return;
    await api("/rest/v1/allowed_users?on_conflict=email", {
      method: "POST",
      headers: { Prefer: "resolution=merge-duplicates,return=minimal" },
      body: JSON.stringify({ email, display_name: displayName || null, role: "member", is_active: true, updated_at: new Date().toISOString() })
    });
    await loadTeamData(); render();
  }
  if (action === "disable-user") {
    await api(`/rest/v1/allowed_users?email=eq.${encodeURIComponent(target.dataset.email)}`, {
      method: "PATCH", headers: { Prefer: "return=minimal" }, body: JSON.stringify({ is_active: false, updated_at: new Date().toISOString() })
    });
    await loadTeamData(); render();
  }
});

window.addEventListener("hashchange", render);

await initAuth();
if (state.user) {
  await loadBids();
  try {
    await loadTeamData();
    await migrateLegacyLocalData();
  } catch (error) {
    state.connectionStatus = "error";
    state.connectionError = `공동 업무 데이터 연결 실패: ${error.message}`;
  }
}
render();
