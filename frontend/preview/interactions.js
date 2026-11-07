/* Offline preview interactions. In src/components these are handled by React state. */
document.querySelectorAll('.faq-item button').forEach(button => {
  button.addEventListener('click', () => {
    const item=button.closest('.faq-item');
    const wasOpen=item.classList.contains('open');
    document.querySelectorAll('.faq-item').forEach(node => {
      node.classList.remove('open');
      const b=node.querySelector('button');if(b){b.setAttribute('aria-expanded','false');b.querySelector('b').textContent='+'}
      node.querySelector('p')?.remove();
    });
    if (!wasOpen) {
      item.classList.add('open');button.setAttribute('aria-expanded','true');button.querySelector('b').textContent='−';
      const texts={
        'Что такое шанс поступления?':'Это прогноз вероятности того, что при текущих баллах и ситуации в конкурсе вы пройдёте на выбранное направление. Он не гарантирует поступление.',
        'Откуда берутся данные?':'В будущем — из официальной статистики ЕГЭ, требований вузов и доступных конкурсных списков. Доступность и частота обновлений зависят от источника.',
        'Как часто обновляется прогноз?':'После обновления доступных источников. Частота зависит от конкретного вуза и приёмной кампании.',
        'Можно ли доверять прогнозу?':'Реальную точность можно утверждать только после проверки модели на исторических данных и исходах зачисления.'
      };const p=document.createElement('p');p.textContent=texts[button.querySelector('span').textContent]||'';item.appendChild(p);
    }
  });
});
document.querySelectorAll('.competitors-tabs button').forEach(button=>{
  button.addEventListener('click',()=>{
    document.querySelectorAll('.competitors-tabs button').forEach(b=>b.classList.toggle('active',b===button));
    const card=button.closest('.competitors-card');
    const table=card.querySelector('table');let info=card.querySelector('.tab-placeholder');
    if (button.textContent==='Список абитуриентов') {table.style.display='table'; info?.remove()}
    else {table.style.display='none';if(!info){info=document.createElement('div');info.className='tab-placeholder';card.appendChild(info)}info.innerHTML=`<strong>${button.textContent==='Динамика'?'Позиция обновляется':'Информация о конкурентах'}</strong><span>Демо-интерфейс. Реальные данные появятся после подключения источников.</span>`}
  });
});
document.querySelector('.calc-form')?.addEventListener('submit', e=>{
  e.preventDefault();const root=document.querySelector('.calculator-section');let message=root.querySelector('.calc-message');
  if(!message){message=document.createElement('p');message.className='calc-message';message.setAttribute('role','status');root.appendChild(message)}
  message.textContent='Пример результата: 74%. Когда подключим данные и модель, расчёт будет зависеть от твоих баллов и конкурса.';
});
