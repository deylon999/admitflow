export function limitCodePoints(value: string, max: number): string {
  return Array.from(value).slice(0, max).join('');
}
