# B19/T218: тесты, формат и проверки

56TypeScript test files приведены к тому же многострочному стилю. Test cases,
assertions и skip guards не менялись. Команда format:check закреплена также
в основном CI задании, сразу после npm ci. Runtime dependencies прежние.

Фактические проверки текущего кода из frontend:

- `npm run format:check`:passed для исходников, тестов, config/publicJS.
- `npm test`:116passed/22files.
- `npm run build`:exit0.
- Chromium на изолированном compiled preview5281/API8031:
  79passed/36scopedskips/0failed,2.1min. Требующие отдельного archive fixture
  или Nginx cases не выдаются за passed; реальные абитуриенты не искались.
- Semantic AST сравнение с5440410:100TS/TSX files,0mismatches после
  нормализации форматирования/JSX text; ни assertions, ни control flow не менялись.
- CSS bundle SHA256 совпадает с исходной сборкой. JS bundles не объявляются
  побайтово идентичными: многострочный JSX имеет другое представление children.

Метрики и ограничения: [b19-format-verification.json](b19-format-verification.json).
Зелёные старые и текущие тесты не опровергают найденные аудитом дефекты:
их конкретные конкурентные/error/boundary сценарии отсутствуют в регрессии.
Дефекты остаются для отдельного исправления по запросу пользователя.
