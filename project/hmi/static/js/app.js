// 文件作用：Edge-Sort 上位机前端交互逻辑。
//
// 主要内容：
//   1. 每 2 秒轮询 /api/stats，更新统计卡片与最近记录表。
//   2. 每 200 毫秒轮询 /api/state，更新连接状态徽标，并把关节角度交给 3D 视图。
//   3. 请求失败时显示离线状态，不抛出未处理异常。

const els = {
  badge: document.getElementById("status-badge"),
  total: document.getElementById("stat-total"),
  rate: document.getElementById("stat-rate"),
  avg: document.getElementById("stat-avg"),
  last: document.getElementById("stat-last"),
  records: document.getElementById("records-body"),
};

function fmtDuration(value) {
  return value === null || value === undefined ? "--" : Number(value).toFixed(1);
}

function fmtPercent(value) {
  return value === null || value === undefined ? "--" : (value * 100).toFixed(1) + "%";
}

function fmtTime(ts) {
  if (!ts) return "--";
  const d = new Date(ts);
  return Number.isNaN(d.getTime()) ? ts : d.toLocaleString("zh-CN");
}

async function fetchStats() {
  const resp = await fetch("/api/stats");
  if (!resp.ok) throw new Error("stats failed");
  const s = await resp.json();
  els.total.textContent = s.total_attempts ?? 0;
  els.rate.textContent = fmtPercent(s.success_rate);
  els.avg.textContent = fmtDuration(s.avg_duration_s);
  const last = (s.recent && s.recent[0]) || null;
  els.last.textContent = last ? fmtDuration(last.duration_s) : "--";
  renderRecords(s.recent || []);
}

function renderRecords(records) {
  if (!records.length) {
    els.records.innerHTML = '<tr><td colspan="5" class="text-muted">暂无数据</td></tr>';
    return;
  }
  els.records.innerHTML = records
    .map(
      (r) => `
      <tr>
        <td>${fmtTime(r.ts)}</td>
        <td>${r.object || "--"}</td>
        <td>${r.success ? "成功" : "失败"}</td>
        <td>${fmtDuration(r.duration_s)}</td>
        <td>${r.retries ?? 0}</td>
      </tr>`,
    )
    .join("");
}

async function fetchState() {
  const resp = await fetch("/api/state");
  if (!resp.ok) throw new Error("state failed");
  const s = await resp.json();
  els.badge.textContent = s.connected ? "在线" : "离线";
  els.badge.className = "badge " + (s.connected ? "badge-online" : "badge-offline");
  // 3D 视图由 viewer3d.js 注册；未加载完成时忽略
  if (typeof window.updateArmJoints === "function" && s.joints) {
    window.updateArmJoints(s.joints, s.gripper ?? 0);
  }
}

async function tickStats() {
  try {
    await fetchStats();
  } catch {
    els.badge.textContent = "离线";
    els.badge.className = "badge badge-offline";
  }
}

async function tickState() {
  try {
    await fetchState();
  } catch {
    els.badge.textContent = "离线";
    els.badge.className = "badge badge-offline";
  }
}

setInterval(tickStats, 2000);
setInterval(tickState, 200);
tickStats();
tickState();
