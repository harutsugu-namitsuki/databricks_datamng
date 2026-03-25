/**
 * api.js — FastAPI バックエンドとの通信ユーティリティ
 *
 * 使い方:
 *   const products = await api.get('/api/products');
 *   await api.post('/api/orders', { ... });
 */

const API_BASE = '';  // FastAPI と同じオリジンから配信する前提

const api = {
  /** ストレージキー */
  ADMIN_TOKEN_KEY: 'northwind_admin_token',
  STORE_TOKEN_KEY: 'northwind_store_token',

  /** 保存されたトークンを返す */
  getAdminToken() { return localStorage.getItem(this.ADMIN_TOKEN_KEY); },
  getStoreToken() { return localStorage.getItem(this.STORE_TOKEN_KEY); },

  /** トークンを保存 */
  setAdminToken(token) { localStorage.setItem(this.ADMIN_TOKEN_KEY, token); },
  setStoreToken(token) { localStorage.setItem(this.STORE_TOKEN_KEY, token); },

  /** ログアウト */
  clearAdminSession() {
    localStorage.removeItem(this.ADMIN_TOKEN_KEY);
    localStorage.removeItem('northwind_admin_user');
  },
  clearStoreSession() {
    localStorage.removeItem(this.STORE_TOKEN_KEY);
    localStorage.removeItem('northwind_store_customer');
    localStorage.removeItem('northwind_cart');
  },

  /** 共通 fetch ラッパー */
  async _fetch(method, path, body, tokenKey) {
    const token = tokenKey === 'admin'
      ? this.getAdminToken()
      : this.getStoreToken();

    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(API_BASE + path, {
      method,
      headers,
      body: body != null ? JSON.stringify(body) : undefined,
    });

    if (res.status === 401) {
      // 認証切れ → ログインページへ
      const isAdmin = window.location.pathname.includes('/admin/');
      window.location.href = isAdmin ? '/static/admin/login.html' : '/static/store/login.html';
      return;
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const ct = res.headers.get('Content-Type') || '';
    return ct.includes('application/json') ? res.json() : res.text();
  },

  get(path, tokenKey = 'store')    { return this._fetch('GET',    path, null, tokenKey); },
  post(path, body, tokenKey = 'store') { return this._fetch('POST', path, body, tokenKey); },
  put(path, body, tokenKey = 'store')  { return this._fetch('PUT',  path, body, tokenKey); },
};

/** カート (localStorage) */
const cart = {
  CART_KEY: 'northwind_cart',

  getAll() {
    return JSON.parse(localStorage.getItem(this.CART_KEY) || '[]');
  },

  save(items) {
    localStorage.setItem(this.CART_KEY, JSON.stringify(items));
    _updateCartBadge();
  },

  add(product, quantity) {
    const items = this.getAll();
    const existing = items.find(i => i.product_id === product.product_id);
    if (existing) {
      existing.quantity += quantity;
    } else {
      items.push({
        product_id: product.product_id,
        product_name: product.product_name,
        unit_price: product.unit_price,
        quantity,
        max_stock: product.units_in_stock,
      });
    }
    this.save(items);
  },

  remove(productId) {
    this.save(this.getAll().filter(i => i.product_id !== productId));
  },

  updateQty(productId, quantity) {
    const items = this.getAll();
    const item = items.find(i => i.product_id === productId);
    if (item) item.quantity = quantity;
    this.save(items);
  },

  clear() { this.save([]); },

  total() {
    return this.getAll().reduce((sum, i) => sum + i.unit_price * i.quantity, 0);
  },

  count() {
    return this.getAll().reduce((sum, i) => sum + i.quantity, 0);
  },
};

function _updateCartBadge() {
  document.querySelectorAll('.cart-badge').forEach(el => {
    el.textContent = cart.count();
  });
}

/** toast 通知 */
function showToast(msg, type = 'success') {
  const el = document.createElement('div');
  el.textContent = msg;
  el.style.cssText = `
    position: fixed; bottom: 24px; right: 24px; z-index: 9999;
    background: ${type === 'success' ? '#16a34a' : '#dc2626'};
    color: #fff; padding: 12px 20px; border-radius: 8px;
    font-size: 13px; font-weight: 600; box-shadow: 0 4px 16px rgba(0,0,0,0.2);
    animation: slideUp 0.3s ease;
  `;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

/** テーブルを生成するユーティリティ */
function buildTable(container, headers, rows, rowFn) {
  container.innerHTML = '';
  const table = document.createElement('table');
  const thead = document.createElement('thead');
  thead.innerHTML = `<tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>`;
  const tbody = document.createElement('tbody');
  rows.forEach(row => {
    const tr = document.createElement('tr');
    tr.innerHTML = rowFn(row);
    tbody.appendChild(tr);
  });
  table.appendChild(thead);
  table.appendChild(tbody);
  container.appendChild(table);
}

/** ページ読み込み時にカートバッジを更新 */
document.addEventListener('DOMContentLoaded', _updateCartBadge);
