/** Validate structure before JSON.parse can discard duplicate object members. */
export function parseStrictJson(source: string): unknown {
  let offset = 0;
  const fail = (): never => { throw new Error('Invalid JSON document'); };
  function whitespace() { while (/[\x20\t\r\n]/.test(source[offset] ?? '') && offset < source.length) offset++; }
  function string(): string {
    const start = offset++;
    while (offset < source.length) {
      const char = source[offset++];
      if (char === '\\') offset++;
      else if (char === '"') return JSON.parse(source.slice(start, offset)) as string;
    }
    return fail();
  }
  function value(depth: number): void {
    whitespace();
    const char = source[offset];
    if (char === '{' || char === '[') {
      if (depth >= 64) fail();
      offset++;
      whitespace();
      const close = char === '{' ? '}' : ']';
      const keys = new Set<string>();
      if (source[offset] !== close) {
        while (true) {
          if (char === '{') {
            whitespace();
            if (source[offset] !== '"') fail();
            const key = string();
            if (keys.has(key)) fail();
            keys.add(key);
            whitespace();
            if (source[offset++] !== ':') fail();
          }
          value(depth + 1);
          whitespace();
          if (source[offset] !== ',') break;
          offset++;
        }
      }
      if (source[offset++] !== close) fail();
    } else if (char === '"') string();
    else {
      const token = /^(?:true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)/.exec(source.slice(offset))?.[0];
      if (!token || (!['true', 'false', 'null'].includes(token) && !Number.isFinite(Number(token)))) fail();
      offset += token!.length;
    }
  }
  value(0);
  whitespace();
  if (offset !== source.length) fail();
  return JSON.parse(source);
}
