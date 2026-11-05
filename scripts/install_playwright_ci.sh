#!/usr/bin/env bash
set -euo pipefail

case "${1:-}" in
  chromium|firefox|webkit) ;;
  *) echo "Usage: install_playwright_ci.sh chromium|firefox|webkit" >&2; exit 2 ;;
esac

# Hosted Ubuntu's Azure mirror took 22 minutes to download 42 MB in run42095492218.
# Keep the Ubuntu repositories and signatures; change that mirror's transport/host.
if [[ "${RUNNER_OS:-}" == Linux && -f /etc/apt/apt-mirrors.txt ]]; then
  sudo sed -i \
    -e 's|http://azure.archive.ubuntu.com/ubuntu|https://archive.ubuntu.com/ubuntu|g' \
    -e 's|https://azure.archive.ubuntu.com/ubuntu|https://archive.ubuntu.com/ubuntu|g' \
    /etc/apt/apt-mirrors.txt
fi

exec npx playwright install --with-deps "$1"
