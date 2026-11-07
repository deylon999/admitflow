export function navigate(to: string): void {
  if (typeof window === 'undefined') return;
  const target = new URL(to, window.location.href);
  if (target.origin !== window.location.origin) {
    window.location.href = to;
    return;
  }
  if (target.pathname === window.location.pathname && target.hash) {
    const element = document.getElementById(target.hash.slice(1));
    element?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    return;
  }
  window.history.pushState({}, '', target.pathname + target.search + target.hash);
  window.dispatchEvent(new PopStateEvent('popstate'));
  window.scrollTo({ top: 0, behavior: 'instant' });
}

export function interceptInternalLinks(event: MouseEvent): void {
  const target = event.target;
  if (!(target instanceof Element)) return;
  const link = target.closest('a[href]') as HTMLAnchorElement | null;
  if (!link || link.target === '_blank' || link.download) return;
  if (event.metaKey || event.ctrlKey || event.altKey || event.shiftKey || event.button !== 0) return;
  if (!link.href.startsWith(window.location.origin)) return;
  const href = link.getAttribute('href');
  if (!href || href.startsWith('mailto:') || href.startsWith('tel:')) return;
  event.preventDefault();
  navigate(href);
}
