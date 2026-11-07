import { Button, Card } from '@/shared/ui';
import { Component, createRef } from 'react';
import type { ReactNode } from 'react';

export class PageErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  heading = createRef<HTMLHeadingElement>();
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch() {
    document.title = 'Не удалось открыть страницу — Абитуриент';
    this.heading.current?.focus();
  }
  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <main
        id="top"
        className="container page-shell"
      >
        <Card className="page-message">
          <h1
            ref={this.heading}
            tabIndex={-1}
          >
            Не удалось открыть страницу
          </h1>
          <p className="section-description">
            Обновите страницу и попробуйте снова. Уже сохранённые на сервере данные при этом не
            удаляются.
          </p>
          <div className="page-actions">
            <Button
              variant="primary"

              type="button"
              onClick={() => window.location.reload()}
            >
              Обновить страницу
            </Button>
            <a
              className="button button-secondary"
              href="/"
            >
              На главную
            </a>
          </div>
        </Card>
      </main>
    );
  }
}
