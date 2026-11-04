#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Biến một file giao diện dashboard (có sẵn dòng  const RAW = {...};  nhúng cứng số liệu)
thành index.html dùng cho Netlify + Supabase: số liệu được nạp từ Supabase thay vì nhúng cứng.

Cách dùng:
    python build_index.py "Báo cáo Ver 1.html"             -> ghi ra index.html cạnh file nguồn
    python build_index.py "Báo cáo Ver 1.html" -o out.html

Chỉ dùng thư viện chuẩn của Python, không cần cài thêm.
Mọi chức năng của giao diện (bộ lọc, chọn màu, Sáng/Tối, biểu đồ) giữ nguyên.
"""
import argparse
import re
import sys
from pathlib import Path

EMPTY_RAW = (
    'let RAW = {tg:[],pd:[],btp:[],meta:{months:[],weeks:[],days:[],lines:[],types:[],'
    'hplTarget:0.25,cerarlTarget:0.30,defectTarget:0.0005,dateRange:"",nDays:0,updatedAt:""}};'
)

EXTRA_CSS = """<style>
#xg-msg{position:fixed;inset:0;z-index:50;display:flex;align-items:center;justify-content:center;background:var(--bg);color:var(--text);font:600 16px/1.5 system-ui,sans-serif;text-align:center;padding:24px}
#xg-msg small{display:block;color:var(--muted);font-weight:400;margin-top:6px}
#xg-msg a{color:var(--red)}
.footer a{color:var(--red);text-decoration:none;font-weight:600}
</style>
"""

LOADER = """/* ---- Nạp số liệu từ Supabase rồi dựng báo cáo ---- */
(function () {
  const CFG = window.APP_CONFIG || {};
  const box = document.createElement('div');
  box.id = 'xg-msg';
  box.innerHTML = '<div>Đang tải số liệu…</div>';
  document.body.appendChild(box);
  const say = (t, sub) => { box.innerHTML = '<div>' + t + (sub ? '<small>' + sub + '</small>' : '') + '</div>'; };
  if (!CFG.SUPABASE_URL || !CFG.SUPABASE_ANON_KEY || CFG.SUPABASE_URL.indexOf('YOUR') >= 0) {
    say('Chưa cấu hình kết nối', 'Mở file config.js và điền SUPABASE_URL, SUPABASE_ANON_KEY (xem README).');
    return;
  }
  const headers = { apikey: CFG.SUPABASE_ANON_KEY };
  if (CFG.SUPABASE_ANON_KEY.indexOf('eyJ') === 0) headers.Authorization = 'Bearer ' + CFG.SUPABASE_ANON_KEY;
  const get = q => fetch(CFG.SUPABASE_URL + '/rest/v1/report?id=eq.1&select=' + q, { headers }).then(r => {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  });
  get('data,updated_at').then(rows => {
    if (!rows.length) {
      say('Chưa có số liệu', 'Vào <a href="upload.html">Cập nhật dữ liệu</a> để tải file Excel lên lần đầu.');
      return;
    }
    RAW = rows[0].data;
    const stamp = rows[0].updated_at;
    box.remove();
    setupFilters();
    initCharts();
    refresh();
    window.__xgReady = true;
    // tự tải lại khi có số liệu mới (kiểm tra mỗi phút, chỉ tải lại khi có thay đổi)
    setInterval(() => {
      if (document.hidden) return;
      get('updated_at').then(r => { if (r.length && r[0].updated_at !== stamp) location.reload(); }).catch(() => {});
    }, 60000);
  }).catch(e => say('Không tải được số liệu', 'Kiểm tra mạng và cấu hình config.js. (' + e.message + ')'));
})();
</script>"""

VIEW_HEAD = """<script>(function(){try{var d=document.documentElement,v=localStorage.getItem('xg-view');var coarse=window.matchMedia&&matchMedia('(pointer:coarse)').matches;var small=Math.min(screen.width,screen.height)<700;if(v!=='mobile'&&v!=='desktop')v=(coarse&&small)?'mobile':'desktop';d.setAttribute('data-view',v);var m=document.querySelector('meta[name=viewport]');if(m)m.setAttribute('content',(coarse&&small&&v==='desktop')?'width=1280':'width=device-width, initial-scale=1.0')}catch(e){}})();</script>
"""

VIEW_CSS = """<style>
/* Tùy chọn kiểu xem: data-view="desktop" | "mobile" */
.view-pick .skin-menu{min-width:200px}
html[data-view="mobile"]{background:var(--bg)}
html[data-view="mobile"] body{max-width:440px;margin:0 auto;padding:12px 12px 20px;box-shadow:0 0 0 1px var(--border);min-height:100vh}
html[data-view="mobile"] .header{flex-direction:column;align-items:stretch;gap:10px;margin-bottom:10px}
html[data-view="mobile"] .header-left h1{font-size:18px;padding-left:10px}
html[data-view="mobile"] .header-left .sub{padding-left:14px}
html[data-view="mobile"] .header-right{width:100%;display:flex;flex-wrap:wrap;gap:8px}
html[data-view="mobile"] .filters{width:100%;display:grid;grid-template-columns:1fr 1fr;gap:8px}
html[data-view="mobile"] .filter-item select{width:100%;min-width:0}
html[data-view="mobile"] .btn-reset{grid-column:1/-1;padding:8px}
html[data-view="mobile"] .skin-pick:not(.view-pick){flex:1 1 100%}
html[data-view="mobile"] .skin-pick .theme-btn{width:100%;justify-content:center}
html[data-view="mobile"] .view-pick{flex:1 1 0;min-width:0}
html[data-view="mobile"] #themeBtn{flex:1 1 0;justify-content:center}
html[data-view="mobile"] .skin-pick:not(.view-pick) .skin-menu{left:0;right:auto;min-width:0;width:100%}
html[data-view="mobile"] .view-pick .skin-menu{left:0;right:auto}
html[data-view="mobile"] .kpi-row{grid-template-columns:1fr 1fr;gap:8px}
html[data-view="mobile"] .kpi-row .kpi:last-child{grid-column:1/-1}
html[data-view="mobile"] .kpi .gauge-mini{display:none}
html[data-view="mobile"] .kpi .k-badge{display:none}
html[data-view="mobile"] .kpi-row>*,html[data-view="mobile"] .row2>*,html[data-view="mobile"] .row3>*{min-width:0}
html[data-view="mobile"] .heat-wrap,html[data-view="mobile"] .tbl-wrap{max-width:100%}
html[data-view="mobile"] .row2,html[data-view="mobile"] .row3{grid-template-columns:1fr;gap:8px}
html[data-view="mobile"] .chart-box{height:190px}
html[data-view="mobile"] .tbl-wrap{max-height:320px}
html[data-view="mobile"] .footer{flex-direction:column;align-items:flex-start;gap:4px}
</style>
"""

VIEW_HTML = """<div class="skin-pick view-pick" id="viewPick">
      <button class="theme-btn" id="viewBtn" type="button" aria-haspopup="true" aria-expanded="false" title="Chọn kiểu xem">
        <svg id="viewIcon" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"></svg>
        <span id="viewLabel">Máy tính</span><span aria-hidden="true">▾</span>
      </button>
      <div class="skin-menu" id="viewMenu" role="menu"></div>
    </div>
    """

VIEW_JS = """<script>
/* Tùy chọn kiểu xem: Máy tính / Điện thoại */
(function () {
  const root = document.documentElement;
  const $ = id => document.getElementById(id);
  const MON = '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>';
  const PHN = '<rect x="6" y="2" width="12" height="20" rx="2"/><path d="M11 18h2"/>';
  const VIEWS = [
    { id: 'desktop', name: 'Xem trên Máy tính', short: 'Máy tính', icon: MON },
    { id: 'mobile', name: 'Xem trên Điện thoại', short: 'Điện thoại', icon: PHN }
  ];
  const coarse = window.matchMedia && matchMedia('(pointer:coarse)').matches;
  const menu = $('viewMenu'), btn = $('viewBtn');
  function paint() {
    const v = VIEWS.find(x => x.id === root.getAttribute('data-view')) || VIEWS[0];
    $('viewLabel').textContent = v.short;
    $('viewIcon').innerHTML = v.icon;
    menu.querySelectorAll('button').forEach(b => b.classList.toggle('active', b.dataset.id === v.id));
  }
  function apply(id) {
    try { localStorage.setItem('xg-view', id); } catch (e) {}
    if (coarse) { location.reload(); return; }   // điện thoại/máy tính bảng: tải lại để trình duyệt đổi khung nhìn
    root.setAttribute('data-view', id);
    paint();
    if (window.__xgReady) {
      refresh();
      setTimeout(() => window.dispatchEvent(new Event('resize')), 60);
    }
  }
  menu.innerHTML = VIEWS.map(v =>
    '<button type="button" role="menuitem" data-id="' + v.id + '"><svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">' + v.icon + '</svg>' + v.name + '</button>').join('');
  menu.querySelectorAll('button').forEach(b => b.addEventListener('click', () => { menu.classList.remove('open'); btn.setAttribute('aria-expanded', 'false'); apply(b.dataset.id); }));
  btn.addEventListener('click', ev => {
    ev.stopPropagation();
    const sm = document.getElementById('skinMenu'); if (sm) sm.classList.remove('open');
    const open = !menu.classList.contains('open');
    menu.classList.toggle('open', open);
    btn.setAttribute('aria-expanded', open);
  });
  document.addEventListener('click', e => { if (!e.target.closest('#viewPick')) { menu.classList.remove('open'); btn.setAttribute('aria-expanded', 'false'); } }, true);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') menu.classList.remove('open'); });
  paint();
})();
</script>
"""


def fail(msg):
    print("LỖI: " + msg)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    src = Path(a.src)
    out = Path(a.out) if a.out else src.with_name("index.html")
    s = src.read_text(encoding="utf-8")
    had_link = "upload.html" in s

    # 1. dòng số liệu nhúng cứng -> RAW rỗng
    m = re.search(r"^const RAW = .*;$", s, re.M)
    if not m:
        fail("Không thấy dòng 'const RAW = {...};' trong file nguồn. File này đã là bản dùng Supabase hoặc khác cấu trúc.")
    s = s[: m.start()] + EMPTY_RAW + s[m.end():]
    print("  ✓ thay số liệu nhúng cứng bằng RAW rỗng")

    # 2. nạp config.js + CSS cho màn hình chờ
    if "</head>" not in s:
        fail("Không thấy thẻ </head>.")
    s = s.replace("</head>", VIEW_HEAD + '<script src="config.js"></script>\n' + EXTRA_CSS + VIEW_CSS + "</head>", 1)
    print("  ✓ thêm config.js và CSS màn hình chờ")

    # 3. thay đoạn khởi động cuối file bằng đoạn nạp từ Supabase
    pat = re.compile(r"setupFilters\(\);\s*initCharts\(\);\s*refresh\(\);\s*</script>")
    if len(pat.findall(s)) != 1:
        fail("Không thấy đúng 1 đoạn khởi động 'setupFilters(); initCharts(); refresh();' ở cuối file.")
    s = pat.sub(lambda _m: LOADER, s)
    print("  ✓ thay đoạn khởi động bằng bộ nạp Supabase")

    # 4. liên kết sang trang cập nhật ở chân trang (không bắt buộc)
    pf = re.compile(r'(<div class="footer">\s*<div>)([^<]*)(</div>)')
    if pf.search(s) and not had_link:
        s = pf.sub(lambda m: m.group(1) + m.group(2) + ' · <a href="upload.html">Cập nhật dữ liệu</a>' + m.group(3), s, count=1)
        print("  ✓ thêm liên kết 'Cập nhật dữ liệu' ở chân trang")
    else:
        print("  - bỏ qua liên kết chân trang (không tìm thấy khối footer)")

    # 5. tùy chọn kiểu xem (Máy tính / Điện thoại), đặt cạnh nút chọn màu và nút Sáng/Tối
    anchor = '<button class="theme-btn" id="themeBtn"'
    if s.count(anchor) != 1 or "</body>" not in s:
        fail("Không tìm thấy nút Sáng/Tối (id=themeBtn) hoặc thẻ </body> để gắn tùy chọn kiểu xem.")
    s = s.replace(anchor, VIEW_HTML + anchor, 1)
    s = s[: s.rindex("</body>")] + VIEW_JS + s[s.rindex("</body>"):]
    print("  ✓ thêm tùy chọn kiểu xem: Máy tính / Điện thoại")

    out.write_text(s, encoding="utf-8")
    print(f"Xong: {out}  ({len(s) // 1024} KB)")


if __name__ == "__main__":
    main()
