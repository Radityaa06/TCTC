import time
import random
from typing import Tuple
from playwright.sync_api import Page
from config import QUIZ_ANSWER_STRATEGY, MIN_THINK_TIME_SEC, MAX_THINK_TIME_SEC, QUIZ_TIMEOUT_SEC
from logger import logger, print_success, print_failure, print_warning


class QuizSolver:
    """Automates dynamic MCQ quiz completion for a logged-in student (1 to 5 questions)."""

    def __init__(self, page: Page):
        self.page = page

    def start_quiz_session(self) -> bool:
        """Navigates to or clicks the 'Begin Quiz Now' / 'Start Quiz' button."""
        try:
            logger.info("Checking for 'Begin Quiz Now' button or direct quiz screen...")
            time.sleep(1.5)

            start_btn = self.page.locator(
                "a:has-text('Begin Quiz Now'), button:has-text('Begin Quiz Now'), a:has-text('Start Quiz'), button:has-text('Start Quiz'), a[href*='quizstart'], .start-quiz-btn"
            ).first

            if start_btn.is_visible(timeout=8000):
                txt = start_btn.inner_text().strip()
                logger.info(f"Found Quiz Start button: '{txt}'. Clicking...")
                time.sleep(random.uniform(0.8, 1.5))
                start_btn.click()
                self.page.wait_for_load_state("domcontentloaded")
                time.sleep(1.5)
                return True
            else:
                logger.info("Directly on quiz page or start button not required.")
                return True
        except Exception as e:
            logger.warning(f"Notice looking for quiz start button ({e}). Checking for active question...")
            return True

    def select_mcq_option(self) -> bool:
        """
        Locates MCQ options (radio buttons / labels / option boxes) for the active question
        and selects an option according to QUIZ_ANSWER_STRATEGY.
        """
        radio_locators = self.page.locator("input[type='radio']")

        if radio_locators.count() > 0:
            count = radio_locators.count()
            logger.info(f"Found {count} MCQ radio options for current question.")

            if QUIZ_ANSWER_STRATEGY == "first_option":
                target_idx = 0
            elif QUIZ_ANSWER_STRATEGY == "fixed_index":
                target_idx = min(1, count - 1)
            else:  # Default: random
                target_idx = random.randint(0, count - 1)

            chosen_radio = radio_locators.nth(target_idx)

            time.sleep(random.uniform(MIN_THINK_TIME_SEC, MAX_THINK_TIME_SEC))
            try:
                chosen_radio.click(force=True)
            except Exception:
                chosen_radio.evaluate("el => el.click()")

            return True

        custom_options = self.page.locator(".quiz-option, .answer-option, label.option, ul.options li, div.option")
        if custom_options.count() > 0:
            count = custom_options.count()
            logger.info(f"Found {count} custom MCQ option containers.")
            target_idx = random.randint(0, count - 1) if QUIZ_ANSWER_STRATEGY == "random" else 0
            time.sleep(random.uniform(MIN_THINK_TIME_SEC, MAX_THINK_TIME_SEC))
            custom_options.nth(target_idx).click()
            return True

        logger.warning("No radio buttons or MCQ option containers found for this question step.")
        return False

    def submit_question_or_quiz(self) -> Tuple[bool, bool]:
        """
        Clicks the Next Question / Submit Answer / Submit Quiz button.
        Returns: (success_status, is_quiz_finished)
        """
        submit_btn = self.page.locator(
            "button:has-text('Submit Answer'), input[value*='Submit'], button:has-text('Next Question'), button:has-text('Submit Question'), button:has-text('Submit Quiz'), button:has-text('Finish Quiz'), button:has-text('Submit'), button[type='submit'], input[type='submit']"
        ).first

        if submit_btn.is_visible(timeout=4000):
            txt = submit_btn.inner_text().strip() if submit_btn.count() > 0 else "Submit"
            logger.info(f"Clicking quiz button: '{txt}'...")
            time.sleep(random.uniform(0.5, 1.2))
            submit_btn.click()
            self.page.wait_for_load_state("domcontentloaded")
            time.sleep(1.2)

        finish_indicators = self.page.locator(
            ":text('Quiz Completed'), :text('Quiz Finished'), :text('Thank You'), :text('Score'), .quiz-result, .completion-msg, :text('Submitted Successfully')"
        )
        if finish_indicators.count() > 0 and finish_indicators.first.is_visible():
            return True, True

        return True, False

    def solve_quiz(self) -> Tuple[bool, str]:
        """
        Main entry point for solving dynamic 1 to 5 MCQ questions.
        Enforces strict verification that questions were actually found and answered.
        """
        logger.info("\n--- STARTING AUTOMATED MCQ QUIZ SOLVER ---")
        try:
            if not self.start_quiz_session():
                return False, "Failed to start quiz session"

            max_questions = 10
            question_count = 0

            for q_idx in range(1, max_questions + 1):
                logger.info(f"Processing Quiz Question #{q_idx}...")

                finish_check = self.page.locator(":text('Quiz Completed'), :text('Quiz Finished'), :text('Score'), .quiz-result, :text('Thank You')")
                if finish_check.count() > 0 and finish_check.first.is_visible():
                    if question_count > 0:
                        logger.info("Quiz completion screen detected!")
                        print_success(f"Quiz Completed Successfully ({question_count} questions solved)!")
                        return True, f"Completed ({question_count} questions)"

                option_selected = self.select_mcq_option()

                if not option_selected and q_idx == 1:
                    logger.warning("No MCQ options found on Question #1 page.")
                    return False, "Quiz Error: No quiz options found on page"

                success, is_finished = self.submit_question_or_quiz()
                if option_selected:
                    question_count += 1

                if is_finished:
                    logger.info(f"Quiz finished! Total questions answered: {question_count}.")
                    print_success(f"Quiz Completed Successfully ({question_count} questions)!")
                    return True, f"Completed ({question_count} questions)"

                if not option_selected and q_idx > 1:
                    logger.info(f"No further questions detected after question #{q_idx-1}.")
                    print_success(f"Quiz Completed ({question_count} questions answered)!")
                    return True, f"Completed ({question_count} questions)"

            if question_count > 0:
                return True, f"Completed ({question_count} questions)"
            else:
                return False, "Quiz Error: 0 questions were answered"

        except Exception as e:
            logger.error(f"Error during quiz auto-solving: {e}")
            return False, f"Quiz Error: {e}"
