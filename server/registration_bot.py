import time
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List
import pandas as pd
from playwright.sync_api import sync_playwright, BrowserContext, Page, Playwright
from config import TARGET_URL, HEADLESS, BROWSER_TIMEOUT_MS, MAX_RETRIES, RETRY_DELAY_SEC, SCREENSHOT_DIR, BASE_DIR
from logger import logger, print_success, print_failure, print_warning


def get_flexible_value(student: Dict[str, Any], possible_keys: List[str]) -> str:
    """Flexible, case-insensitive key lookup for external user uploaded Excel datasets."""
    student_clean = {}
    for k, v in student.items():
        if k is not None and v is not None and not pd.isna(v):
            clean_k = str(k).strip().lower()
            student_clean[clean_k] = str(v).strip()

    for key in possible_keys:
        lk = key.strip().lower()
        if lk in student_clean:
            return student_clean[lk]
    return ""


class RegistrationBot:
    """Automates form registration, login verification for existing accounts, and MCQ quiz solving."""

    def __init__(self, url: str = TARGET_URL, headless: bool = HEADLESS):
        self.url = url
        self.headless = headless
        self.playwright: Playwright = None
        self.context: BrowserContext = None
        self.page: Page = None
        self.user_data_dir = BASE_DIR / "browser_data"
        self.user_data_dir.mkdir(parents=True, exist_ok=True)

    def start(self):
        """Launches Google Chrome in full screen resolution with persistent stealth context."""
        logger.info(f"Starting browser session in full screen resolution (Headless: {self.headless})...")
        self.playwright = sync_playwright().start()

        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--start-maximized"
        ]

        try:
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                channel="chrome",
                headless=self.headless,
                args=launch_args,
                ignore_default_args=["--enable-automation"],
                viewport=None
            )
        except Exception:
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=self.headless,
                args=launch_args,
                ignore_default_args=["--enable-automation"],
                viewport=None
            )

        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        self.page.set_default_timeout(BROWSER_TIMEOUT_MS)

        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

    def stop(self):
        """Closes browser session."""
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser session closed.")

    def clear_session(self):
        """
        Clears site session storage and user session cookies while PRESERVING
        Cloudflare cf_clearance tokens so Turnstile auto-passes for all subsequent candidates!
        """
        try:
            if self.context:
                existing_cookies = self.context.cookies()
                # Retain Cloudflare clearance & bot management cookies
                cf_cookies = [c for c in existing_cookies if "cf" in c.get("name", "").lower()]
                self.context.clear_cookies()
                if cf_cookies:
                    self.context.add_cookies(cf_cookies)

            if self.page:
                self.page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
        except Exception as e:
            logger.debug(f"Clear session notice: {e}")

    def capture_error_screenshot(self, student_name: str, row_index: int) -> Path:
        """Captures a screenshot of the browser on registration error."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in student_name if c.isalnum() or c in (" ", "_")).rstrip()
        filename = f"error_row_{row_index}_{safe_name}_{timestamp}.png"
        path = SCREENSHOT_DIR / filename
        try:
            self.page.screenshot(path=str(path), full_page=True)
            logger.info(f"Captured error screenshot: {path}")
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
        return path

    def wait_for_cloudflare_and_form(self, timeout_sec: int = 45):
        """Monitors page until Cloudflare verification completes and form is visible."""
        start_time = time.time()
        form_found = False

        while (time.time() - start_time) < timeout_sec:
            if "my-account" in self.page.url.lower() or self.page.locator("a:has-text('Logout')").count() > 0:
                logger.info("Logging out previous student session...")
                self.clear_session()
                self.page.goto(self.url, wait_until="domcontentloaded")
                time.sleep(1)
                continue

            if self.page.locator("form").count() > 0:
                form_found = True
                break

            title = self.page.title().lower()
            content = self.page.content().lower()

            if "just a moment" in title or "verifying you are human" in content:
                logger.info("Cloudflare verification in progress... Waiting for page redirect...")
                time.sleep(2)
            else:
                time.sleep(1)

        if not form_found:
            raise Exception("Timed out waiting for Cloudflare verification or form to load.")

    def human_type(self, locator, text: str):
        """Types text into input with human keystroke timing."""
        locator.click()
        time.sleep(random.uniform(0.1, 0.2))
        locator.clear()
        time.sleep(random.uniform(0.1, 0.15))

        for char in str(text):
            locator.type(char, delay=random.uniform(25, 80))
        time.sleep(random.uniform(0.1, 0.2))

    def fill_form_field(self, selector_or_name: str, value: str, field_name: str):
        """Fills a single form field with human-like interaction."""
        locator = self.page.locator(
            f"input[name='{selector_or_name}'], textarea[name='{selector_or_name}'], input#{selector_or_name}, textarea#{selector_or_name}, select[name='{selector_or_name}']"
        )

        if locator.count() == 0:
            locator = self.page.get_by_label(field_name, exact=False)
            if locator.count() == 0:
                locator = self.page.get_by_placeholder(field_name, exact=False)

        loc = locator.first
        loc.wait_for(state="visible", timeout=BROWSER_TIMEOUT_MS)
        self.human_type(loc, str(value))

    def login_and_attempt_quiz(self, student: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Navigates to https://quiz.toitctc.com/login, enters username & password,
        verifies login success, and runs the MCQ quiz solver.
        """
        student_name = get_flexible_value(student, ["Name", "Student Name", "Full Name", "Candidate Name", "Student"])
        email_val = get_flexible_value(student, ["Guardian Email", "Email", "Email Address", "GuardianEmail"])
        pass_val = get_flexible_value(student, ["Password", "Pass", "Password123!"]) or "Password123!"

        logger.info(f"\n--- EXISTING ACCOUNT CHECK FOR {student_name} ({email_val}) ---")
        logger.info("Navigating to https://quiz.toitctc.com/login for verification...")

        try:
            self.clear_session()
            login_url = "https://quiz.toitctc.com/login"
            self.page.goto(login_url, wait_until="domcontentloaded")

            self.wait_for_cloudflare_and_form(timeout_sec=45)

            uname_input = self.page.locator("input[name='uname'], input#uname, input[placeholder*='Username'], input[placeholder*='Email']").first
            psw_input = self.page.locator("input[name='psw'], input#psw, input[placeholder*='Password']").first

            uname_input.wait_for(state="visible", timeout=15000)
            psw_input.wait_for(state="visible", timeout=15000)

            logger.info(f"Entering login credentials for {email_val}...")
            self.human_type(uname_input, email_val)
            time.sleep(0.3)
            self.human_type(psw_input, pass_val)
            time.sleep(0.5)

            # Submit Login
            login_btn = self.page.locator("button[type='submit']:has-text('Login'), button:has-text('Login'), input[type='submit'][value*='Login']").first
            login_btn.click()
            self.page.wait_for_load_state("domcontentloaded")
            time.sleep(2.5)

            # VERIFY LOGIN SUCCESS
            login_err_locator = self.page.locator(".alert-danger, .error-msg, .woocommerce-error, :text('Invalid'), :text('incorrect')").first
            if login_err_locator.is_visible(timeout=2000):
                err_text = login_err_locator.inner_text().strip()
                logger.warning(f"Login failed for {email_val}: {err_text}")
                self.clear_session()
                return False, f"Login Error: Account not registered or invalid credentials ({err_text})"

            # Execute MCQ Quiz Solver
            from config import ENABLE_QUIZ_SOLVER
            if ENABLE_QUIZ_SOLVER:
                from quiz_solver import QuizSolver
                quiz_solver = QuizSolver(self.page)
                quiz_ok, quiz_msg = quiz_solver.solve_quiz()
                logger.info(f"Quiz status for {student_name} (Logged In): {quiz_msg}")
                if not quiz_ok:
                    self.clear_session()
                    return False, f"Login Quiz Error: {quiz_msg}"

            self.clear_session()
            print_success(f"Existing Account Logged In & Quiz Completed for {student_name}")
            return True, "Success (Logged In & Quiz Completed)"

        except Exception as e:
            logger.error(f"Login & quiz attempt failed for {student_name}: {e}")
            self.clear_session()
            return False, f"Login Error: {e}"

    def process_student_registration(self, student: Dict[str, Any], current: int, total: int) -> Tuple[bool, str]:
        """
        Full Lifecycle per Student:
        Supports dynamic column name matching for files uploaded by external users!
        """
        student_name = get_flexible_value(student, ["Name", "Student Name", "Full Name", "Candidate Name", "Student"]) or f"Student #{current}"
        row_idx = student.get("_row_index", current)

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                self.clear_session()

                self.page.goto(self.url, wait_until="domcontentloaded")

                self.wait_for_cloudflare_and_form(timeout_sec=45)

                field_mapping = {
                    "student": ("Name", get_flexible_value(student, ["Name", "Student Name", "Full Name", "Candidate Name", "Student"])),
                    "class": ("Class", get_flexible_value(student, ["Class", "Grade", "Standard", "Class Name"])),
                    "school": ("School", get_flexible_value(student, ["School", "School Name", "Institution"])),
                    "parent": ("Parent's Name", get_flexible_value(student, ["Parent's Name", "Parent Name", "Father Name", "Guardian Name", "Parent"])),
                    "phone": ("Phone Number", get_flexible_value(student, ["Phone Number", "Phone", "Mobile", "Mobile Number", "Contact"])),
                    "address": ("Home Address", get_flexible_value(student, ["Home Address", "Address", "Street Address"])),
                    "pincode": ("Pin Code", get_flexible_value(student, ["Pin Code", "Pin", "Pincode", "Zip", "Zip Code"])),
                    "city": ("City", get_flexible_value(student, ["City", "Town"])),
                    "state": ("State", get_flexible_value(student, ["State", "Province"])),
                    "email": ("Guardian Email", get_flexible_value(student, ["Guardian Email", "Email", "Email Address", "GuardianEmail"])),
                    "pass": ("Password", get_flexible_value(student, ["Password", "Pass"]) or "Password123!"),
                    "repass": ("Confirm Password", get_flexible_value(student, ["Confirm Password", "ConfirmPass", "Password"]) or "Password123!")
                }

                for field_key, (field_name, val) in field_mapping.items():
                    self.fill_form_field(field_key, val, field_name)
                    time.sleep(random.uniform(0.1, 0.3))

                time.sleep(random.uniform(0.4, 0.8))

                submit_button = self.page.locator("button[type='submit'], input[type='submit'], button:has-text('Join Now'), button:has-text('Register')").first
                submit_button.hover()
                time.sleep(random.uniform(0.1, 0.25))
                submit_button.click()

                success_locator = self.page.locator(".alert-success, #success-message, :text('Successful'), :text('Registration Completed'), :text('Begin Quiz Now'), a:has-text('Logout')").first
                error_alert_locator = self.page.locator(".alert-danger, #error-message, .error-msg, .woocommerce-error, :text('already registered'), :text('already exist')").first

                start_time = time.time()
                success_found = False
                failure_reason = ""

                while (time.time() - start_time) * 1000 < BROWSER_TIMEOUT_MS:
                    curr_url = self.page.url.lower()
                    if "my-account" in curr_url or "quizstart" in curr_url or success_locator.is_visible():
                        success_found = True
                        break
                    if error_alert_locator.is_visible():
                        failure_reason = error_alert_locator.inner_text().strip()
                        break
                    time.sleep(0.3)

                # BRANCH A: NEW REGISTRATION SUCCESS -> SOLVE QUIZ
                if success_found or "my-account" in self.page.url.lower() or "quizstart" in self.page.url.lower():
                    print_success("Registration Successful")

                    from config import ENABLE_QUIZ_SOLVER
                    if ENABLE_QUIZ_SOLVER:
                        from quiz_solver import QuizSolver
                        quiz_solver = QuizSolver(self.page)
                        quiz_ok, quiz_msg = quiz_solver.solve_quiz()
                        logger.info(f"Quiz status for {student_name}: {quiz_msg}")
                        if not quiz_ok:
                            self.clear_session()
                            return False, f"Quiz Error: {quiz_msg}"

                    self.clear_session()
                    time.sleep(random.uniform(0.8, 1.5))
                    return True, "Success"

                # BRANCH B: ALREADY REGISTERED -> NAVIGATE TO LOGIN & SOLVE QUIZ
                if failure_reason:
                    lower_err = failure_reason.lower()
                    if "already registered" in lower_err or "already exist" in lower_err:
                        print_warning(f"Email already registered for {student_name}. Switching to Login & Quiz Attempt...")
                        return self.login_and_attempt_quiz(student)

                    raise Exception(f"Form submission returned error: {failure_reason}")

                if "success" in self.page.url.lower() or "thank" in self.page.url.lower():
                    print_success("Registration Successful (URL redirection confirmed)")
                    self.clear_session()
                    time.sleep(random.uniform(0.8, 1.5))
                    return True, "Success"

                raise Exception("Timed out waiting for registration success confirmation.")

            except Exception as e:
                err_msg = str(e)

                if "already registered" in err_msg.lower() or "already exist" in err_msg.lower():
                    print_warning(f"Email already registered for {student_name}. Switching to Login & Quiz Attempt...")
                    return self.login_and_attempt_quiz(student)

                logger.warning(f"Registration attempt {attempt}/{MAX_RETRIES} failed for row {row_idx} ({student_name}): {err_msg}")
                self.capture_error_screenshot(student_name, row_idx)
                self.clear_session()

                if attempt < MAX_RETRIES:
                    print_warning(f"Registration Failed (Attempt {attempt}/{MAX_RETRIES}). Retrying in {RETRY_DELAY_SEC}s...")
                    time.sleep(RETRY_DELAY_SEC)
                else:
                    print_failure(f"Registration Failed after {MAX_RETRIES} attempts: {err_msg}")
                    return False, err_msg

        return False, "Max retries exceeded"
