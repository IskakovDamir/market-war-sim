"""Screenshot every .html in a folder to a .png next to it (1440 wide, full page), e.g. the out/sim1 team pages.
usage: python3 shots.py <dir>    (Playwright; CHROME_PATH picks a browser, default is Playwright's Chromium)"""
import asyncio, sys, glob, os
from playwright.async_api import async_playwright
async def m(d):
    async with async_playwright() as p:
        chrome = os.environ.get('CHROME_PATH') or ('/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
        b = await p.chromium.launch(executable_path=chrome) if chrome else await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 1440, 'height': 900}, device_scale_factor=1.5)
        for f in sorted(glob.glob(d + '/*.html')):
            await pg.goto('file://' + os.path.abspath(f)); await pg.wait_for_timeout(600)
            await pg.screenshot(path=f[:-5] + '.png', full_page=True); print('png', f[:-5] + '.png')
        await b.close()
if __name__ == '__main__':
    asyncio.run(m(sys.argv[1]))
