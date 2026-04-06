/**
 * CSU Date 前端 API 工具
 * Token：优先 csudate_token（与 login 一致），兼容旧键 csudate_access_token。
 * API 根：默认 http://127.0.0.1:8888，可 localStorage.setItem('csudate_api_base', url) 覆盖。
 */
(function () {
  var KEY_TOKEN = 'csudate_token';
  var KEY_TOKEN_LEGACY = 'csudate_access_token';
  var KEY_API = 'csudate_api_base';

  window.csudateGetToken = function () {
    return localStorage.getItem(KEY_TOKEN) || localStorage.getItem(KEY_TOKEN_LEGACY);
  };

  // 本地开发用 127.0.0.1:8888，线上 Nginx 反代同域名用空串
  var DEFAULT_API = location.hostname === '127.0.0.1' || location.hostname === 'localhost'
    ? 'http://127.0.0.1:8888'
    : '';

  window.CSU_DATE_API_BASE = function () {
    return (localStorage.getItem(KEY_API) || DEFAULT_API).replace(/\/$/, '');
  };

  window.csudateSetApiBase = function (url) {
    if (url) localStorage.setItem(KEY_API, String(url).replace(/\/$/, ''));
    else localStorage.removeItem(KEY_API);
  };

  window.csudateAuthHeaders = function (jsonBody) {
    var h = {};
    if (jsonBody !== false) h['Content-Type'] = 'application/json';
    var t = window.csudateGetToken();
    if (t) h['Authorization'] = 'Bearer ' + t;
    return h;
  };

  window.csudateFetch = function (path, options) {
    options = options || {};
    var url = CSU_DATE_API_BASE() + path;
    var headers = Object.assign({}, csudateAuthHeaders(true), options.headers || {});
    if (options.body instanceof FormData) delete headers['Content-Type'];
    return fetch(url, Object.assign({}, options, { headers: headers })).then(function (res) {
      if (res.status === 401) {
        localStorage.removeItem(KEY_TOKEN);
        localStorage.removeItem(KEY_TOKEN_LEGACY);
        localStorage.removeItem('csudate_user');
      }
      return res;
    });
  };

  window.csudateLogout = function () {
    localStorage.removeItem(KEY_TOKEN);
    localStorage.removeItem(KEY_TOKEN_LEGACY);
    localStorage.removeItem('csudate_user');
  };

  window.csudateApiErrorMessage = function (data) {
    if (!data || data.detail == null) return '请求失败';
    if (typeof data.detail === 'string') return data.detail;
    if (Array.isArray(data.detail))
      return data.detail
        .map(function (d) {
          return d.msg || d.message || JSON.stringify(d);
        })
        .join('；');
    return String(data.detail);
  };

  window.csudateRefreshMe = async function () {
    if (!window.csudateGetToken()) return null;
    var res = await csudateFetch('/api/user/me', { method: 'GET' });
    if (res.status === 401) {
      window.location.href = 'login.html';
      return null;
    }
    if (!res.ok) return null;
    var user = await res.json();
    localStorage.setItem('csudate_user', JSON.stringify(user));
    // 全局教育邮箱警告
    window._csudateShowEduWarning(user);
    return user;
  };

  /* ── 全局教育邮箱未验证警告条 ── */
  var EDU_BANNER_ID = '_csudate_global_edu_warn';

  window._csudateShowEduWarning = function (u) {
    if (!u) return;
    // 已验证或在 dashboard 页面（dashboard 有自己的 banner）
    if (u.eduEmailVerified) {
      var existing = document.getElementById(EDU_BANNER_ID);
      if (existing) existing.remove();
      return;
    }
    var isDashboard = location.pathname.indexOf('dashboard.html') !== -1;
    if (isDashboard) return; // dashboard 自带 banner，不重复

    if (document.getElementById(EDU_BANNER_ID)) return; // 已存在

    var banner = document.createElement('div');
    banner.id = EDU_BANNER_ID;

    var blocked = !!u.eduBlocked;
    var bgColor = blocked
      ? 'linear-gradient(135deg, #dc2626, #b91c1c)'
      : 'linear-gradient(135deg, #f59e0b, #d97706)';
    var msg = blocked
      ? '你的教育邮箱未验证且已超期，匹配功能已暂停！请立即前往仪表盘验证 @csu.edu.cn 邮箱。'
      : '你使用的是非教育邮箱注册，请尽快验证 @csu.edu.cn 教育邮箱，否则将无法参与匹配。';

    banner.innerHTML = ''
      + '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">'
      +   '<div style="display:flex;align-items:center;gap:8px;">'
      +     '<span style="font-size:1.4em;">' + (blocked ? '\u26A0\uFE0F' : '\uD83D\uDCE7') + '</span>'
      +     '<span>' + msg + '</span>'
      +   '</div>'
      +   '<a href="dashboard.html" style="'
      +     'background:rgba(255,255,255,0.25);color:#fff;padding:6px 16px;border-radius:20px;'
      +     'text-decoration:none;font-weight:600;font-size:0.85em;white-space:nowrap;'
      +     'backdrop-filter:blur(4px);border:1px solid rgba(255,255,255,0.3);'
      +   '">前往验证</a>'
      + '</div>';

    banner.setAttribute('style', ''
      + 'position:fixed;top:0;left:0;right:0;z-index:9999;'
      + 'background:' + bgColor + ';'
      + 'color:#fff;padding:12px 20px;font-size:0.875rem;font-weight:500;'
      + 'box-shadow:0 4px 20px rgba(0,0,0,0.25);'
      + 'animation:_eduSlideDown 0.4s ease;'
    );

    // 注入动画 keyframe
    if (!document.getElementById('_csudate_edu_anim')) {
      var style = document.createElement('style');
      style.id = '_csudate_edu_anim';
      style.textContent = '@keyframes _eduSlideDown{from{transform:translateY(-100%);opacity:0}to{transform:translateY(0);opacity:1}}';
      document.head.appendChild(style);
    }

    document.body.insertBefore(banner, document.body.firstChild);

    // 推下页面内容，避免被遮挡
    document.body.style.paddingTop = (banner.offsetHeight + 4) + 'px';
  };

  // 页面加载时也尝试从缓存显示
  document.addEventListener('DOMContentLoaded', function () {
    try {
      var cached = localStorage.getItem('csudate_user');
      if (cached) window._csudateShowEduWarning(JSON.parse(cached));
    } catch (e) {}
  });
})();
