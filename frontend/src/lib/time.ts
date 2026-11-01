/** Match the server's real calendar and microsecond precision, without Date.parse rollover. */
export function compareOpaqueIds(left: string, right: string): number {
  const a = Array.from(left, char => char.codePointAt(0)!);
  const b = Array.from(right, char => char.codePointAt(0)!);
  for (let index = 0; index < Math.min(a.length, b.length); index++) {
    if (a[index] !== b[index]) return a[index] < b[index] ? -1 : 1;
  }
  return Math.sign(a.length - b.length);
}

export function instantMicros(value: string): bigint {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?(Z|[+-]\d{2}:\d{2})$/.exec(value);
  if (!match) throw new Error('Invalid timestamp');
  const [year, month, day, hour, minute, second] = match.slice(1, 7).map(Number);
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (year < 1 || month < 1 || month > 12 || day < 1 || day > days[month - 1] || hour > 23 || minute > 59 || second > 59) throw new Error('Invalid timestamp');
  let offset = 0;
  if (match[8] !== 'Z') {
    const hours = Number(match[8].slice(1, 3));
    const minutes = Number(match[8].slice(4, 6));
    if (hours > 23 || minutes > 59) throw new Error('Invalid timestamp');
    offset = (hours * 60 + minutes) * (match[8][0] === '+' ? 1 : -1);
  }
  const date = new Date(0);
  date.setUTCFullYear(year, month - 1, day);
  date.setUTCHours(hour, minute, second, 0);
  const micros = BigInt(date.getTime() - offset * 60_000) * 1000n + BigInt((match[7] ?? '').padEnd(6, '0'));
  // Python datetime supports UTC years 0001..9999, including microseconds.
  if (micros < -62135596800000000n || micros > 253402300799999999n) throw new Error('Invalid timestamp');
  return micros;
}
