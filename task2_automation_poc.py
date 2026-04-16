#!/usr/bin/env python3
"""
Task 2: Automation Proof of Concept
Platform: Character.AI (https://character.ai)
Approach: Playwright browser automation

This PoC demonstrates automated interaction with an AI companion character
on Character.AI by sending a list of messages and capturing responses.

Approach:
- Uses Playwright to automate a Chromium browser
- Navigates to a Character.AI character chat page
- Sends predefined messages sequentially
- Waits for and captures AI responses
- Saves conversation to JSON and CSV

Why this approach:
- Character.AI is web-accessible, making browser automation viable
- Playwright is robust, supports modern SPAs, and handles dynamic content well
- No API reverse-engineering needed (more maintainable)
- Easily extensible to other web-based platforms (Replika, Chai, etc.)

Limitations:
- Requires a valid Character.AI account (login needed)
- Rate-limited by Character.AI's response generation speed
- UI changes may break selectors (mitigated by using data-testid and role selectors)
- Cannot bypass CAPTCHA if triggered

Usage:
    python3 task2_automation_poc.py [--character-url URL] [--headless]

The script will:
1. Open Character.AI in a browser
2. Pause for manual login (first run only; session is saved)
3. Navigate to the specified character
4. Send each message and capture the response
5. Save results to conversation_results.json and conversation_results.csv
"""

import argparse
import json
import csv
import time
import os
from datetime import datetime

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Default character URL (a popular public character)
DEFAULT_CHARACTER_URL = "https://character.ai/chat/M4gRx-hB6Rr8iT8O0_mmsEQ6vX35yi3qMGtflV1xrlE"

# Messages to send to the AI character
INPUT_MESSAGES = [
    "Hi there! What's your name?",
    "What do you like to do for fun?",
    "Can you tell me about your favorite memory?",
    "What's your opinion on artificial intelligence?",
    "If you could travel anywhere, where would you go?",
    "What makes you happy?",
    "Do you have any fears or worries?",
    "What's the most interesting thing you've learned recently?",
    "How do you feel about our conversation so far?",
    "If you could give one piece of advice to someone, what would it be?",
    "What do you think about the future of technology?",
    "Tell me a joke or something funny.",
]

SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "browser_session")


def wait_for_response(page, message_count_before, timeout=60):
    """Wait for a new AI response to appear after sending a message."""
    start = time.time()
    while time.time() - start < timeout:
        # Character.AI renders messages in a chat container
        # Look for new message elements that appeared after our send
        try:
            # Try multiple selector strategies for robustness
            messages = page.query_selector_all('[class*="message"]')
            if not messages:
                messages = page.query_selector_all('[data-testid*="message"]')
            if not messages:
                messages = page.query_selector_all('div[class*="chat"] > div')

            if len(messages) > message_count_before:
                # Wait a bit more for the response to finish generating
                time.sleep(2)
                # Check if still generating (typing indicator)
                typing = page.query_selector('[class*="typing"]') or page.query_selector('[class*="loading"]')
                if typing:
                    time.sleep(3)
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def get_latest_response(page):
    """Extract the latest AI response text from the chat."""
    try:
        # Strategy 1: Look for the last message that's not from the user
        # Character.AI typically alternates user/bot messages
        selectors = [
            'div[class*="markdown"]',  # Response content often in markdown div
            '[class*="bot-message"]',
            '[class*="char-message"]',
            '[data-testid*="response"]',
            'div[class*="message"] p',
        ]
        for sel in selectors:
            elements = page.query_selector_all(sel)
            if elements:
                last = elements[-1]
                text = last.inner_text().strip()
                if text:
                    return text

        # Fallback: get all text blocks in the chat area and return the last substantial one
        all_msgs = page.query_selector_all('div[class*="chat"] div[class*="message"], div[class*="swiper"] div')
        if all_msgs:
            for msg in all_msgs:
                text = msg.inner_text().strip()
                if text and len(text) > 5:
                    return text
    except Exception as e:
        return f"[Error extracting response: {e}]"
    return "[No response detected]"


def count_messages(page):
    """Count current number of message elements in the chat."""
    selectors = [
        '[class*="message"]',
        '[data-testid*="message"]',
        'div[class*="chat"] > div',
    ]
    for sel in selectors:
        msgs = page.query_selector_all(sel)
        if msgs:
            return len(msgs)
    return 0


def send_message(page, message):
    """Type and send a message in the chat input."""
    # Find the chat input
    input_selectors = [
        'textarea',
        'div[contenteditable="true"]',
        'input[type="text"]',
        '[data-testid*="input"]',
        '[class*="input"]',
    ]

    input_el = None
    for sel in input_selectors:
        input_el = page.query_selector(sel)
        if input_el:
            break

    if not input_el:
        raise Exception("Could not find chat input element")

    # Clear and type the message
    input_el.click()
    input_el.fill(message)
    time.sleep(0.5)

    # Send via Enter key
    input_el.press("Enter")
    time.sleep(1)


def run_automation(character_url, headless=False):
    """Main automation flow."""
    results = []
    timestamp = datetime.now().isoformat()

    with sync_playwright() as p:
        # Use persistent context to save login session
        browser = p.chromium.launch_persistent_context(
            SESSION_DIR,
            headless=headless,
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        # Navigate to Character.AI
        print("Navigating to Character.AI...")
        page.goto("https://character.ai", wait_until="networkidle", timeout=30000)
        time.sleep(3)

        # Check if logged in by looking for login/signup buttons
        login_btn = page.query_selector('a[href*="sign-in"], button:has-text("Sign In"), button:has-text("Log In")')
        if login_btn:
            print("\n" + "=" * 60)
            print("LOGIN REQUIRED")
            print("Please log in to Character.AI in the browser window.")
            print("After logging in, press Enter here to continue...")
            print("=" * 60)
            input()
            time.sleep(3)

        # Navigate to the character chat
        print(f"Navigating to character: {character_url}")
        page.goto(character_url, wait_until="networkidle", timeout=30000)
        time.sleep(5)

        # Dismiss any popups/modals
        try:
            close_btns = page.query_selector_all('button[aria-label="Close"], button:has-text("Got it"), button:has-text("Accept"), button:has-text("Continue")')
            for btn in close_btns:
                btn.click()
                time.sleep(0.5)
        except Exception:
            pass

        print(f"\nSending {len(INPUT_MESSAGES)} messages...\n")

        for i, message in enumerate(INPUT_MESSAGES):
            print(f"[{i+1}/{len(INPUT_MESSAGES)}] Sending: {message[:50]}...")

            msg_count_before = count_messages(page)

            try:
                send_message(page, message)
                time.sleep(2)

                # Wait for response
                got_response = wait_for_response(page, msg_count_before, timeout=60)

                if got_response:
                    response = get_latest_response(page)
                    print(f"  Response: {response[:80]}...")
                else:
                    response = "[Timeout waiting for response]"
                    print(f"  {response}")

            except Exception as e:
                response = f"[Error: {e}]"
                print(f"  {response}")

            results.append({
                "message_index": i + 1,
                "timestamp": datetime.now().isoformat(),
                "input_message": message,
                "ai_response": response,
            })

            # Small delay between messages
            time.sleep(2)

        # Take a screenshot of the final state
        page.screenshot(path="conversation_screenshot.png", full_page=False)
        print("\nScreenshot saved to conversation_screenshot.png")

        browser.close()

    # Save results
    output = {
        "platform": "Character.AI",
        "character_url": character_url,
        "automation_tool": "Playwright",
        "run_timestamp": timestamp,
        "total_messages": len(INPUT_MESSAGES),
        "successful_responses": sum(1 for r in results if not r["ai_response"].startswith("[")),
        "conversation": results,
    }

    with open("conversation_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print("Results saved to conversation_results.json")

    with open("conversation_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["message_index", "timestamp", "input_message", "ai_response"])
        writer.writeheader()
        writer.writerows(results)
    print("Results saved to conversation_results.csv")

    return results


def main():
    parser = argparse.ArgumentParser(description="Character.AI Automation PoC")
    parser.add_argument("--character-url", default=DEFAULT_CHARACTER_URL, help="Character.AI chat URL")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode (no visible browser)")
    args = parser.parse_args()

    print("=" * 60)
    print("Task 2: AI Companion Automation PoC")
    print(f"Platform: Character.AI")
    print(f"Tool: Playwright (Chromium)")
    print(f"Messages to send: {len(INPUT_MESSAGES)}")
    print("=" * 60)

    results = run_automation(args.character_url, args.headless)

    print(f"\n{'=' * 60}")
    print(f"Automation complete!")
    print(f"Total messages sent: {len(results)}")
    print(f"Successful responses: {sum(1 for r in results if not r['ai_response'].startswith('['))}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
