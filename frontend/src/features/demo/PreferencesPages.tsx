import { useState } from 'react';
import { PageTitle, Surface } from '../../shared/UI';

export function ProfilePage() {
  const [name, setName] = useState('Абитуриент');
  const [city, setCity] = useState('Москва');
  const [saved, setSaved] = useState(false);
  return (
    <>
      <PageTitle kicker="МОИ ДАННЫЕ" title="Настрой профиль." description="Добавь актуальные данные для персонального прогноза." />
      <div className="af-split-grid af-split-grid--form">
        <Surface title="Основная информация">
          <div className="af-form-grid">
            <label className="af-field"><span>ИМЯ</span><input value={name} onChange={e => setName(e.target.value)} /></label>
            <label className="af-field"><span>ГОРОД</span><input value={city} onChange={e => setCity(e.target.value)} /></label>
            <label className="af-field"><span>ГОД ПОСТУПЛЕНИЯ</span><select defaultValue="2027"><option>2027</option><option>2026</option></select></label>
          </div>
          <button className="af-action af-action--primary" type="button" onClick={() => setSaved(true)}>Сохранить изменения</button>
          {saved && <div className="af-inline-success">Демо: изменения не сохраняются на сервере.</div>}
        </Surface>
        <Surface tone="lime" title="Твои баллы — твой выбор." description="Добавь результаты, чтобы сравнивать возможные варианты. Изменения в реальной системе должны храниться безопасно." />
      </div>
    </>
  );
}

export function SettingsPage() {
  const [theme, setTheme] = useState('Системная');
  const [notifications, setNotifications] = useState(true);
  const [showConfirm, setShowConfirm] = useState(false);
  return (
    <>
      <PageTitle kicker="НАСТРОЙКИ" title="Управляй своим пространством." description="Уведомления, тема и приватность." />
      <div className="af-split-grid">
        <Surface title="Внешний вид и события">
          <label className="af-field"><span>ТЕМА ИНТЕРФЕЙСА</span><select value={theme} onChange={e => setTheme(e.target.value)}><option>Системная</option><option>Светлая</option><option>Тёмная</option></select></label>
          <label className="af-check"><input type="checkbox" checked={notifications} onChange={e => setNotifications(e.target.checked)} />Показывать изменения по выбранным программам</label>
          <p className="af-caption">Переключение темы показано как UI-сценарий; полная тёмная тема не реализована в этом наборе.</p>
        </Surface>
        <Surface title="Данные и приватность">
          <p>В рабочем продукте нужны экспорт, удаление, безопасное хранение и контроль срока гостевой сессии.</p>
          <button className="af-danger-button" type="button" onClick={() => setShowConfirm(true)}>Очистить мои данные</button>
        </Surface>
      </div>
      {showConfirm && <div className="af-modal-backdrop"><div className="af-modal" role="dialog" aria-modal="true" aria-label="Подтверждение удаления"><h2>Очистить данные?</h2><p>Подтверди действие перед удалением данных.</p><div><button onClick={() => setShowConfirm(false)} type="button">Отмена</button><button onClick={() => setShowConfirm(false)} type="button">Понятно</button></div></div></div>}
    </>
  );
}
