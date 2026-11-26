# Project Report: The Coffee That Carries a Story
**AI-Content Generation: The Heritage Short (Week 0 Challenge)**  
**Author:** Hayat Mohammedsherif  
**Repository:** `heritage-short/`  
**Date:** November 26, 2026  
**Film Links:**
- **Vertical (9:16 - Main Cut):** [Watch on Vimeo (9:16)](https://vimeo.com/share/a4244b2a-c8c4-48c5-ae7b-18889444628f?share=copy&fl=sv&fe=ci)
- **Horizontal (16:9):** [Watch on Vimeo (16:9)](https://vimeo.com/share/7d08e21a-7bbc-44dc-a991-cb4fd37afde6?share=copy&fl=sv&fe=ci)

---

## 1. What I Set Out to Make, and for Whom

I set out to create an intimate, 67-second heritage short film titled *"The Coffee That Carries a Story"* (*የቡና ታሪክ*). The film explores how the traditional Ethiopian coffee ceremony is not merely a social routine or beverage preparation, but a living vessel of memory, values, patience, and love passed down across generations. 

### Target Audience & Intent
* **Primary Audience:** Ethiopian youth and the global Ethiopian diaspora (ages 18–40) living in cities like Addis Ababa, Washington D.C., London, and Toronto, who may feel physically distanced from their family roots yet retain an instinctive emotional connection to the smell of roasting beans and the sound of the clay *jebena*.
* **Secondary Audience:** Cultural archivists and creative AI practitioners interested in indigenous storytelling mediated by modular generative pipelines.
* **Intended Emotional Arc:** Viewers should experience a quiet ache of recognition that ritual survives displacement, ending with grounded pride and a personal commitment to carry the tradition forward.

---

## 2. Audience Reflection & Learning: What They Said and What Changed

We conducted two rounds of user feedback following design-thinking principles: an early low-fidelity **Radio Cut test** (Phase 1) and a **Near-Final Video cut test** (Phase 3). Each session included three participants from our target audience.

### A. Radio Cut Feedback (Phase 1)
* **Bethlehem (28, UX Designer, Addis Ababa):** Praised the authentic cadence of the pre-recorded Amharic narration, but noted that the transition between the lesson understood (Shot 07) and the modern apartment (Shot 08) felt rushed. The listener needed space to digest the emotion before returning to the present.
* **Dawit (34, Software Engineer, Washington D.C. diaspora):** Emphasized that the opening visual hook required breathing room. Starting speech immediately would break the contemplative sacredness of the ceremony.
* **Selamawit (22, Student):** Advised keeping the English subtitle phrasing conversational and grounded rather than poetic or academic, ensuring second-generation diaspora who speak conversational Amharic can follow effortlessly.
* **What Changed:**
  - Added a `0.5s` audio pre-roll offset to every narrated shot in `storyboard.json` so the visual atmosphere and acoustic chords land before the speaker begins.
  - Expanded Shot 08 to 8.0 seconds, splitting the narration into two distinct sentences with a 4.8s reflective pause.
  - Simplified and verified subtitle phrasing.

### B. Near-Final Cut Feedback (Phase 3)
* **Yonas (31, Videographer, Addis Ababa):** Identified that Shot 02 ("Home is more than walls and a roof") rendered as an out-of-focus macro mud texture rather than a home. He also noted that in vertical 9:16, subtitles sat too high in the center of the frame, obscuring the elder's hands and the coffee pouring action.
* **Rahel (27, Diaspora Organizer, Toronto):** Caught a translation error in Shot 03 ("unfamiliar voice" instead of "familiar voice", contradicting the Amharic word *የታወቀ*). She also observed that the initial background score had a heavy, repetitive synth bass that competed with the male narrator's baritone voice.
* **Michael (36, Cultural Heritage Archivist):** Highlighted that the Ken Burns pan-and-zoom motion gave the stills authentic documentary weight, and commended the explicit "Made with AI" end card.
* **What Changed:**
  - Regenerated Shot 02 as an evocative wide exterior establishing shot of an Ethiopian countryside home at sunrise (`seed=202`).
  - Lowered subtitle vertical margin from `MarginV=180` to `MarginV=70`, anchoring text cleanly in the mobile lower-third safe zone.
  - Fixed the subtitle typo (`unfamiliar` → `familiar`).
  - Completely replaced the synth track with an authentic 75 BPM Ethiopian Tizita acoustic guitar/string score, notched with a 120Hz highpass filter and sidechain ducking.

---

## 3. The Hardest Problem and How It Was Solved

The hardest engineering obstacle was **achieving robust, high-fidelity music scoring without relying on fragile cloud infrastructure or gated commercial web tools.**

### The Blocker
Our original plan relied on open-weight ACE-Step 1.5 or Audiocraft on Kaggle/Colab. However, strict outbound network policies blocked git dependencies, and missing C++ compilation toolchains caused fatal errors during wheel building (`failed to build av`). When we evaluated web-based alternatives (Suno, Udio), free tiers had blocked direct audio downloads and required account paywalls.

### The Solution: Autonomous Physical Modeling
Rather than faking an API call or abandoning the musical score, we developed an autonomous physical-modeling music synthesizer directly in Python (`pipeline/03_music.py`) using zero external dependencies:
1. **Karplus-Strong Plucked String Synthesis:** We implemented the Karplus-Strong physical modeling algorithm to simulate acoustic nylon/gut strings for traditional Ethiopian *krar* and acoustic guitar arpeggios in the nostalgic *Tizita Major* pentatonic scale (`D → G → Bm → A` at 75 BPM).
2. **Warm String Pad Bed:** We layered multi-harmonic bowed string chords with an analog 4.5 Hz vibrato LFO.
3. **Studio FFmpeg Post-Processing:** We shaped the synthesized audio through FFmpeg using a 3-tap acoustic hall reverb (`aecho=0.85:0.88:60|120|240`), warm low-mid EQ (+2.5 dB at 280 Hz), and analog high-frequency roll-off (`lowpass=f=6200`).
4. **Sidechain Ducking:** In `pipeline/04_assemble.py`, the music was fed through a 120Hz high-pass filter and ducked automatically (`sidechaincompress=threshold=0.02:ratio=6:attack=300:release=1500`), creating professional broadcast separation under the voice.

This produced a tailored 67-second instrumental score in 38 seconds locally with 100% offline reproducibility.

---

## 4. Suggested Practices Tested Honestly

### Practice That Beat My Instinct: Schema Contract & Prompt-Hash Caching
* **My initial instinct:** It felt like unnecessary overhead to define a strict JSON Schema (`storyboard.schema.json`) and write SHA-256 caching code before generating any media.
* **What actually happened:** This practice saved the entire project. When Shot 08's narration clips initially exceeded the shot duration, `00_validate.py` caught the error in 0.05 seconds before any API calls were made. Furthermore, when Shot 02 required regeneration due to user feedback, the SHA-256 prompt-hash caching ensured that only Shot 02 made an API call to Cloudflare (`runs.jsonl` line 12); shots 1 and 3–10 were instantly loaded from cache. The pipeline demonstrated true incremental compilation.

### Practice That Did Not Beat My Instinct: Remote GPU Notebooks for Audio Synthesis
* **The suggested practice:** Run open-weight music models (ACE-Step 1.5) on free hosted Kaggle/Colab GPU environments.
* **What actually happened:** Fragile cloud environments introduced unexpected environment drift, network permission issues (git clone error 128), and wheel compilation failures. Relying on remote GPU instances for a task that could be executed reliably through deterministic local synthesis and FFmpeg processing wasted over an hour of debugging time. Moving the audio synthesis stage local and self-contained was dramatically more dependable.

---

## 5. Curiosity Beyond the Floor (Ceiling Work)

To push the project beyond the baseline requirements, we implemented two major technical contributions:

1. **Self-Contained Algorithmic Physical Modeling Engine:** Instead of using canned stock music or empty placeholders, we designed a standalone physical modeling synthesis engine based on the Karplus-Strong string algorithm, tuned to traditional Ethiopian pentatonic scales. This allows any developer running this repository to generate infinite unique, copyright-free musical variations simply by changing the random seed and scale mode.
2. **Dual-Aspect Ratio Master Video Architecture:** Rather than exporting 16:9 and naively cropping it down to 9:16 (which degrades resolution and doubles burned-in subtitles), we engineered `pipeline/04_assemble.py` to maintain an unburned high-bitrate intermediate master track (`video_track.mp4`). Both 16:9 (`1920x1080`, `MarginV=60`, `FontSize=20`) and 9:16 (`1080x1920`, `MarginV=70`, `FontSize=13`) are rendered independently in a single pass, ensuring optimal composition framing and safe-area subtitle compliance.

---

## 6. What I Would Build Next

If I had another week to expand this project, I would build:
* **Interactive Family Storyboard Web App:** A lightweight Streamlit or Gradio interface where elderly relatives can record short voice memos on their phones, speak Amharic, Oromo, or Tigrinya, and have the pipeline automatically transcribe, extract emotional beats, suggest image prompts, and produce a finished short film without writing a line of code.
* **Character Consistency LoRA / IP-Adapter Pipeline:** Train a lightweight character consistency model on historical family photographs so the depicted elders and children maintain exact facial features across multi-scene narrative films.
