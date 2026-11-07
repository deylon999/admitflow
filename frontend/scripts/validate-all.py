from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright
import re, json, sys

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / 'preview'
CSS = (ROOT / 'src/styles.css').read_text() + '\n' + (ROOT / 'src/internal.css').read_text()
HTML = sorted(PAGES.glob('*.html'))
HTML = [f for f in HTML if f.name != 'all-pages.html']
OUT = ROOT/'screenshots'
(OUT/'desktop').mkdir(parents=True,exist_ok=True)
(OUT/'mobile').mkdir(parents=True,exist_ok=True)

results=[]
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-gpu'])
    for width,kind in [(1440,'desktop'),(390,'mobile')]:
        page=browser.new_page(viewport={'width':width,'height':900 if width == 1440 else 844},device_scale_factor=1)
        for p in HTML:
            raw=p.read_text()
            raw=re.sub(r'<link[^>]+rel="stylesheet"[^>]*>', '',raw)
            raw=raw.replace('</head>', '<style>'+CSS+'</style></head>')
            page.set_content(raw,wait_until='load')
            page.evaluate('document.fonts.ready')
            stats=page.evaluate('''() => {
              const w=document.documentElement.clientWidth;
              const offenders=[...document.querySelectorAll('body *')].filter(el => {
                const r=el.getBoundingClientRect();
                return r.right > w+3 && r.width > 0 && getComputedStyle(el).position !== 'fixed';
              }).slice(0,4).map(el=>({tag:el.tagName,className:String(el.className).slice(0,60),name:(el.textContent||'').slice(0,35)}));
              return {title:document.querySelector('h1')?.innerText?.slice(0,70),documentWidth:document.documentElement.scrollWidth, clientWidth:w, offenders};
            }''')
            name=p.stem.replace('__','-')
            file=OUT/kind/(name+'.png')
            page.screenshot(path=str(file),full_page=False)
            results.append({'route':p.name,'view':kind,'stats':stats,'image':str(file.relative_to(ROOT))})
        page.close()
    browser.close()

(OUT/'qa-report.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
errors=[r for r in results if r['stats']['documentWidth']>r['stats']['clientWidth']+3]
print('Checked:',len(results),'screens; pages:',len(HTML))
print('Horizontal overflow:',len(errors))
for entry in errors[:25]:print(entry['view'],entry['route'],entry['stats']['documentWidth'],entry['stats']['offenders'])

def make_sheet(kind):
    originals=sorted((OUT/kind).glob('*.png'))
    if not originals:return
    width=370 if kind=='desktop' else 200
    height=270 if kind=='desktop' else 440
    cols=3 if kind=='desktop' else 5
    rows=(len(originals)+cols-1)//cols
    sheet=Image.new('RGB',(cols*width,rows*height),(245,247,251))
    draw=ImageDraw.Draw(sheet)
    for i,p in enumerate(originals):
        im=Image.open(p).convert('RGB')
        im.thumbnail((width-18,height-47))
        x=(i%cols)*width+9
        y=(i//cols)*height+13
        sheet.paste(im,(x,y))
        draw.text((x,y+height-38),p.stem[:39],fill=(15,20,39))
    sheet.save(OUT/('all-'+kind+'-screens.png'),optimize=True)
make_sheet('desktop');make_sheet('mobile')
if errors:sys.exit(1)
