export function SortField({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return <label className="af-field"><span>СОРТИРОВКА</span><select value={value} onChange={e => onChange(e.target.value)}>
    <option value="name">По названию А–Я</option><option value="name-desc">По названию Я–А</option>
  </select></label>;
}

export function YearField({ value, years, onChange }: { value: string; years: number[]; onChange: (value: string) => void }) {
  const options = [...new Set([...years.map(String), ...(value ? [value] : [])])].sort().reverse();
  return <label className="af-field"><span>ГОД ПОСТУПЛЕНИЯ</span><select value={value} onChange={e => onChange(e.target.value)}>
    <option value="">Все годы</option>{options.map(year => <option key={year}>{year}</option>)}
  </select></label>;
}
