import { useEffect } from 'react';
import { useLocation } from 'react-router';
export function PagePosition() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    document.title = pathname.startsWith('/sources')
      ? 'Источники и группы — Абитуриент'
      : pathname === '/tracker'
        ? 'Мои направления — Абитуриент'
        : pathname === '/'
          ? 'Абитуриент — ручные сценарии поступления'
          : 'Страница не найдена — Абитуриент';
    const observer = new MutationObserver(position);
    function position() {
      const target = hash
        ? document.getElementById(hash.slice(1))
        : document.querySelector<HTMLElement>('main h1');
      if (!target) return false;
      target.tabIndex = -1;
      target.focus({ preventScroll: true });
      if (hash) target.scrollIntoView();
      else window.scrollTo(0, 0);
      observer.disconnect();
      return true;
    }
    if (!position())
      observer.observe(document.getElementById('root')!, { childList: true, subtree: true });
    return () => observer.disconnect();
  }, [pathname, hash]);
  return null;
}
