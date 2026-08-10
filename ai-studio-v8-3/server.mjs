import express from 'express';
import { GoogleGenAI } from '@google/genai';
import { parse } from 'csv-parse/sync';
import sharp from 'sharp';

const app = express();
const port = process.env.PORT || 8080;

app.use(express.json({ limit: '80mb' }));
app.use(express.static('public'));

const MODEL_DEFAULT = process.env.GEMINI_IMAGE_MODEL || 'gemini-3.1-flash-image';
const V83_LOCK = `
V8.3 ABSOLUTE LOCK — APPLY TO EVERY CARD:
- One complete finished card in one generation request. Final title, exact copy, category icon, subject-specific identifier, plaque and canonical ID must be present in the image.
- Correct canonical ID and subject are mandatory. Do not substitute another species.
- Subject is the largest and sharpest focal point. Only distant habitat may have restrained depth-of-field softness. Foreground habitat frame, title panel, lower panel, plaque, text and defining anatomy stay crisp.
- Organic frame is a physical continuation of the exact habitat. Strong asymmetry. Leave at least one major edge or corner open so actual habitat reaches full bleed.
- Never trace the card rectangle, mirror both sides, balance all four corners, make a vine cage, wreath, oval enclosure, generic picture frame, equal-width rim or four-sided surround.
- Pop color is selective and localized only: one dominant exterior opening, optionally one much smaller secondary opening. It is usually subject-derived, but may be habitat-derived if needed for better contrast. No color on every edge.
- Pop color must be clean and natural: no grunge, speckles, splatter, peeling paint, paint smear, ombre, glow, halo, feathered fade or paper-like perimeter.
- Title panel, information panel and number plaque use the exact same physical material treatment. Shapes may vary.
- Title is straight, horizontal, ALL CAPS, about 80% refined Red Panda carved serif and 20% softer Fennec hand-carved irregularity.
- Lower panel uses the Fennec Fox hierarchy: centered italic scientific name; compact stats; restrained divider; subject-specific identifier lower left; exact fun fact centered; exact canonical ID once only lower right.
- Category icon and subject identifier are different and specific. Never use generic Leaf, Track, Paw print, Footprint or other placeholders unless the row explicitly provides an approved final instruction.
- No footer. No unrelated branding. No pseudo-text, duplicated ID, wrong ID, wrong subject or malformed anatomy.
`;

function ensureApiKey() {
  if (!process.env.GEMINI_API_KEY) {
    const err = new Error('GEMINI_API_KEY is not configured. In Google AI Studio, add it in Secrets; AI Studio normally injects it server-side.');
    err.status = 500;
    throw err;
  }
}

function validateCard(card) {
  const errors = [];
  const required = ['Card ID', 'Subject', 'Manus Direct Finished-Card Prompt'];
  for (const field of required) {
    if (!card?.[field]?.trim()) errors.push(`Missing ${field}`);
  }
  const prompt = card?.['Manus Direct Finished-Card Prompt'] || '';
  const id = card?.['Card ID'] || '';
  const subject = card?.['Subject'] || '';
  if (id && !prompt.includes(id)) errors.push(`Prompt does not contain canonical ID ${id}`);
  if (subject && !prompt.toLowerCase().includes(subject.toLowerCase())) errors.push(`Prompt does not contain subject ${subject}`);
  const blocked = ['ART PLATE', 'TEXT-FREE', 'BLANK PANEL', 'TWO-STAGE', 'COMPOSITOR'];
  for (const token of blocked) {
    if (prompt.toUpperCase().includes(token)) errors.push(`Blocked legacy token: ${token}`);
  }
  return errors;
}

function dataUrlToInput(dataUrl) {
  const match = /^data:(image\/[a-zA-Z0-9.+-]+);base64,(.+)$/.exec(dataUrl || '');
  if (!match) throw new Error('Invalid reference image data URL');
  return { type: 'image', mime_type: match[1], data: match[2] };
}

async function normalizeTo5x7(base64, mimeType = 'image/png') {
  const src = Buffer.from(base64, 'base64');
  const image = sharp(src);
  const meta = await image.metadata();
  if (!meta.width || !meta.height) return { base64, mimeType, normalized: false };

  // Gemini currently offers 3:4, not native 5:7. We request 3:4 and perform a geometry-only center crop.
  // The prompt reserves the outer ~2.5% on each side for habitat bleed only, so no title/panel/plaque/frame content is intentionally cropped.
  const targetWidth = Math.round(meta.height * 5 / 7);
  if (targetWidth >= meta.width) return { base64, mimeType, normalized: false };
  const left = Math.floor((meta.width - targetWidth) / 2);
  const out = await image.extract({ left, top: 0, width: targetWidth, height: meta.height }).png().toBuffer();
  return { base64: out.toString('base64'), mimeType: 'image/png', normalized: true, width: targetWidth, height: meta.height };
}

app.get('/api/health', (_req, res) => {
  res.json({ ok: true, model: MODEL_DEFAULT, v83: true, apiKeyConfigured: Boolean(process.env.GEMINI_API_KEY) });
});

app.post('/api/parse-csv', (req, res) => {
  try {
    const records = parse(req.body.csv || '', { columns: true, skip_empty_lines: true, relax_quotes: true, bom: true });
    const rows = records.map((row) => ({ ...row, _validation: validateCard(row) }));
    res.json({ rows, count: rows.length, valid: rows.filter(r => r._validation.length === 0).length });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

app.post('/api/generate', async (req, res) => {
  try {
    ensureApiKey();
    const { card, referenceImages = [], model = MODEL_DEFAULT, imageSize = '2K', normalize5x7 = true } = req.body;
    const validation = validateCard(card);
    if (validation.length) return res.status(400).json({ error: 'Card blocked by V8.3 validation', validation });

    const basePrompt = card['Manus Direct Finished-Card Prompt'];
    const prompt = `${basePrompt}\n\n${V83_LOCK}\n\nGEOMETRY SAFETY FOR GOOGLE IMAGE MODELS:\nCompose the entire finished card inside the central 95% of the 3:4 canvas width. Keep only expendable habitat bleed in the extreme outer 2.5% left and right so a geometry-only 5:7 crop cannot cut the subject, title, lower panel, plaque, text, category icon, identifier, or organic frame objects. Do not add a visible border for this safe area.`;

    const input = [{ type: 'text', text: prompt }];
    for (const img of referenceImages.slice(0, 10)) input.push(dataUrlToInput(img));

    const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
    const interaction = await ai.interactions.create({
      model,
      input,
      response_format: {
        type: 'image',
        mime_type: 'image/png',
        aspect_ratio: '3:4',
        image_size: imageSize
      }
    });

    let imageData = interaction.output_image?.data;
    let mimeType = 'image/png';
    if (!imageData) {
      for (const step of interaction.steps || []) {
        if (step.type !== 'model_output') continue;
        for (const block of step.content || []) {
          if (block.type === 'image') {
            imageData = block.data;
            mimeType = block.mime_type || mimeType;
            break;
          }
        }
      }
    }
    if (!imageData) throw new Error('Gemini returned no image');

    const normalized = normalize5x7 ? await normalizeTo5x7(imageData, mimeType) : { base64: imageData, mimeType, normalized: false };
    res.json({
      cardId: card['Card ID'],
      subject: card['Subject'],
      image: `data:${normalized.mimeType};base64,${normalized.base64}`,
      normalized5x7: normalized.normalized,
      width: normalized.width,
      height: normalized.height,
      model
    });
  } catch (error) {
    res.status(error.status || 500).json({ error: error.message });
  }
});

app.listen(port, () => console.log(`V8.3 Zoo Card Studio listening on ${port}`));
