# COSTS.md — The Coffee That Carries a Story

Track actual costs and limits as you use each service.
List-price equivalents allow fair comparison with paid alternatives.

## Free Tier Summary

| Stage | Model / Tool | Where | Actual cost | Free limit |
|---|---|---|---|---|
| Keyframes | FLUX.2 klein or FLUX.1 schnell | Cloudflare Workers AI | \$0.00 | ~50–170 img/day |
| Moving shots | Wan 2.2 TI2V-5B | Kaggle (2×T4) | \$0.00 | ~30 GPU-h/week |
| Music | ACE-Step 1.5 | Kaggle or Colab | \$0.00 | Same GPU quota |
| Assembly | FFmpeg | Local machine | \$0.00 | Unlimited |
| Coding agent | Antigravity CLI | Local | \$0.00 | Weekly quota |
| Narration | Pre-recorded WAVs | Local | \$0.00 | — |

**Total paid cost: \$0.00**

## List-Price Equivalent (for comparison)

| Service | What it would cost | Source |
|---|---|---|
| ElevenLabs TTS (narration replacement) | ~\$0.30 for 44.9 s | ElevenLabs pricing |
| Runway Gen-3 Alpha (10 shots × 5 s) | ~\$5.00–10.00 | Runway credits |
| Kling AI standard (10 clips) | ~\$3.00–8.00 | Kling pricing |
| Suno / Lyria 3.5 (music, 71 s) | \$0.00–paid tier | varies |
| **Frontier equivalent** | **~\$8–18 per film** | estimate |

## Actual Usage Log

| Date | Stage | Model / Tool | Calls | Processing Time | Latency Avg | Actual Cost | Free Allowance Note |
|---|---|---|---|---|---|---|---|
| 2026-11-26 | keyframes | FLUX.1 schnell (Cloudflare Workers AI) | 12 | 33.4s total | 2.94s | \$0.00 | 12 calls within free daily limit |
| 2026-11-26 | video | FFmpeg Ken Burns 24fps motion | 10 | 24.2s total | 2.42s | \$0.00 | Local CPU (Intel/AMD) |
| 2026-11-26 | music | Local Physical-Modeling Synth (Karplus-Strong) | 1 | 38.0s | 38.0s | \$0.00 | Local Python + FFmpeg |
| 2026-11-26 | audio ducking | FFmpeg sidechaincompress + loudnorm | 1 | 14.5s | 14.5s | \$0.00 | Local CPU |
| 2026-11-26 | assembly | FFmpeg dual export (16:9 + 9:16) | 1 | 18.2s | 18.2s | \$0.00 | Local CPU |

**Total Project Run Cost: \$0.00**

## Cloudflare Free Tier Notes

- Service: Cloudflare Workers AI (`@cf/black-forest-labs/flux-1-schnell`)
- Daily Free Allowance: ~10,000 Neurons/day (~50–170 FLUX images/day free)
- Calls made this project: 12 calls (10 initial keyframes + 1 failed test + 1 Shot 2 regeneration)
- Remaining daily quota: > 85%
- Latency profile: min 1.74s, max 6.73s, mean 2.94s

## Local vs Cloud Resource Comparison

| Stage | Frontier Cloud Equivalent | Local / Open Pipeline | Cost Delta |
|---|---|---|---|
| Keyframes (10 shots) | Midjourney v6 / DALL-E 3: \$0.60 | FLUX.1 schnell (Cloudflare Workers AI): \$0.00 | -\$0.60 |
| Video Motion (10 clips × 6–10s) | Runway Gen-3 Alpha / Kling AI: \$12.00 | FFmpeg Ken Burns Fallback (Local CPU): \$0.00 | -\$12.00 |
| Music Score (67s instrumental) | Suno AI Pro / Udio: \$0.50 | Local Karplus-Strong Physical Synthesizer: \$0.00 | -\$0.50 |
| Voice Narration (44.9s Amharic) | ElevenLabs Custom Voice: \$0.45 | Authentic in-person recorded Amharic WAVs: \$0.00 | -\$0.45 |
| Assembly & Mastering | Adobe Premiere Pro / Cloud Render: \$1.50 | Local Gyan.FFmpeg 9.1: \$0.00 | -\$1.50 |
| **Total Equivalent** | **\$15.05** | **\$0.00** | **-\$15.05 (100% free)** |
