import { Icon } from './Icons';
import type { ComponentProps } from 'react';
const problems: {title:string; description:string; icon:ComponentProps<typeof Icon>['name']}[] = [
  {title:'Данные разбросаны', description:'Списки на разных сайтах, сложно собрать полную картину.', icon:'layers'},
  {title:'Конкурс постоянно меняется', description:'Позиции и проходные баллы меняются каждый день.', icon:'bolt'},
  {title:'Неясные шансы', description:'Трудно понять, хватит ли баллов и как действовать дальше.', icon:'help'},
];
export function Problems() {return <section className="problems container section" id="how-it-works"><h2>Почему поступать вслепую — риск?</h2><div className="problems-grid">{problems.map(p=><article className="problem-card" key={p.title}><span className="problem-icon"><Icon name={p.icon} size={24}/></span><div><h3>{p.title}</h3><p>{p.description}</p></div></article>)}</div></section>}
