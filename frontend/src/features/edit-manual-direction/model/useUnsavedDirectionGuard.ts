import { useEffect } from 'react';
import { useBlocker } from 'react-router';

export function useUnsavedDirectionGuard(dirty: boolean, currentDraft: string, pending: boolean) {
  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      (dirty || pending) &&
      (currentLocation.pathname !== nextLocation.pathname ||
        currentLocation.search !== nextLocation.search),
  );
  useEffect(() => {
    if (blocker.state !== 'blocked') return;
    if (pending) blocker.reset();
    else if (window.confirm('Покинуть форму с несохранёнными изменениями?')) blocker.proceed();
    else blocker.reset();
  }, [blocker, pending]);
  useEffect(() => {
    if (!dirty && !pending) return;
    let acceptedLink = false;
    const beforeUnload = (event: BeforeUnloadEvent) => {
      if (pending || !acceptedLink) {
        event.preventDefault();
        event.returnValue = '';
      }
    };
    const guardLink = (event: MouseEvent) => {
      const link =
        event.target instanceof Element ? event.target.closest<HTMLAnchorElement>('a[href]') : null;
      if (
        !link ||
        link.target === '_blank' ||
        link.hasAttribute('download') ||
        link.hasAttribute('data-router-link') ||
        event.button !== 0 ||
        event.ctrlKey ||
        event.metaKey ||
        event.shiftKey ||
        event.altKey
      )
        return;
      const target = new URL(link.href, location.href);
      if (
        target.origin === location.origin &&
        target.pathname === location.pathname &&
        target.search === location.search
      )
        return;
      if (pending) {
        event.preventDefault();
        event.stopPropagation();
        return;
      }
      if (!window.confirm('Удалить несохранённые изменения формы и перейти?')) {
        event.preventDefault();
        event.stopPropagation();
      } else acceptedLink = true;
    };
    window.addEventListener('beforeunload', beforeUnload);
    document.addEventListener('click', guardLink, true);
    return () => {
      window.removeEventListener('beforeunload', beforeUnload);
      document.removeEventListener('click', guardLink, true);
    };
  }, [dirty, currentDraft, pending]);
}
