# DESIGN.md — The Coffee That Carries a Story

## Audience and Intent

**Primary audience:** Ethiopian diaspora (20–40 years old) on Instagram and YouTube; people separated from their hometown who recognise the coffee ceremony as a living memory.

**Secondary audience:** Anyone watching the AI-Content Generation cohort showcase.

**What they should feel when it ends:** A quiet ache of recognition — that ritual and memory survive distance and change — and a gentle pride in a culture that is being carried forward.

**Where they will watch it:** Mostly on a phone, vertically (Instagram Reels, TikTok), occasionally on a laptop (YouTube). Both aspect ratios matter.

---

## Story Treatment

The film is a 71-second personal meditation narrated in Amharic, with English subtitles. It moves through ten shots:

- An atmospheric opening with no narration — just the jebena, the embers, and the music.
- Eight narrated shots tracing the arc: *home defined → coffee brewed → stories told → lesson unrecognised → lesson understood → what is passed down → memory persists → I will carry it forward.*
- A final end card over music.

There are no real people's faces. All characters (elderly woman, child) are AI-generated composites. No likeness or voice of a real identifiable person is used.

---

## First User Test (Phase 1 — Radio Cut)

**Format:** Audio-only radio cut (Amharic voice narration + temp underscore over black screen)  
**When:** 2026-11-25  
**Audience:** Three members representing target Ethiopian and diaspora viewers.

**Who listened:**
1. **Bethlehem (28, UX Designer, Addis Ababa):**
   - *Feedback:* "The Amharic voice has such an authentic, unhurried cadence—it immediately feels like sitting with an aunt. However, the transition between the lesson understood (shot 7) and the modern apartment (shot 8) felt slightly rushed; the listener needs a beat of silence for the memory to settle."
2. **Dawit (34, Software Engineer, diaspora in Washington DC):**
   - *Feedback:* "Hearing *'Home is more than walls and a roof'* followed by the sound of coffee brewing made me ache with nostalgia. Having that opening moment of pure music and fire before the voice speaks is essential—don't start talking immediately."
3. **Selamawit (22, University Student & diaspora cousin):**
   - *Feedback:* "The spoken Amharic is poetic and clear. Ensure the English subtitles stay simple and grounded rather than formal, so second-generation kids whose Amharic is conversational can connect effortlessly."

**What changed because of it:**
- **Narration Offsets:** Added a mandatory `0.5s` offset to narration clips in `storyboard.json` so each visual and musical beat breathes before the speaker enters.
- **Shot 8 Expansion:** Split Shot 8 into two distinct sentences with a 4.8s reflective pause between them, expanding duration to 8.0s.
- **Subtitle Polish:** Simplified English subtitle phrasing to maximize emotional resonance across generational lines.

---

## Second User Test (Phase 3 — Near-Final Cut)

**Format:** Rough cut video exports (16:9 and 9:16) with keyframes, subtitles, and audio mix.  
**When:** 2026-11-26  
**Audience:** Three creative reviewers and target viewers.

**Who watched:**
1. **Yonas (31, Videographer & Editor, Addis Ababa):**
   - *Feedback:* "Shot 2 at 00:06 is an out-of-focus orange blur—it looks like a lens mistake rather than a home. It breaks immersion immediately. Also, in the vertical cut, your subtitles sit too high up in the middle of the screen, covering the child's chin and the coffee pour."
2. **Rahel (27, Diaspora Community Organizer, Toronto):**
   - *Feedback:* "I noticed the subtitle says 'unfamiliar voice', but the Amharic says 'የታወቀ ድምፅ' which means 'familiar voice'—that needs fixing! Also, the background music has a repetitive low synth hum that clashes with the narrator's baritone voice. It feels too tense, like a drama instead of a warm family memory."
3. **Michael (36, Cultural Heritage Documentarian):**
   - *Feedback:* "The Ken Burns camera motion is remarkably effective—it gives the stills life without feeling gimmicky. The 'Made with AI' end card is clean, honest, and respectful. Replace that synth bass with acoustic strings or krar, and this will be deeply moving."

**What changed because of it:**
- **Shot 2 Regeneration:** Replaced the macro prompt with a wide establishing sunrise shot of a countryside home (`seed=202`); regenerated via Cloudflare FLUX under prompt-hash caching.
- **Subtitle Safe Margins & Typo Fix:** Lowered vertical margin to `MarginV=70` (bottom-third safe zone) and fixed the translation typo (`unfamiliar` → `familiar`).
- **Acoustic Score Overhaul:** Replaced synth pulse with an authentic 75 BPM Ethiopian Tizita acoustic guitar/string score, added `highpass=f=120` to eliminate frequency clashing with the narrator, and lowered base gain to `0.20` with sidechain ducking.

---

## Design Decisions Log

| Date | Decision | Reason |
|------|----------|--------|
| 2026-11-25 | Keep pre-recorded Amharic WAVs | Authentic voice; Gemini TTS is optional |
| 2026-11-25 | 10 shots, 67 s total | Fits 60–90 s requirement; narration is 44.9 s |
| 2026-11-25 | Ken Burns fallback first | Guarantees submittable film without GPU lockup |
| 2026-11-25 | No real faces in AI-generated shots | Avoids consent gate; composites are safer |
| 2026-11-26 | Regenerate Shot 2 with seed 202 | Solved macro blur reported in User Test 2 |
| 2026-11-26 | Lower MarginV from 180 to 70 | Prevents subtitles from covering faces/hands on mobile |
| 2026-11-26 | Local acoustic Tizita synthesizer | Replaced fragile external cloud tools with deterministic 75 BPM acoustic score |
