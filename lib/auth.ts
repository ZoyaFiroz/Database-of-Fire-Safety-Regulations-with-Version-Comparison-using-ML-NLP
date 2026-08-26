// Token storage in localStorage, not an httpOnly cookie - simplest option
// for a demo/dissertation project. Trade-off worth knowing: this is
// readable by any script on the page (XSS risk), which a production app
// would avoid with an httpOnly cookie + a backend session instead.
const TOKEN_KEY = "fire_regs_auth_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}
