import time
import asyncio
import random
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List
import pandas as pd
from playwright.async_api import Page, BrowserContext
from config import TARGET_URL, BROWSER_TIMEOUT_MS, MAX_RETRIES, RETRY_DELAY_SEC, SCREENSHOT_DIR, BASE_DIR
from logger import logger, print_success, print_failure, print_warning, _global_state_ref
from quiz_solver import QuizSolver


async def send_live_screenshot(page: Page):
    """Captures a lightweight base64 JPEG screenshot and streams it live to the web dashboard UI."""
    try:
        if page and _global_state_ref:
            img_bytes = await page.screenshot(type="jpeg", quality=65)
            b64_str = base64.b64encode(img_bytes).decode("utf-8")
            _global_state_ref["live_screenshot"] = f"data:image/jpeg;base64,{b64_str}"
    except Exception:
        pass


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


async def capture_error_screenshot(page: Page, student_name: str, row_index: int) -> Path:
    """Captures a screenshot of the browser on registration error."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c for c in student_name if c.isalnum() or c in (" ", "_")).rstrip()
    filename = f"error_row_{row_index}_{safe_name}_{timestamp}.png"
    path = SCREENSHOT_DIR / filename
    try:
        if page:
            await page.screenshot(path=str(path), full_page=True)
            logger.info(f"Captured error screenshot: {path}")
    except Exception as e:
        logger.error(f"Failed to capture screenshot: {e}")
    return path


async def auto_click_cloudflare_turnstile(page: Page):
    """Detects Cloudflare Turnstile challenge iframe and clicks the verification checkbox automatically."""
    try:
        for frame in page.frames:
            if "challenges.cloudflare.com" in frame.url or "turnstile" in frame.url:
                checkbox = frame.locator("input[type='checkbox'], #challenge-stage, .mark, span.mark, .cb-lb").first
                if await checkbox.is_visible(timeout=1500):
                    logger.info("Found Cloudflare Turnstile challenge checkbox! Auto-clicking...")
                    await checkbox.click(force=True)
                    await send_live_screenshot(page)
                    await asyncio.sleep(1.5)
                    return True
    except Exception as e:
        logger.debug(f"Turnstile click notice: {e}")
    return False


async def wait_for_cloudflare_and_form(page: Page, url: str, timeout_sec: int = 45):
    """Monitors page until Cloudflare verification completes and form is visible."""
    start_time = time.time()
    form_found = False
    reload_attempted = False

    while (time.time() - start_time) < timeout_sec:
        await send_live_screenshot(page)
        curr_url = page.url.lower()
        logout_count = await page.locator("a:has-text('Logout')").count()
        if "my-account" in curr_url or logout_count > 0:
            await page.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(1)
            continue

        form_count = await page.locator("input[name='student'], input[name='email'], form input").count()
        title = (await page.title()).lower()

        if form_count > 0 and "just a moment" not in title:
            form_found = True
            break

        # Attempt Turnstile auto-click
        clicked = await auto_click_cloudflare_turnstile(page)

        # Smart reload fallback if stuck on Turnstile for > 12 seconds
        elapsed = time.time() - start_time
        if elapsed > 12 and not reload_attempted and ("just a moment" in title or form_count == 0):
            logger.info("Cloudflare challenge bypass delay detected. Refreshing page with stealth context...")
            reload_attempted = True
            await page.reload(wait_until="domcontentloaded")
            await asyncio.sleep(2)
            continue

        content = (await page.content()).lower()
        if "just a moment" in title or "verifying you are human" in content or "cf-turnstile" in content:
            logger.info("Cloudflare verification in progress... Waiting for page redirect...")
            await asyncio.sleep(2)
        else:
            await asyncio.sleep(1)

    if not form_found:
        if (await page.locator("input").count()) > 0:
            return
        raise Exception("Timed out waiting for Cloudflare verification or form to load.")


async def human_type(page: Page, locator, text: str):
    """Types text into input with human keystroke timing."""
    await locator.click()
    await asyncio.sleep(random.uniform(0.1, 0.2))
    await locator.clear()
    await asyncio.sleep(random.uniform(0.1, 0.15))

    for char in str(text):
        await locator.type(char, delay=random.uniform(25, 80))
    await asyncio.sleep(random.uniform(0.1, 0.2))


async def fill_form_field(page: Page, selector_or_name: str, value: str, field_name: str):
    """Fills a single form field with human-like interaction."""
    locator = page.locator(
        f"input[name='{selector_or_name}'], textarea[name='{selector_or_name}'], input#{selector_or_name}, textarea#{selector_or_name}, select[name='{selector_or_name}']"
    )

    if (await locator.count()) == 0:
        locator = page.get_by_label(field_name, exact=False)
        if (await locator.count()) == 0:
            locator = page.get_by_placeholder(field_name, exact=False)

    loc = locator.first
    await loc.wait_for(state="visible", timeout=BROWSER_TIMEOUT_MS)
    await human_type(page, loc, str(value))


async def login_and_attempt_quiz(page: Page, student: Dict[str, Any], url: str) -> Tuple[bool, str]:
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
        login_url = "https://quiz.toitctc.com/login"
        await page.goto(login_url, wait_until="domcontentloaded")
        await send_live_screenshot(page)

        await wait_for_cloudflare_and_form(page, url, timeout_sec=45)

        uname_input = page.locator("input[name='uname'], input#uname, input[placeholder*='Username'], input[placeholder*='Email']").first
        psw_input = page.locator("input[name='psw'], input#psw, input[placeholder*='Password']").first

        await uname_input.wait_for(state="visible", timeout=15000)
        await psw_input.wait_for(state="visible", timeout=15000)

        logger.info(f"Entering login credentials for {email_val}...")
        await human_type(page, uname_input, email_val)
        await asyncio.sleep(0.3)
        await human_type(page, psw_input, pass_val)
        await send_live_screenshot(page)
        await asyncio.sleep(0.5)

        # Submit Login
        login_btn = page.locator("button[type='submit']:has-text('Login'), button:has-text('Login'), input[type='submit'][value*='Login']").first
        await login_btn.click()
        await page.wait_for_load_state("domcontentloaded")
        await send_live_screenshot(page)
        await asyncio.sleep(2.5)

        # VERIFY LOGIN SUCCESS
        login_err_locator = page.locator(".alert-danger, .error-msg, .woocommerce-error, :text('Invalid'), :text('incorrect')").first
        if await login_err_locator.is_visible(timeout=2000):
            err_text = (await login_err_locator.inner_text()).strip()
            logger.warning(f"Login failed for {email_val}: {err_text}")
            return False, f"Login Error: Account not registered or invalid credentials ({err_text})"

        # Execute MCQ Quiz Solver
        from config import ENABLE_QUIZ_SOLVER
        if ENABLE_QUIZ_SOLVER:
            quiz_solver = QuizSolver(page)
            quiz_ok, quiz_msg = await quiz_solver.solve_quiz()
            logger.info(f"Quiz status for {student_name} (Logged In): {quiz_msg}")
            if not quiz_ok:
                return False, f"Login Quiz Error: {quiz_msg}"

        print_success(f"Existing Account Logged In & Quiz Completed for {student_name}")
        return True, "Success (Logged In & Quiz Completed)"

    except Exception as e:
        logger.error(f"Login & quiz attempt failed for {student_name}: {e}")
        return False, f"Login Error: {e}"


async def process_student_registration(page: Page, student: Dict[str, Any], current: int, total: int, url: str) -> Tuple[bool, str]:
    """
    Full Lifecycle per Student using native async_playwright.
    """
    student_name = get_flexible_value(student, ["Name", "Student Name", "Full Name", "Candidate Name", "Student"]) or f"Student #{current}"
    row_idx = student.get("_row_index", current)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await page.goto(url, wait_until="domcontentloaded")
            await send_live_screenshot(page)

            await wait_for_cloudflare_and_form(page, url, timeout_sec=45)

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
                await fill_form_field(page, field_key, val, field_name)
                await asyncio.sleep(random.uniform(0.1, 0.2))

            await send_live_screenshot(page)
            await asyncio.sleep(random.uniform(0.3, 0.6))

            submit_button = page.locator("button[type='submit'], input[type='submit'], button:has-text('Join Now'), button:has-text('Register')").first
            await submit_button.hover()
            await asyncio.sleep(random.uniform(0.1, 0.25))
            await submit_button.click()
            await send_live_screenshot(page)

            success_locator = page.locator(".alert-success, #success-message, :text('Successful'), :text('Registration Completed'), :text('Begin Quiz Now'), a:has-text('Logout')").first
            error_alert_locator = page.locator(".alert-danger, #error-message, .error-msg, .woocommerce-error, :text('already registered'), :text('already exist')").first

            start_time = time.time()
            success_found = False
            failure_reason = ""

            while (time.time() - start_time) * 1000 < BROWSER_TIMEOUT_MS:
                curr_url = page.url.lower()
                if "my-account" in curr_url or "quizstart" in curr_url or (await success_locator.is_visible()):
                    success_found = True
                    break
                if await error_alert_locator.is_visible():
                    failure_reason = (await error_alert_locator.inner_text()).strip()
                    break
                await asyncio.sleep(0.3)

            await send_live_screenshot(page)

            # BRANCH A: NEW REGISTRATION SUCCESS -> SOLVE QUIZ
            if success_found or "my-account" in page.url.lower() or "quizstart" in page.url.lower():
                print_success("Registration Successful")

                from config import ENABLE_QUIZ_SOLVER
                if ENABLE_QUIZ_SOLVER:
                    quiz_solver = QuizSolver(page)
                    quiz_ok, quiz_msg = await quiz_solver.solve_quiz()
                    logger.info(f"Quiz status for {student_name}: {quiz_msg}")
                    if not quiz_ok:
                        return False, f"Quiz Error: {quiz_msg}"

                await asyncio.sleep(random.uniform(0.8, 1.5))
                return True, "Success"

            # BRANCH B: ALREADY REGISTERED -> NAVIGATE TO LOGIN & SOLVE QUIZ
            if failure_reason:
                lower_err = failure_reason.lower()
                if "already registered" in lower_err or "already exist" in lower_err:
                    print_warning(f"Email already registered for {student_name}. Switching to Login & Quiz Attempt...")
                    return await login_and_attempt_quiz(page, student, url)

                raise Exception(f"Form submission returned error: {failure_reason}")

            if "success" in page.url.lower() or "thank" in page.url.lower():
                print_success("Registration Successful (URL redirection confirmed)")
                await asyncio.sleep(random.uniform(0.8, 1.5))
                return True, "Success"

            raise Exception("Timed out waiting for registration success confirmation.")

        except Exception as e:
            err_msg = str(e)

            if "already registered" in err_msg.lower() or "already exist" in err_msg.lower():
                print_warning(f"Email already registered for {student_name}. Switching to Login & Quiz Attempt...")
                return await login_and_attempt_quiz(page, student, url)

            logger.warning(f"Registration attempt {attempt}/{MAX_RETRIES} failed for row {row_idx} ({student_name}): {err_msg}")
            await capture_error_screenshot(page, student_name, row_idx)

            if attempt < MAX_RETRIES:
                print_warning(f"Registration Failed (Attempt {attempt}/{MAX_RETRIES}). Retrying in {RETRY_DELAY_SEC}s...")
                await asyncio.sleep(RETRY_DELAY_SEC)
            else:
                print_failure(f"Registration Failed after {MAX_RETRIES} attempts: {err_msg}")
                return False, err_msg

    return False, "Max retries exceeded"
