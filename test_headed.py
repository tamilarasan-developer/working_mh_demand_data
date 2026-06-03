from playwright.sync_api import sync_playwright
import os

def test():
    # Use xvfb-run to start headed
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--no-sandbox'])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            ignore_https_errors=True
        )
        page = context.new_page()
        
        try:
            print("Going to URL...")
            page.goto("https://vidyutpravah.in/state-data/maharashtra", timeout=30000, wait_until="domcontentloaded")
            print("Goto finished")
        except Exception as e:
            print(f"Error during goto: {e}")
            
        try:
            page.wait_for_selector('//*[@id="Maharastra_map"]/div[6]/span/span', timeout=15000)
            print("Current:", page.locator('//*[@id="Maharastra_map"]/div[6]/span/span').inner_text())
            print("Success finding element!")
        except Exception as e:
            print(f"Selector Error: {e}")
            
        browser.close()

if __name__ == "__main__":
    test()
