from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        # try headed if headless fails, but we can't run headed without xvfb.
        # we will use headless but try to spoof a bit and ignore https.
        browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            ignore_https_errors=True,
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        # Block images and unnecessary requests to speed up
        def handle_route(route):
            if route.request.resource_type in ["image", "media", "font"]:
                route.abort()
            else:
                route.continue_()
        
        page.route("**/*", handle_route)
        
        try:
            print("Going to URL...")
            # We wait until 'commit' instead of 'domcontentloaded' to avoid timeout on slow assets
            page.goto("https://vidyutpravah.in/state-data/maharashtra", timeout=60000, wait_until="commit")
            print("Goto finished")
        except Exception as e:
            print(f"Error during goto: {e}")
        
        try:
            print("Waiting for selector...")
            page.wait_for_selector('//*[@id="Maharastra_map"]/div[6]/span/span', timeout=30000)
            current = page.locator('//*[@id="Maharastra_map"]/div[6]/span/span').inner_text()
            yesterday = page.locator('//*[@id="Maharastra_map"]/div[4]/span/span').inner_text()
            print("Current:", current)
            print("Yesterday:", yesterday)
            print("Success finding element!")
        except Exception as e:
            print(f"Selector Error: {e}")
            
        browser.close()

if __name__ == "__main__":
    test()
