import json, os
from playwright.sync_api import sync_playwright

pages = json.load(open('shots_pages.json', encoding='utf-8'))
os.makedirs('reports/astrowind_previews', exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch()
    for item in pages:
        for theme in ['light', 'dark']:
            for w in [1440, 390]:
                page = browser.new_page(viewport={'width': w, 'height': 900})
                try:
                    page.goto('http://localhost:8080' + item['path'], wait_until='load', timeout=30000)
                    page.wait_for_timeout(800)
                    if theme == 'dark':
                        page.evaluate("document.documentElement.classList.add('dark')")
                        page.wait_for_timeout(400)
                    name = item['name'] + '_' + theme + '_' + str(w) + '.png'
                    page.screenshot(path='reports/astrowind_previews/' + name, full_page=True)
                    print('shot:', name)
                except Exception as e:
                    print('FAIL:', item['name'], e)
                finally:
                    page.close()
    browser.close()
print('DONE')
