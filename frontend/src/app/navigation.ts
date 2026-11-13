export function navigate(to: string): void {
  if (typeof window === 'undefined') return;
  const target = new URL(to, window.location.href);
  if (target.origin !== window.location.origin) {
    window.location.href = to;
    return;
  }
  if (target.href !== window.location.href) {
    window.history.pushState({}, '', target.pathname + target.search + target.hash);
    window.dispatchEvent(new PopStateEvent('popstate'));
  }
  if (target.hash && !['/auth/verify', '/auth/reset'].includes(target.pathname)) {
    window.requestAnimationFrame(() => document.getElementById(target.hash.slice(1))?.scrollIntoView({ behavior: 'smooth', block: 'start' }));
  } else window.scrollTo({ top: 0, behavior: 'instant' });
}

export function interceptInternalLinks(event: MouseEvent): void {
  const target = event.target;
  if (event.defaultPrevented || !(target instanceof Element)) return;
  const link = target.closest('a[href]');
  if (!(link instanceof HTMLAnchorElement) || (link.target && link.target !== '_self') || link.hasAttribute('download')) return;
  if (event.metaKey || event.ctrlKey || event.altKey || event.shiftKey || event.button !== 0) return;
  if (new URL(link.href).origin !== window.location.origin) return;
  const href = link.getAttribute('href');
  if (!href || href.startsWith('mailto:') || href.startsWith('tel:')) return;
  event.preventDefault();
  navigate(href);
}

/** Decode each route segment once, rejecting malformed encodings and separators. */
export function decodeRouteId(segment: string): string | null {
  try {
    const id = decodeURIComponent(segment);
    return id.trim() && !/[\s/\\?#]/.test(id) && !Array.from(id).some(c => c.charCodeAt(0) < 32 || c.charCodeAt(0) === 127) ? id : null;
  } catch { return null; }
}

export function routeHref(to: string): string {
  if (typeof window === 'undefined' || new URLSearchParams(window.location.search).get('mode') !== 'demo' || !to.startsWith('/') || to.startsWith('//')) return to;
  const target = new URL(to, window.location.href);
  if (target.pathname.startsWith('/universities') || target.pathname.startsWith('/programs') || target.searchParams.has('mode')) return to;
  target.searchParams.set('mode', 'demo');
  return target.pathname + target.search + target.hash;
}
