import { ForecastCard } from './ForecastCard';
import { Icon } from './Icons';

export function Hero() {
  return <section className="hero container" aria-labelledby="hero-title">
    <div className="hero-copy">
      <h1 id="hero-title">Оцени шансы<br/>на поступление<br/><span>с точным<br/>прогнозом</span></h1>
      <p>Конкурсные списки, конкуренты, сложность ЕГЭ<br className="desktop-only"/> и динамика кампании — в одном сервисе.</p>
      <div className="hero-actions"><a href="#calculator" className="button button-primary">Оценить свои шансы <Icon name="arrow" size={16}/></a><a href="#how-it-works" className="button button-outline">Как это работает</a></div>
    </div>
    <div className="hero-art" aria-hidden="false"><span className="hero-shape hero-lime"/><span className="hero-shape hero-red"/><span className="hero-shape hero-purple"/><ForecastCard/></div>
  </section>;
}
