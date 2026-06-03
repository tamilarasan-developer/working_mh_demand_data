from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            ignore_https_errors=True
        )
        
        try:
            print("Going to URL...")
            page.goto("https://vidyutpravah.in/state-data/maharashtra", timeout=20000)
            print("Loaded")
        except Exception as e:
            print(f"Error during goto: {e}")
        
        try:
            page.wait_for_selector('//*[@id="Maharastra_map"]/div[6]/span/span', timeout=10000)
            print("Current:", page.locator('//*[@id="Maharastra_map"]/div[6]/span/span').inner_text())
            print("Success finding element!")
        except Exception as e:
            print(f"Selector Error: {e}")
            
        browser.close()

if __name__ == "__main__":
    test()
