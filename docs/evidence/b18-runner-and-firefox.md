# B18/T212: Firefox Tab и установка браузеров

Локальная диагностика после Tab из поля «Вуз»:
Firefox activeElement=DIV.catalog-results, Chromium=BUTTON.catalog-option.
Firefox включает scroll container в последовательную навигацию по умолчанию;
его дополнительная остановка не нужна между полем и уже доступными кнопками.
На контейнере явно задан tabIndex=-1. Все варианты/ссылки остаются доступны,
существующие ArrowUp/Down/Escape/Tab assertions сохранены. Справка о фокусе
scroll containers: [MDN overflow](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/overflow#accessibility).

После исправления тот же probe даёт BUTTON.catalog-option в обоих браузерах.
Из frontend выполнен production build и
`npx playwright test tests/e2e/keyboard.spec.ts tests/e2e/catalog.spec.ts tests/e2e/national-catalog.spec.ts --project=firefox --project=chromium --project=mobile-chromium --reporter=line`:
**27passed/0skipped/0failed,54.0s**, env E2E_API=1,E2E_SERVER=external,
E2E_BASE_URL=http://127.0.0.1:5280, synthetic API8029. Это включает обе
ранее упавшие Firefox ширины,50→100пагинацию и сохранение20го направления.

CI использует явно ubuntu-24.04 вместо плавающего ubuntu-latest. Перед
прежней командой `npx playwright install --with-deps` новый shell helper
заменяет только Azure Ubuntu mirror в /etc/apt/apt-mirrors.txt на официальный
HTTPS archive.ubuntu.com. Репозитории, подписи и версии пакетов сохраняются.
Лимит установки5минут оставляет время для диагностического отчёта; общие
job limits15/25/20минут не повышались. Это исправление известного сетевого
блокера из исходного run; фактическая загрузка на hosted runner — проверка T214.

`bash -n scripts/install_playwright_ci.sh` и YAML parsing проходят; подтверждены
три задания/четыре browser matrix entries. Script в Git закреплён LF.
При ошибке установки/теста workflow продолжает возвращать failure, никаких
continue-on-error или новых test.skip не добавлено. Прежний demo/данные
не менялись, национальное покрытие не выросло.
