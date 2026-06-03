from playwright.sync_api import sync_playwright
from pyvirtualdisplay import Display
import os

def test():
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--no-sandbox'])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            ignore_https_errors=True,
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        # Block unnecessary resources
        def handle_route(route):
            if route.request.resource_type in ["image", "media", "font"]:
                route.abort()
            else:
                route.continue_()
        
        page.route("**/*", handle_route)
        
        try:
            print("Going to URL...")
            page.goto("https://vidyutpravah.in/state-data/maharashtra", timeout=30000)
            print("Goto finished")
        except Exception as e:
            print(f"Error during goto: {e}")
            
        try:
            page.wait_for_selector('//*[@id="Maharastra_map"]/div[6]/span/span', timeout=15000)
            print("Current:", page.locator('//*[@id="Maharastra_map"]/div[6]/span/span').inner_text())
            page.screenshot(path="test_screenshot.png")
            print("Success finding element and screenshot!")
        except Exception as e:
            print(f"Selector Error: {e}")
            
        browser.close()
    
    display.stop()

if __name__ == "__main__":
    test()
