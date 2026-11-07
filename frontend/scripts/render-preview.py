from pathlib import Path
from playwright.sync_api import sync_playwright
import re
root=Path(__file__).resolve().parents[1]
css=(root/'src/styles.css').read_text()+'\n'+(root/'src/internal.css').read_text()
previews={
 'landing_desktop':('index.html',1440,900),
 'dashboard_desktop':('app.html',1440,900),
 'forecast_desktop':('app__forecast__example.html',1440,900),
 'catalog_desktop':('universities.html',1440,900),
 'competition_desktop':('app__competitions__mtuci-se.html',1440,900),
 'landing_mobile':('index.html',390,844),
 'dashboard_mobile':('app.html',390,844),
 'forecast_mobile':('app__forecast__example.html',390,844),
}
shots=root/'screenshots';shots.mkdir(exist_ok=True)
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-gpu'])
 for name,(filename,w,h) in previews.items():
  path=root/'preview'/filename
  text=path.read_text()
  text=re.sub(r'<link[^>]+rel="stylesheet"[^>]*>', '',text)
  text=text.replace('</head>','<style>'+css+'</style></head>')
  page=b.new_page(viewport={'width':w,'height':h},device_scale_factor=1)
  page.set_content(text,wait_until='load')
  page.evaluate('document.fonts.ready')
  out=shots/(name+'.png')
  page.screenshot(path=str(out),full_page=name.startswith('landing') or name.endswith('_mobile'))
  metrics=page.evaluate('''() => ({w:document.documentElement.scrollWidth,h:document.documentElement.scrollHeight, title:document.querySelector('h1')?.innerText, a:document.querySelectorAll('a').length})''')
  print(name,metrics,out.stat().st_size)
  page.close()
 b.close()
