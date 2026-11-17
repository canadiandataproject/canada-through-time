import asyncio, sys
from playwright.async_api import async_playwright
import os
SIZES={'desktop':(1440,900,1),'phone':(390,844,2),'short':(1080,1920,1),'desktopvox':(1440,900,1),'phonevox':(390,844,2)}
async def main(keys):
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome')
        for k in keys:
            for kind,(w,h,dpr) in SIZES.items():
                if not os.path.exists(f'/tmp/sf/out/{k}_{kind}.html'): continue
                pg=await b.new_page(viewport={'width':w,'height':h},device_scale_factor=dpr)
                await pg.goto(f'file:///tmp/sf/out/{k}_{kind}.html'); await pg.wait_for_timeout(700)
                await pg.screenshot(path=f'/tmp/sf/out/{k}_{kind}.png'); await pg.close()
        await b.close()
asyncio.run(main(sys.argv[1:] or ['A','B','C']))
