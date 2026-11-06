# B19/T215: единый читаемый стиль frontend

По уточнению пользователя однострочные блоки разворачиваются в многострочный
код. Функциональные исправления в этот подход не входят: найденные ошибки
сначала подтверждаются и описываются в отдельном отчёте.

Prettier3.9.10 закреплён точной devDependency/lockfile. Настройки:
printWidth100, singleAttributePerLine, single quotes, LF. Команды из frontend:
`npm run format` и `npm run format:check`. Fixtures, font assets, lockfile,
dist и test-results исключены; форматируются только исходники/тестовый код
и собственные frontend configs/public JS. Исходные production JS/CSS hashes
зафиксированы до изменений для сравнения после сборки.

Проверки: установка по npm registry прошла; npm audit0 vulnerabilities.
Version и чтение config подтверждены. Общий format check относится к T218,
когда будут обработаны все области; текущий неформатированный код ещё не
объявляется соответствующим стилю. Git author/settings не изменялись.
