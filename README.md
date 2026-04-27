# SinoStudy Navigator: Autonomous AI University Assistant

An Agentic AI workflow for bypassing the chaos of foreign university websites. Built with Python, Playwright Async API, and Google Gemini 2.0 Flash, this tool acts as an autonomous, bilingual higher-education consultant.

## 🚀 Overview

Applying to universities in China can be difficult for international students: critical information (like scholarships, application deadlines, and English-taught programs) is often buried across multiple subpages, obscured by navigation frames, or poorly translated.

**SinoStudy Navigator** solves this by autonomously crawling a university's domain, locating the most valuable admission and scholarship pages, extracting the raw HTML, and utilizing Gemini to synthesize a highly personalized briefing document based on the applicant's specific profile.

## ✨ Key Features

- 🕵️‍♂️ **Autonomous Web Crawling:** Fetches entire site structures and intelligently predicts which subpages hold the highest value using an LLM.
- 🛡️ **Robust Web Scraping:** Uses the **Playwright Asynchronous API** to bypass bots, lazy-loaded JavaScript, and Chinese network firewalls to extract clean text.
- 🧹 **Smart Noise Filtering:** Custom BeautifulSoup logic to strip out navigation headers, footers, cookie banners, and duplicate inline menus.
- 🧠 **Personalized Synthesis:** Cross-references raw, translated university data against a user's academic profile (budget, HSK level, degree interest) to output highly tailored insights.

## 🛠️ Technology Stack

- **Python 3.12+**
- **Playwright (Async)** for headless browser scraping and JavaScript execution.
- **BeautifulSoup4** for complex HTML parsing, table extraction, and noise reduction.
- **Google GenAI API (Gemini 2.0 Flash)** for intelligent crawling logic and final markdown synthesis.
- **Jupyter Notebooks / asyncio** for the runtime environment.

## ⚙️ How It Works

This project utilizes a standard **Agentic Crawl** pattern:

1. **Discover:** The agent visits the university homepage and extracts every absolute link available.
2. **Think & Filter:** It passes the massive list of links to Gemini, acting as a "Web Navigation Agent," to select the 3-5 subpages most likely to contain admissions, program, and scholarship information.
3. **Act:** It autonomously scrapes the selected high-value pages, gracefully handling timeouts caused by blocked external scripts.
4. **Synthesize:** It compiles all the gathered data, combines it with the student profile, and triggers the core extraction prompt to generate the final, personalized admissions brief.

## 💻 Setup & Usage

1. Clone the repository and navigate to the project directory.
2. Set up a Python virtual environment and activate it.
3. Install the dependencies:
   ```bash
   uv pip install python-dotenv google-genai playwright beautifulsoup4
   ```
4. Install the Chromium browser binaries required for Playwright:
   ```bash
   playwright install chromium
   ```
5. Create a `.env` file in the root directory and add your Gemini API key:
   ```env
   GEMINI_API_KEY="your-api-key-here"
   ```
6. Open `chinese_uni_assistant.ipynb` and run all cells to see the agent in action!

## 📄 Example Output

*(Imagine the agent researching Tsinghua University for a prospective Master's student in Computer Science...)*

```markdown
# Tsinghua University (清华大学 / Qīnghuá Dàxué)

## 1. Quick Overview
* **Location:** Beijing, China
* **General Description:** A world-class research university known for its rigorous academic environment and prestigious STEM programs...

## 2. Detailed Programs Offered
* **Specific Majors/Programs:** Master's in Computer Science (English-taught available).
...
## 7. Personalized Recommendations
* **Matching Programs:** Your interest in Computer Science perfectly aligns with their Advanced Computing Master's track.
* **Scholarships:** You are highly eligible for the Chinese Government Scholarship (CSC), which covers your <30,000 RMB budget completely.
```

---
*Created as part of an Advanced LLM Engineering sandbox.*
