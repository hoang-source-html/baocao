/* Đọc file "Báo cáo Bộ phận Xếp Giấy.xlsx" (Nhap_TG · Nhap_SP · Nhap_BTP) thành dữ liệu báo cáo.
   Logic giống hệt update_dashboard.py. Cần thư viện SheetJS (biến XLSX). */
(function (root) {
  const HPL_TARGET = 0.25, CERARL_TARGET = 0.30, DEFECT_TARGET = 0.0005;
  const pad = n => String(n).padStart(2, '0');
  const has = v => v !== null && v !== undefined && v !== '';
  const str = v => (v === null || v === undefined ? '' : String(v)).trim();
  const num = v => { const n = parseFloat(v); return isNaN(n) ? 0 : n; };

  function toDt(v, XLSX) {            // -> {y,m,d} hoặc null
    if (v instanceof Date && !isNaN(v)) return { y: v.getUTCFullYear(), m: v.getUTCMonth() + 1, d: v.getUTCDate() };
    if (typeof v === 'number') { const p = XLSX.SSF.parse_date_code(v); return p ? { y: p.y, m: p.m, d: p.d } : null; }
    if (typeof v === 'string') {
      const s = v.trim().slice(0, 10); let m;
      if ((m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/))) return { y: +m[1], m: +m[2], d: +m[3] };
      if ((m = s.match(/^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})$/))) return { y: +m[3], m: +m[2], d: +m[1] };
    }
    return null;
  }
  const fmtDate = t => `${t.y}-${pad(t.m)}-${pad(t.d)}`;
  const monthOf = t => `${pad(t.m)}/${t.y}`;
  const weekFallback = day => `Tuần ${Math.floor((day - 1) / 7) + 1}`;

  function simplifyOp(s) {
    if (!has(s)) return '';
    const main = String(s).split('(')[0].trim();
    return main.replace(/–/g, '-').split('-')
      .map(p => { p = p.trim(); return p ? p.charAt(0).toUpperCase() + p.slice(1).toLowerCase() : ''; })
      .filter(Boolean).join(' - ');
  }
  function normType(t) {
    t = str(t).toUpperCase();
    if (!t || t === 'BTP') return '';
    if (t.includes('CERARL') || t.includes('CERAR')) return 'CERARL';
    return 'HPL';
  }
  function rowsOf(wb, name, XLSX, startRow) {
    const ws = wb.Sheets[name];
    if (!ws) throw new Error(`Không tìm thấy sheet "${name}" trong file Excel.`);
    // luôn đọc từ ô A1 để số dòng trùng với Excel, kể cả khi vùng dữ liệu bắt đầu thấp hơn
    const e = XLSX.utils.decode_range(ws['!ref'] || 'A1').e;
    const all = XLSX.utils.sheet_to_json(ws, { header: 1, raw: true, defval: null, blankrows: true, range: XLSX.utils.encode_range({ s: { r: 0, c: 0 }, e }) });
    return all.slice(startRow - 1);   // startRow tính từ 1 như Excel
  }

  function buildReport(wb, XLSX, now) {
    now = now || new Date();
    // ---- Nhap_TG: tiêu đề dòng 2, dữ liệu từ dòng 3
    const tg = [], lotInfo = {};
    for (const row of rowsOf(wb, 'Nhap_TG', XLSX, 3)) {
      const dt = toDt(row[0], XLSX);
      if (!dt || !has(row[4])) continue;
      const week = has(row[19]) && row[19] !== 0 ? str(row[19]) : weekFallback(dt.d);
      const line = str(row[2]);
      const typ = normType(row[17]) || normType(row[3]);
      const lot = str(row[4]);
      const minutes = Math.round(num(row[14]) * 10) / 10;
      const rec = { date: fmtDate(dt), day: dt.d, week, month: monthOf(dt), line, type: typ, lot, minutes, op: simplifyOp(row[13]) };
      tg.push(rec);
      if (!(lot in lotInfo)) lotInfo[lot] = { date: rec.date, day: rec.day, week, month: rec.month, line, type: typ };
    }
    // ---- Nhap_SP: tiêu đề dòng 3, dữ liệu từ dòng 4
    const pd = [];
    for (const row of rowsOf(wb, 'Nhap_SP', XLSX, 4)) {
      if (!has(row[1])) continue;
      const lot = str(row[1]);
      const qty = num(row[4]);
      const sizeCat = str(row[6]);
      let typ = normType(row[11]);
      const code = str(row[3]);
      let line = str(row[10]);
      const dt = toDt(row[0], XLSX), info = lotInfo[lot];
      let day, month, week, date;
      if (dt) { day = dt.d; month = monthOf(dt); week = has(row[13]) && row[13] !== 0 ? str(row[13]) : weekFallback(day); date = fmtDate(dt); }
      else if (info) { ({ day, month, week, date } = info); if (!line) line = info.line; if (!typ) typ = info.type; }
      else continue;
      if (!line && info) line = info.line;
      if (!typ && info) typ = info.type;
      pd.push({ date, day, week, month, line, type: typ || 'HPL', sizeCat, lot, qty, code });
    }
    // ---- Nhap_BTP: tiêu đề dòng 2, dữ liệu từ dòng 3
    const btp = [];
    for (const row of rowsOf(wb, 'Nhap_BTP', XLSX, 3)) {
      if (!has(row[1])) continue;
      const lot = str(row[1]);
      const qty = num(row[4]);
      const cause = str(row[5]), code = str(row[3]);
      let line = str(row[6]), typ = '';
      if (has(row[12])) { const parts = String(row[12]).split('-'); if (parts.length >= 2) typ = normType(parts[parts.length - 1]); }
      const info = lotInfo[lot];
      if (!typ && info) typ = info.type;
      if (!line && info) line = info.line;
      const dt = toDt(row[0], XLSX);
      let day, month, week, date;
      if (dt) { day = dt.d; month = monthOf(dt); week = has(row[9]) && row[9] !== 0 ? str(row[9]) : weekFallback(day); date = fmtDate(dt); }
      else if (info) { ({ day, month, week, date } = info); }
      else continue;
      btp.push({ date, day, week, month, line, type: typ || 'HPL', lot, qty, cause, code });
    }
    return finish(tg, pd, btp, now);
  }

  function finish(tg, pd, btp, now) {
    const uniq = a => [...new Set(a)];
    const days = uniq(tg.map(r => r.day)).sort((a, b) => a - b);
    const months = uniq(tg.map(r => r.month)).sort((a, b) => { const [m1, y1] = a.split('/').map(Number), [m2, y2] = b.split('/').map(Number); return y1 - y2 || m1 - m2; });
    const wnum = w => { const m = String(w).match(/\d+/); return m ? +m[0] : 0; };
    const weeks = uniq(tg.map(r => r.week)).sort((a, b) => wnum(a) - wnum(b));
    const lines = uniq(tg.map(r => r.line).filter(Boolean)).sort();
    const types = uniq(tg.map(r => r.type).filter(Boolean)).sort();
    let dateRange = '';
    if (tg.length) {
      const ds = tg.map(r => r.date).sort(), lo = ds[0], hi = ds[ds.length - 1];
      dateRange = `${lo.slice(8, 10)}/${lo.slice(5, 7)} – ${hi.slice(8, 10)}/${hi.slice(5, 7)}/${hi.slice(0, 4)}`;
    }
    const meta = {
      days, weeks, months, lines, types,
      hplTarget: HPL_TARGET, cerarlTarget: CERARL_TARGET, defectTarget: DEFECT_TARGET,
      updatedAt: `${pad(now.getDate())}/${pad(now.getMonth() + 1)}/${now.getFullYear()} ${pad(now.getHours())}:${pad(now.getMinutes())}`,
      dateRange, nDays: days.length
    };
    return { tg, pd, btp, meta };
  }

  const api = { buildReport, finish };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.XgParse = api;
})(typeof window !== 'undefined' ? window : globalThis);
