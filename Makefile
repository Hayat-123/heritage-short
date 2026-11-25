# ============================================================
# Makefile for The Coffee That Carries a Story
# Requires: GNU Make, Python 3.9+, FFmpeg
# Windows: install GNU Make via `winget install GnuWin32.Make`
#          or just run: python pipeline/run_all.py
# ============================================================

PYTHON   = python
PIPELINE = pipeline

.PHONY: all film validate music endcard fallback assemble radio-cut clean help

## Default target
all: film

## Run the full pipeline (Ken Burns fallback path, no paid APIs)
film: validate music endcard fallback assemble

## Validate storyboard.json against schema
validate:
	$(PYTHON) $(PIPELINE)/00_validate.py

## Generate placeholder score.wav (or use real ACE-Step output if present)
music:
	$(PYTHON) $(PIPELINE)/03_music.py

## Generate end-card keyframe (Cloudflare if credentials set, else local)
endcard:
	$(PYTHON) $(PIPELINE)/05_endcard.py

## Generate Ken Burns fallback clips for every shot
fallback:
	$(PYTHON) $(PIPELINE)/02_video_fallback.py

## Assemble final film (both aspect ratios)
assemble:
	$(PYTHON) $(PIPELINE)/04_assemble.py --force

## Phase 1 checkpoint: narration over black + music
radio-cut:
	$(PYTHON) $(PIPELINE)/03_music.py
	$(PYTHON) $(PIPELINE)/04_assemble.py --radio-cut --force

## Generate keyframes via Cloudflare Workers AI (optional — set .env first)
keyframes:
	$(PYTHON) $(PIPELINE)/01_keyframes.py

## Regenerate one keyframe (usage: make keyframe SHOT=shot_03)
keyframe:
	$(PYTHON) $(PIPELINE)/01_keyframes.py --shot $(SHOT)

## Show Wan 2.2 video status (Kaggle upgrade)
video-status:
	$(PYTHON) $(PIPELINE)/02_video.py --status

## Generate Wan 2.2 Kaggle notebook cell
video-notebook:
	$(PYTHON) $(PIPELINE)/02_video.py --write-notebook

## Generate ACE-Step Kaggle notebook cell
music-notebook:
	$(PYTHON) $(PIPELINE)/03_music.py --write-notebook

## Remove generated outputs (keeps storyboard and assets)
clean:
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in [pathlib.Path('outputs'), pathlib.Path('assets/shots'), pathlib.Path('assets/keyframes')]]"
	@echo "Cleaned outputs/, assets/shots/, assets/keyframes/"

help:
	@echo ""
	@echo "  make film          Full pipeline (validate → music → endcard → fallback → assemble)"
	@echo "  make radio-cut     Phase 1: narration + music over black"
	@echo "  make validate      Validate storyboard.json"
	@echo "  make keyframes     Cloudflare FLUX keyframes (needs .env)"
	@echo "  make video-status  Check real vs fallback video clips"
	@echo "  make clean         Delete generated outputs"
	@echo ""
	@echo "  Windows without Make: python pipeline/run_all.py"
	@echo ""
