import { Icon } from './Icons';

/** Decorative forecast preview. Demonstration values only, not model output. */
export function ForecastCard({ compact = false }: { compact?: boolean }) {
  return (
    <article className={`forecast-card ${compact ? 'forecast-card-compact' : ''}`} aria-label="Демонстрация прогноза">
      <div className="forecast-heading">
        <span className="forecast-icon"><Icon name="cap" size={27}/></span>
        <div><strong>Прогноз поступления</strong><span>МГУ · Прикладная математика · демо</span></div>
      </div>
      <div className="forecast-metrics">
        <div className="chance-metric"><span className="metric-label">Шанс поступить</span><strong>74%</strong></div>
        <div className="passing-metric"><span className="metric-label">Прогноз проходного</span><strong>280 – 285</strong><span className="delta-pill">↓ −2 балла</span></div>
      </div>
      <div className="forecast-position"><span className="metric-label">Текущая позиция в списке</span><strong>90 <em>из</em> 128</strong><div className="progress-track"><span/></div></div>
      <span className="visually-hidden">Демонстрационные числа: настоящая прогнозная модель не подключена.</span>
    </article>
  );
}
