from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Block unnecessary resources
        page.route("**/*", lambda route: route.abort() 
                   if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
                   else route.continue_())
        
        try:
            print("Going to URL...")
            page.goto("https://vidyutpravah.in/state-data/maharashtra", timeout=60000, wait_until="domcontentloaded")
            print("Loaded")
        except Exception as e:
            print(f"Error during goto: {e}")
        
        try:
            page.wait_for_selector('//*[@id="Maharastra_map"]/div[6]/span/span', timeout=30000)
            print(page.locator('//*[@id="Maharastra_map"]/div[6]/span/span').inner_text())
            print("Success finding element!")
        except Exception as e:
            print(f"Selector Error: {e}")
        browser.close()

if __name__ == "__main__":
    test()
