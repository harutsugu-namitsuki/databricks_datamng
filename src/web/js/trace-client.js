/* trace-client.js — 全通信に trace_id を付与する計装（被観測アプリ側に読み込む）。
 * 決定#1: クリックを伴わない自動発火通信も含め、全 fetch を対象にする。
 * window.fetch を最優先でパッチするため、api.js より前に読み込むこと。 */
(function () {
  let currentRoot = null;     // 直近のユーザー操作(クリック)に対応する trace_id
  let rootSetAt = 0;

  function newId() {
    return (Date.now().toString(36) + Math.random().toString(36).slice(2, 6));
  }

  // ユーザー操作（クリック/サブミット）を起点に root を更新。
  // 同一クリックから派生する複数 fetch を 1 trace に束ねる（要件 #6）。
  function markRoot() { currentRoot = newId(); rootSetAt = Date.now(); }
  document.addEventListener('click', markRoot, true);
  document.addEventListener('submit', markRoot, true);

  const _fetch = window.fetch.bind(window);
  window.fetch = function (input, init) {
    init = init || {};
    const headers = new Headers(init.headers || (input instanceof Request ? input.headers : undefined));
    // クリック直後(2秒以内)は同じ root を、そうでなければ自動発火として新規 trace を採番。
    const tid = (currentRoot && (Date.now() - rootSetAt) < 2000) ? currentRoot : newId();
    headers.set('X-Trace-Id', tid);
    return _fetch(input, Object.assign({}, init, { headers }));
  };
})();
