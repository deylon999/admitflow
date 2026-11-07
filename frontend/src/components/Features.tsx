import { Icon } from './Icons';
import type { ComponentProps } from 'react';
const features: {title:string; description:string; tone:string; icon:ComponentProps<typeof Icon>['name']}[]=[
  {title:'Сложность ЕГЭ', description:'Анализируем уровень заданий и влияние на баллы.', tone:'blue', icon:'chart'},
  {title:'Прошлые проходные', description:'Учитываем историю и тренды за несколько лет.', tone:'lime', icon:'cap'},
  {title:'Конкуренты', description:'Оцениваем динамику заявлений и возможное поведение поступающих.', tone:'red', icon:'users'},
  {title:'Конкурсные списки', description:'Анализируем актуальные списки и динамику позиций.', tone:'violet', icon:'list'},
];
export function Features(){return <section className="features container section" id="features"><h2>Что учитывает прогноз?</h2><div className="features-grid">{features.map(f=><article key={f.title} className={`feature-card feature-${f.tone}`}><Icon name={f.icon} size={24}/><h3>{f.title}</h3><p>{f.description}</p></article>)}</div></section>}
