# Task explanation and approach



**Platform:** Character.AI (https://character.ai)  
**Approach:** Playwright browser automation  

---

## Overview

This Proof of Concept demonstrates automated interaction with an AI companion character on Character.AI by sending a list of messages and capturing responses.

---

## Approach

- Uses **Playwright** to automate a Chromium browser with a persistent session to avoid repeated logins
- Navigates to a specified Character.AI character chat page
- Sends a predefined list of 12 messages sequentially via the chat input field
- Polls the DOM after each message to detect and wait for the AI response to finish generating
- Extracts the AI response text using multiple CSS selector strategies for robustness
- Saves the full conversation to **JSON** and **CSV** (both files are attached in this repository) along with a **screenshot** of the final chat state

---

## Why This Approach is Effective and Scalable

- **No API dependency** — Playwright controls a real browser, so it works with any web-based AI platform regardless of whether a public API exists
- **Persistent session** — login cookies are saved to disk, eliminating the need to re-authenticate on every run
- **Element detection** — multiple CSS selector strategies are tried in sequence, making the script resilient to minor UI changes on the platform
- **Flexible inputs** — the character URL and message list are easily swappable, allowing the same script to be reused across different characters or question sets

---

## Assumptions and Limitations

- **Login required** — the script assumes the user will log in manually on the first run. Automated credential entry was intentionally avoided for security reasons
- **DOM selector** — Although multiple selectors are tried, a major Character.AI UI redesign could still break response detection and require selector updates
- **Single character only** — each run targets one character URL; automating across multiple characters would require looping logic to be added.
- **Rate limiting** — Character.AI may throttle or block automated interactions if too many messages are sent too quickly, as the platform is designed for human-paced conversation

---

## Extending to Multiple Platforms

- The core functions (`send_message`, `wait_for_response`, `get_latest_response`) can be abstracted into a base class, with platform-specific subclasses overriding only the selectors and navigation logic for each platform
- Each platform's URL, CSS selectors, and login flow could be defined in a JSON or YAML config file, allowing new platforms to be added without changing the core script
- Platforms that offer a public API (e.g. character engines built on OpenAI) could bypass browser automation entirely
- Using Playwright's async API or Python's `multiprocessing`, multiple platforms or characters could be automated simultaneously

# Demo Video URL:



## Usage

```bash
python3 task2_automation_poc.py [--character-url URL] [--headless]