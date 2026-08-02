# V8 Gemini Mode

Gemini mode changes only the art-plate stage. The exact text compositor, export sizes, QA checks, contact sheet, and manifest remain the same as mock mode.

Start with one fully ready card. The workflow validates `GEMINI_API_KEY`, rejects blocked data before generation, requests a 3:4 art plate, crops safely to 5:7, and then produces the final master, app image, and thumbnail.
