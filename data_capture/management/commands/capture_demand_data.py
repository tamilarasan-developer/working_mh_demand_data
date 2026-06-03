# data_capture/management/commands/capture_demand_data.py

import time
import os
import re
from datetime import datetime, timedelta

from pyvirtualdisplay import Display
from playwright_stealth import Stealth

from django.core.management.base import BaseCommand
from django.db import transaction
from django import db as django_db
from django.db import connection
from django.db.utils import OperationalError, DatabaseError

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from data_capture.models import DemandData


class Command(BaseCommand):
    """
    Django management command for:
    - Extracting Maharashtra demand data
    - Capturing screenshot
    - Saving data into database
    """

    help = "Capture demand data and save into database continuously."

    def handle(self, *args, **options):

        # ---------------- CONFIGURATION ---------------- #

        TARGET_URL = "https://vidyutpravah.in/state-data/maharashtra"

        WAIT_TIME_SECONDS = 300

        XPATH_CURRENT = '//*[@id="Maharastra_map"]/div[6]/span/span'
        
        XPATH_YESTERDAY = '//*[@id="Maharastra_map"]/div[4]/span/span'

        XPATH_TIME_BLOCK = '/html/body/table/tbody/tr[1]/td/table/tbody/tr[2]/td/table/tbody/tr/td[2]'

        SCREENSHOT_DIR = "screenshots"

        KEEP_DAYS = 2

        os.makedirs(SCREENSHOT_DIR, exist_ok=True)

        # ------------------------------------------------ #

        try:

            while True:

                start_time = time.monotonic()

                run_start_time = datetime.now()

                formatted_start_time = run_start_time.strftime("%Y-%m-%d %H:%M:%S")

                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n🚀 Starting capture process at {formatted_start_time}"
                    )
                )

                current_text = None
                yesterday_text = None
                parsed_time_block = None
                parsed_date_obj = None

                capture_status = "UnknownError"

                # =========================================================
                # BLOCK 1 : WEBSITE SCRAPING
                # =========================================================

                try:

                    with Display(visible=0, size=(1920, 1080)):
                        with sync_playwright() as p:
                            browser = p.chromium.launch(headless=False, args=['--no-sandbox'])

                            context = browser.new_context(
                                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                                ignore_https_errors=True,
                                viewport={"width": 1920, "height": 1080}
                            )
                            page = context.new_page()
                            Stealth().apply_stealth_sync(page)

                            # Block unnecessary resources to optimize load time
                            def handle_route(route):
                                if route.request.resource_type in ["image", "media", "font"]:
                                    route.abort()
                                else:
                                    route.continue_()

                            page.route("**/*", handle_route)

                            self.stdout.write(f"🌐 Opening website: {TARGET_URL}")

                            try:
                                page.goto(
                                    TARGET_URL,
                                    timeout=60000,
                                    wait_until="domcontentloaded"
                                )
                            except PlaywrightTimeoutError:
                                self.stdout.write(self.style.WARNING("⚠️ page.goto timed out, but proceeding anyway..."))

                            self.stdout.write(
                                "⏳ Waiting for data elements..."
                            )

                            page.wait_for_selector(
                                f'xpath={XPATH_CURRENT}',
                                state='visible',
                                timeout=30000
                            )

                            self.stdout.write(
                                self.style.SUCCESS(
                                    "✅ Elements loaded successfully"
                                )
                            )

                            # -----------------------------
                            # Extract values
                            # -----------------------------

                            current_text = page.locator(
                                f'xpath={XPATH_CURRENT}'
                            ).inner_text(timeout=10000)

                            yesterday_text = page.locator(
                                f'xpath={XPATH_YESTERDAY}'
                            ).inner_text(timeout=10000)

                            full_text = page.locator(
                                f'xpath={XPATH_TIME_BLOCK}'
                            ).inner_text(timeout=10000)

                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"✅ Current Demand : {current_text}"
                                )
                            )

                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"✅ Yesterday Demand : {yesterday_text}"
                                )
                            )

                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"✅ Full Text : {full_text}"
                                )
                            )

                            # -----------------------------
                            # Parse date and time block
                            # -----------------------------

                            try:

                                full_text = " ".join(full_text.split())

                                pattern = r"TIME BLOCK (\d{2}:\d{2} - \d{2}:\d{2}) DATED (\d{2} [A-Z]{3} \d{4})"

                                match = re.search(pattern, full_text)

                                if match:

                                    parsed_time_block = match.group(1)

                                    date_str = match.group(2)

                                    parsed_date_obj = datetime.strptime(
                                        date_str,
                                        "%d %b %Y"
                                    ).date()

                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f"✅ Parsed Time Block : {parsed_time_block}"
                                        )
                                    )

                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f"✅ Parsed Date : {parsed_date_obj}"
                                        )
                                    )

                                    capture_status = "DataCaptured"

                                else:

                                    self.stderr.write(
                                        self.style.ERROR(
                                            "❌ Failed to parse time block/date"
                                        )
                                    )

                                    capture_status = "ParsingFailed"

                            except Exception as e:

                                self.stderr.write(
                                    self.style.ERROR(
                                        f"❌ Parsing Error : {e}"
                                    )
                                )

                                capture_status = "ParsingFailed"

                            # =================================================
                            # SCREENSHOT SECTION
                            # =================================================

                            if capture_status == "DataCaptured":

                                try:

                                    screenshot_date = run_start_time.date()

                                    screenshot_filename = (
                                        f"vidyutpravah_{screenshot_date.strftime('%Y-%m-%d')}.png"
                                    )

                                    screenshot_path = os.path.join(
                                        SCREENSHOT_DIR,
                                        screenshot_filename
                                    )

                                    # Take screenshot
                                    page.screenshot(path=screenshot_path)

                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f"🖼️ Screenshot saved : {screenshot_path}"
                                        )
                                    )

                                    # Remove old screenshots
                                    keep_dates = set()

                                    for d in range(KEEP_DAYS):

                                        dt = (
                                            run_start_time.date()
                                            - timedelta(days=d)
                                        )

                                        keep_dates.add(
                                            dt.strftime('%Y-%m-%d')
                                        )

                                    allowed_filenames = {
                                        f"vidyutpravah_{d}.png"
                                        for d in keep_dates
                                    }

                                    for fname in os.listdir(SCREENSHOT_DIR):

                                        if not fname.startswith("vidyutpravah_"):
                                            continue

                                        if not fname.lower().endswith(".png"):
                                            continue

                                        if fname not in allowed_filenames:

                                            fpath = os.path.join(
                                                SCREENSHOT_DIR,
                                                fname
                                            )

                                            try:

                                                os.remove(fpath)

                                                self.stdout.write(
                                                    self.style.WARNING(
                                                        f"🗑️ Removed old screenshot : {fpath}"
                                                    )
                                                )

                                            except Exception as e:

                                                self.stderr.write(
                                                    self.style.ERROR(
                                                        f"❌ Failed removing old screenshot : {e}"
                                                    )
                                                )

                                except Exception as e:

                                    self.stderr.write(
                                        self.style.ERROR(
                                            f"❌ Screenshot Error : {e}"
                                        )
                                    )

                                browser.close()

                except PlaywrightTimeoutError:

                    self.stderr.write(
                        self.style.ERROR(
                            "❌ Website loading timeout"
                        )
                    )

                    capture_status = "TimeoutError"

                except Exception as e:

                    self.stderr.write(
                        self.style.ERROR(
                            f"❌ Scraping Error : {e}"
                        )
                    )

                    capture_status = "ScrapingFailed"

                # =========================================================
                # BLOCK 2 : DATABASE SAVE
                # =========================================================

                if capture_status == "DataCaptured":

                    saved = False

                    max_attempts = 4

                    attempt = 0

                    while attempt < max_attempts and not saved:

                        attempt += 1

                        try:

                            # Close old DB connections
                            django_db.close_old_connections()

                            # Ensure connection
                            if hasattr(connection, "ensure_connection"):
                                connection.ensure_connection()

                            # Save data
                            with transaction.atomic():

                                DemandData.objects.create(
                                    current_demand=current_text,
                                    yesterday_demand=yesterday_text,
                                    time_block=parsed_time_block,
                                    date=parsed_date_obj
                                )

                            self.stdout.write(
                                self.style.SUCCESS(
                                    "💾 Data saved successfully"
                                )
                            )

                            saved = True

                        except (OperationalError, DatabaseError) as db_err:

                            err_text = str(db_err)

                            self.stderr.write(
                                self.style.ERROR(
                                    f"❌ DB Error Attempt {attempt}/{max_attempts} : {err_text}"
                                )
                            )

                            try:
                                connection.close()
                            except Exception:
                                pass

                            if attempt >= max_attempts:

                                self.stderr.write(
                                    self.style.ERROR(
                                        "❌ Failed saving to DB"
                                    )
                                )

                                break

                            backoff = 2 ** attempt

                            self.stdout.write(
                                self.style.WARNING(
                                    f"⏳ Retrying in {backoff} seconds..."
                                )
                            )

                            time.sleep(backoff)

                        except Exception as e:

                            self.stderr.write(
                                self.style.ERROR(
                                    f"❌ Unexpected DB Error : {e}"
                                )
                            )

                            try:
                                connection.close()
                            except Exception:
                                pass

                            break

                # =========================================================
                # FINISH
                # =========================================================

                end_time = time.monotonic()

                duration = end_time - start_time

                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n⏱️ Process finished in {duration:.2f} seconds"
                    )
                )

                self.stdout.write(
                    self.style.HTTP_INFO(
                        "\n--- Waiting for next capture ---"
                    )
                )

                for i in range(WAIT_TIME_SECONDS, 0, -1):

                    minutes, seconds = divmod(i, 60)

                    print(
                        f"Next capture in: {minutes:02d}:{seconds:02d}   ",
                        end="\r"
                    )

                    time.sleep(1)

                print("\n")

        except KeyboardInterrupt:

            self.stdout.write(
                self.style.WARNING(
                    "\n🛑 Script stopped by user"
                )
            )



