import os, sys, csv, time, json, logging
from pathlib import Path
from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler(sys.stdout)])

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTS_DIR = BASE_DIR / "renders" / "fronts"
REPORTS_DIR = BASE_DIR / "reports"
FRONTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    logging.error("GEMINI_API_KEY environment variable is missing.")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)
MODEL_NAME = "imagen-3.0-generate-002"

def render_card(card_id, species, prompt_text, max_retries=3):
    clean = species.lower().replace(" ", "_").replace("-", "_")
    filename = f"{card_id}_{clean}_front.png"
    output_path = FRONTS_DIR / filename
    if output_path.exists():
        logging.info(f"Skipping {card_id} ({species}) — already exists.")
        return {"id": card_id, "species": species, "status": "skipped", "path": str(output_path)}
    for attempt in range(1, max_retries + 1):
        try:
            logging.info(f"Rendering {card_id} ({species}) [Attempt {attempt}/{max_retries}]...")
            response = client.models.generate_images(
                model=MODEL_NAME,
                prompt=prompt_text,
                config=types.GenerateImagesConfig(number_of_images=1, output_mime_type="image/png", aspect_ratio="3:4")
            )
            if response.generated_images:
                image_bytes = response.generated_images[0].image.image_bytes
                with open(output_path, "wb") as f:
                    f.write(image_bytes)
                logging.info(f"Saved: {filename}")
                return {"id": card_id, "species": species, "status": "success", "path": str(output_path)}
        except Exception as e:
            logging.warning(f"Error on attempt {attempt}: {e}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)
    logging.error(f"Failed {card_id} after {max_retries} attempts.")
    return {"id": card_id, "species": species, "status": "failed", "error": f"Failed after {max_retries} attempts"}

def run_batch(csv_path, limit=10):
    results = []
    if not Path(csv_path).exists():
        logging.error(f"CSV not found: {csv_path}")
        sys.exit(1)
    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            if limit and count >= limit:
                logging.info(f"Reached batch limit of {limit}.")
                break
            card_id = row.get("id") or row.get("Card_ID") or f"CARD_{count+1:03d}"
            species = row.get("species") or row.get("Species") or "Unknown"
            prompt = row.get("prompt") or row.get("Prompt_V7_1") or row.get("Prompt")
            if not prompt:
                logging.warning(f"Skipping {card_id}: no prompt.")
                continue
            results.append(render_card(card_id, species, prompt))
            count += 1
    report_path = REPORTS_DIR / "qa_audit.json"
    with open(report_path, "w", encoding="utf-8") as rf:
        json.dump(results, rf, indent=2)
    logging.info(f"Done. Report: {report_path}")
    successes = sum(1 for r in results if r["status"] == "success")
    failures = sum(1 for r in results if r["status"] == "failed")
    logging.info(f"Results: {successes} success, {failures} failed, {len(results)-successes-failures} skipped")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Kova-AI Gemini Card Renderer v7.1")
    parser.add_argument("--csv", type=str, default="data/v7.1_zoo_prompts.csv")
    parser.add_argument("--limit", type=int, default=10, help="Cards to render (0 = all)")
    args = parser.parse_args()
    run_batch(args.csv, limit=args.limit)
