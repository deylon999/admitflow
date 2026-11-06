import { Link } from 'react-router';
import { Calculator } from '../components/Calculator';
import { RankingDiagram } from '../components/RankingDiagram';

const sources = [
  [
    'Сайты вузов',
    'Каждый вуз публикует список по-своему: свой формат, своё время обновления. Приходится открывать их по очереди и сверять вручную.',
  ],
  [
    'Госуслуги',
    'Статус заявления и положение в конкурсной группе — разные данные. Для ручного расчёта нужно сверить сам список и условия выбранного конкурса.',
  ],
  [
    'Чаты абитуриентов',
    'Люди пересчитывают места друг для друга. Один и тот же человек в разных сообщениях то 120-й, то 74-й.',
  ],
  [
    'Своя таблица',
    'Многие заводят таблицу и вручную вычитают тех, кто выше вне конкурса. Работает, пока не пропустишь обновление.',
  ],
];
const features = [
  [
    'Сценарий по вашим данным',
    'Показываем два условных расчёта для одной группы. Правила и приоритеты вуза нужно проверять отдельно.',
    'Ручной режим',
  ],
  [
    'Все направления на одном экране',
    'Сохранённые направления можно сравнить вместе с историей, исходными числами и датами ручного ввода.',
    'Доступно',
  ],
  [
    'Автоматическое обновление списков',
    'Подключаем проверенные источники. Пока ссылка ведёт на сайт вуза, а числа и дату проверки вы вносите самостоятельно.',
    'В разработке',
  ],
];
const questions = [
  [
    'Что такое согласие на зачисление?',
    'Смысл согласия, способ подачи и связь с приоритетами смотрите в официальных правилах вашей кампании. В ручной модели «без согласия» — отдельная группа людей выше вас для условного сценария. Они не считаются навсегда выбывшими из конкурса.',
  ],
  [
    'Кого зачисляют вне общего конкурса?',
    'В отдельных конкурсах участвуют поступающие по квотам и другим предусмотренным условиям приёма. Для расчёта берите только людей выше вас, которые не участвуют в вашем общем конкурсе. Условия и обозначения уточняйте в конкурсном списке и приёмной комиссии вуза.',
  ],
  [
    'Почему место меняется?',
    'Другие абитуриенты подают или отзывают согласие, меняют приоритеты и выбирают другие вузы. При обновлении списка меняется и ваше положение. Пересчитывайте место по свежим данным.',
  ],
  [
    'Это гарантия поступления?',
    'Нет. Калькулятор показывает положение по введённым цифрам и упрощённой модели. До завершения приёма ситуация может измениться. Окончательное зачисление подтверждает приказ вуза.',
  ],
];

export default function LandingPage() {
  return (
    <main id="top">
      <section
        className="hero container"
        aria-labelledby="hero-title"
      >
        <p className="eyebrow">Конкурсные списки · Приёмная кампания</p>
        <div className="hero-grid">
          <div className="hero-copy">
            <h1 id="hero-title">
              За конкурсными
              <br />
              списками при
              <br />
              поступлении
              <br />
              приходится следить
              <br />
              <span className="accent">вручную</span>
            </h1>
            <p className="hero-description">
              После подачи документов абитуриент неделями открывает списки нескольких вузов, сверяет
              цифры и считает своё реальное место сам. Номер в списке показывает совсем не то, что
              ему нужно знать.
            </p>
            <div className="hero-buttons">
              <a
                className="button button-primary"
                href="#calculator"
              >
                Посчитать своё место
              </a>
              <a
                className="button button-secondary"
                href="#how-it-works"
              >
                Как это устроено
              </a>
            </div>
          </div>
          <aside
            className="example-card surface"
            aria-label="Пример расчёта из интервью"
          >
            <div className="example-heading">
              <span>Случай из интервью</span>
              <span className="tag">Абитуриент, 1 курс</span>
            </div>
            <dl className="example-numbers">
              <div>
                <dt>Номер в списке</dt>
                <dd>120</dd>
              </div>
              <div>
                <dt>Бюджетных мест</dt>
                <dd>90</dd>
              </div>
              <div>
                <dt>Выше него вне конкурса или без согласия</dt>
                <dd>−46</dd>
              </div>
            </dl>
            <div className="example-total">
              <span>Место в ручном сценарии</span>
              <strong>74</strong>
            </div>
            <p className="small-copy">
              В истории из интервью абитуриент сначала решил, что не проходит. Ручной пересчёт
              показал другой сценарий; по рассказу, в итоге его зачислили на 61-м месте из 90. Этот
              пример не гарантирует результат в другом конкурсе.
            </p>
          </aside>
        </div>
        <div
          className="statistics"
          aria-label="Что показали интервью"
        >
          <div className="stat">
            <strong>1–3 недели</strong>
            <p>ежедневных проверок списков, по рассказам абитуриентов</p>
          </div>
          <div className="stat">
            <strong>до 20 часов</strong>
            <p>за лето уходит на сверку сайтов и подсчёты, по оценке абитуриента</p>
          </div>
          <div className="stat">
            <strong>2 из 2</strong>
            <p>абитуриентов чуть не выбрали не тот вуз из-за ошибки в подсчёте места</p>
          </div>
        </div>
        <p className="source-note">Источник: интервью с абитуриентами-первокурсниками</p>
      </section>
      <section
        className="section container problem"
        id="problem"
        aria-labelledby="problem-title"
      >
        <p className="eyebrow">Как это выглядит сейчас</p>
        <h2 id="problem-title">Четыре источника, четыре разных ответа</h2>
        <div className="sources-grid">
          {sources.map(([title, description], index) => (
            <article
              className="source-card surface"
              key={title}
            >
              <span className="card-number">0{index + 1}</span>
              <h3>{title}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
      </section>
      <section
        className="section container explanation"
        id="how-it-works"
        aria-labelledby="explanation-title"
      >
        <div className="explanation-copy">
          <p className="eyebrow">Почему номер не место</p>
          <h2 id="explanation-title">Номер в списке не равен месту</h2>
          <p className="section-description">
            В ручном сценарии из номера вычитаются две непересекающиеся группы людей выше вас: вне
            этого конкурса и остальные без согласия. Если источник уже исключил их, повторно
            вычитать нельзя. Это упрощённый сценарий, а не официальный итог зачисления.
          </p>
        </div>
        <RankingDiagram />
      </section>
      <Calculator />
      <section
        className="section container interviews"
        aria-labelledby="interviews-title"
      >
        <p className="eyebrow">Из интервью</p>
        <h2 id="interviews-title">Что говорят абитуриенты</h2>
        <div className="quotes-grid">
          <figure className="quote-card">
            <blockquote>«Я почти пошёл не туда.»</blockquote>
            <figcaption>Абитуриент, 1 курс, прикладная информатика</figcaption>
          </figure>
          <figure className="quote-card">
            <blockquote>«Как будто каждую минуту.»</blockquote>
            <figcaption>Абитуриент, 1 курс, реклама</figcaption>
          </figure>
        </div>
        <p className="source-note">Цитаты из интервью, без правок по смыслу</p>
      </section>
      <section
        className="section container roadmap"
        aria-labelledby="roadmap-title"
      >
        <p className="eyebrow">Возможности сервиса</p>
        <h2 id="roadmap-title">Один экран вместо пяти сайтов</h2>
        <div className="features-grid">
          {features.map(([title, description, status]) => (
            <article
              className="feature-card surface"
              key={title}
            >
              <span className="tag">{status}</span>
              <h3>{title}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
      </section>
      <section
        className="section container questions"
        id="questions"
        aria-labelledby="questions-title"
      >
        <p className="eyebrow">Вопросы</p>
        <h2 id="questions-title">Частые вопросы</h2>
        <div className="faq-list">
          {questions.map(([question, answer], index) => (
            <details
              key={question}
              open={index === 0}
            >
              <summary>
                {question}
                <span
                  className="faq-icon"
                  aria-hidden="true"
                />
              </summary>
              <p>{answer}</p>
            </details>
          ))}
        </div>
        <div className="final-cta">
          <h2>Проверьте своё место за минуту</h2>
          <a
            className="button"
            href="#calculator"
          >
            Открыть калькулятор
          </a>
        </div>
        <p className="tracker-entry">
          <Link to="/tracker">Сохранить направления и следить за изменениями →</Link>
        </p>
      </section>
    </main>
  );
}
