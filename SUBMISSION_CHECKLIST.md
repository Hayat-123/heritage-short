# Submission Checklist & Complete Guide
**AI-Content Generation: The Heritage Short**  
**Deadline:** Thursday, 26 November, at 23:59 East Africa Time (EAT)

---

## 1. Assignment 1: Codebase and Report Checklist

| Requirement | Rubric Points | Status | Where Found in Repository |
|---|---|---|---|
| **Software engineering & reproducibility** | 20 pts |  Complete | `pipeline/run_all.py`, `schema/storyboard.schema.json`, `runs.jsonl`, `Makefile` |
| **Documentation** | 10 pts |  Complete | [README.md](file:///c:/Users/hayat/code/ai-video-generation/heritage-short/README.md), [ARCHITECTURE.md](file:///c:/Users/hayat/code/ai-video-generation/heritage-short/ARCHITECTURE.md) |
| **Design thinking & audience** | 10 pts |  Complete | [DESIGN.md](file:///c:/Users/hayat/code/ai-video-generation/heritage-short/DESIGN.md) (Notes for 2 user tests, 3 listeners each; all 10 shots have `reason`) |
| **Experimentation & iteration** | 10 pts |  Complete | [EXPERIMENTS.md](file:///c:/Users/hayat/code/ai-video-generation/heritage-short/EXPERIMENTS.md) (10 complete hypothesis → change → result entries) |
| **Troubleshooting & persistence** | 10 pts |  Complete | [FAILURES.md](file:///c:/Users/hayat/code/ai-video-generation/heritage-short/FAILURES.md) (10 real blockers documented with fixes) |
| **Measurement** | 5 pts |  Complete | [COSTS.md](file:///c:/Users/hayat/code/ai-video-generation/heritage-short/COSTS.md) (Exact latencies, GPU/CPU times, and frontier cost delta) |
| **Consent, labelling & licences** | 5 pts |  Complete | [ETHICS.md](file:///c:/Users/hayat/code/ai-video-generation/heritage-short/ETHICS.md) (Informed voice consent recorded; licenses verified; AI disclosure clear) |
| **Written Report** | 30 pts |  Complete | [REPORT.md](file:///c:/Users/hayat/code/ai-video-generation/heritage-short/REPORT.md) (Full report ready to upload or submit as PDF) |

---

## 2. Assignment 2: Film, Walkthrough, and Post Checklist

### A. The Film Files (50 pts)
- **Vertical Cut (9:16 - Main Submission):**  
  [`outputs/film_9x16.mp4`](file:///c:/Users/hayat/code/ai-video-generation/heritage-short/outputs/film_9x16.mp4) (67.0s, 1080×1920, H.264/AAC, -14 LUFS, bottom safe-area subtitles)
- **Horizontal Cut (16:9 - Attachment):**  
  [`outputs/film_16x9.mp4`](file:///c:/Users/hayat/code/ai-video-generation/heritage-short/outputs/film_16x9.mp4) (67.0s, 1920×1080, H.264/AAC, -14 LUFS, clean safe margins)
- *Upload tip:* Upload both MP4 files to Google Drive, YouTube (Unlisted), or Dropbox and ensure link sharing is set to **"Anyone with the link can view"**.

---

### B. 5-Minute Walkthrough Video Script (30 pts)
Record a screen recording (using OBS, Loom, or Windows Game Bar `Win + G`) under 5 minutes following this structure:

* **0:00 – 1:00 (Introduction & Architecture):**
  - *"Hello, my name is Hayat. This is 'The Coffee That Carries a Story', a 67-second heritage short film in Amharic with English subtitles."*
  - Show `ARCHITECTURE.md` on screen: Explain the 5 stages around `storyboard.json` (validate → keyframes → video motion fallback → music synthesis → assembly).
* **1:00 – 2:15 (One Hard Decision Explained):**
  - Explain how cloud music generation (Kaggle/Audiocraft and web platforms) failed due to network blocks and paywalls.
  - Explain the decision to build an autonomous Karplus-Strong physical modeling acoustic guitar synthesizer in Python (`pipeline/03_music.py`) in Ethiopian Tizita pentatonic scale, with 120Hz highpass separation and FFmpeg sidechain ducking under the narrator's voice.
* **2:15 – 4:00 (Live Shot Regeneration Demo - MANDATORY RUBRIC REQUIREMENT):**
  - Open `storyboard.json` on screen.
  - Go to Shot 02 (`"shot_02"`). Change the `seed` from `202` to `203` (or tweak one word in `image_prompt`).
  - Open terminal and run:
    ```bash
    python pipeline/01_keyframes.py
    ```
  - Show terminal output: Shots 1 and 3–10 show `cache hit (skipping)` because their SHA-256 hash didn't change! Only Shot 02 regenerates.
  - Open `runs.jsonl` and show that only ONE new line was appended for `shot_02`.
* **4:00 – 5:00 (Play Final Cut & Conclusion):**
  - Play a 20-second clip of `outputs/film_9x16.mp4` showing the video motion, ducked music, and the "Made with AI" end card.

---

### C. Public Post Draft (20 pts)
Copy and paste this text to LinkedIn, X (Twitter), or Instagram with your video attached and the platform's **AI Label turned ON**:

> **The Coffee That Carries a Story (የቡና ታሪክ)**
> 
> In Ethiopia, coffee is never just a beverage. It is the smell of roasting beans at dawn, the crackle of embers, and the wisdom shared between generations.
> 
> As part of the AI-Content Generation Challenge, I built an automated multi-stage studio in code to produce this 67-second heritage short film narrated in Amharic. 
> 
> Instead of generating disconnected clips by hand, the entire film is orchestrated through code—from JSON schema validation, to Cloudflare FLUX keyframes, an autonomous physical-modeling acoustic synthesizer in Ethiopian Tizita pentatonic scale, and FFmpeg sidechain audio ducking and subtitle burning.
> 
> **One thing I learned:** Generative AI is brittle when treated as a single black box, but resilient when composed as modular software stages with deterministic caching and defensive fallbacks.
> 
> Created with AI (Cloudflare FLUX, Karplus-Strong synthesis, FFmpeg).
> 
> #AIVideo #GenerativeAI #CreativeTech #EthiopianCulture #HeritageShort #Storytelling

---

## 3. AI Interview Preparation (Assignment 1)

After submitting Assignment 1, the AI interviewer will review your repository. Here are the core questions you can expect and your ready answers:

1. **Why is your pipeline structured around `storyboard.json`?**  
   *Answer:* It serves as an immutable single source of truth and contract between stages. Every stage reads only from the storyboard and cached assets, keeping stages decoupled.
2. **How does your caching work?**  
   *Answer:* `pipeline/utils/cache.py` computes a deterministic SHA-256 hash of `stage + shot_id + image_prompt + motion_prompt + seed`. Changing one prompt or seed in `storyboard.json` only alters that shot's hash, skipping all unchanged shots.
3. **Describe a major failure and how you resolved it:**  
   *Answer:* Kaggle/Colab open-weight music models failed due to network isolation and C++ dependency compilation errors. I solved it by authoring a local physical-modeling Karplus-Strong synthesizer in Python, creating an authentic 75 BPM Tizita acoustic score with zero cloud dependencies.
4. **What did your audience tell you during testing?**  
   *Answer:* In the Radio Cut, listeners noted that transitions between reflection and modernity needed pause, leading to narration pre-roll offsets. In the near-final cut, reviewers identified Shot 2's macro blur and subtitle height issues, which led to regenerating Shot 2 as a wide sunrise establishing shot and lowering `MarginV` to 70.
