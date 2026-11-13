// Email credentials live only in memory. Strip the fragment before React or API work.
let link: { path: string; token: string } | undefined;
export function captureAuthLink(): boolean {
    const { pathname, hash, search } = window.location;
    if (pathname !== '/auth/verify' && pathname !== '/auth/reset') return false;
    if (!hash && !search) return false;
    const params = new URLSearchParams(hash.slice(1));
    const tokens = params.getAll('token');
    const token = tokens.length === 1 && [...params.keys()].length === 1 && /^[A-Za-z0-9_-]{43}$/.test(tokens[0]) ? tokens[0] : '';
    link = { path: pathname, token };
    // Never accept query credentials or callback redirects. Preserve only Demo selection.
    const demo = new URLSearchParams(search).get('mode') === 'demo' ? '?mode=demo' : '';
    window.history.replaceState(window.history.state, '', pathname + demo);
    return true;
}
export function readAuthLink(path: string): string { return link?.path === path ? link.token : ''; }
export function forgetAuthLink() { link = undefined; }
