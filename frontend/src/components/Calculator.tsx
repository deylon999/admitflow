import { useState, type FormEvent } from 'react';
import { Icon } from './Icons';

export function Calculator() {
  const [message, setMessage] = useState('');
  function submit(event: FormEvent<HTMLFormElement>) {event.preventDefault();setMessage('Пример результата: 74%. Когда подключим данные и модель, расчёт будет зависеть от твоих баллов и конкурса.');}
  return <section className="calculator-section full-container" id="calculator">
    <div className="calculator-left"><h2>Посчитайте<br/>свои шансы<br/>за минуту</h2><p>Введите баллы ЕГЭ и направление —<br/>и получите прогноз поступления.</p><span className="ring ring-white"/><span className="lime-accent"/></div>
    <div className="calculator-panel"><form className="calc-form" onSubmit={submit}><label>Направление<select defaultValue="Прикладная математика"><option>Прикладная математика</option><option>Программная инженерия</option><option>Информатика и вычислительная техника</option></select></label><label>Вуз<select defaultValue="МГУ"><option>МГУ</option><option>МТУСИ</option><option>РТУ МИРЭА</option></select></label><div className="scores"><label>Математика<input type="number" min="0" max="100" defaultValue="98"/></label><label>Русский язык<input type="number" min="0" max="100" defaultValue="94"/></label><label>Информатика<input type="number" min="0" max="100" defaultValue="95"/></label></div><button className="button button-primary calc-submit" type="submit">Рассчитать прогноз <Icon name="arrow" size={16}/></button></form>
    <div className="calc-summary"><strong className="calc-caption">Ваш шанс поступить · демо</strong><div className="calc-chance"><span>74%</span><div className="calc-trend"><strong>↑ +12%</strong><small>к прошлой неделе</small></div></div><div className="calc-result-row"><div><small>Прогноз проходного</small><b>280 – 285</b></div><div><small>Ваша позиция</small><b>90 <span>из 128</span></b></div></div></div></div>
    {message && <p className="calc-message" role="status">{message}</p>}
  </section>;
}
