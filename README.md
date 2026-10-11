# Henkel Fabric Care AI — Render-ready project

Mobile-first bilingual (FA/EN) app. Camera/gallery upload, image preview, server-side vision AI and allowlisted product recommendations.

## Publish to Render
1. Upload these files to a **private GitHub repository** (never commit API keys).
2. In Render select **New > Blueprint**, connect the repository and deploy `render.yaml`.
3. Set secret environment variable `OPENAI_API_KEY` in Render dashboard. The API key must never be pasted into the app UI or committed to GitHub.
4. Add verified product records to `approved_products.json`, then redeploy. Until this is done, the AI returns fabric guidance but **no specific product recommendation**.
5. Open your Render HTTPS URL on a phone. Free instances can sleep after inactivity and cold-start slowly.

## Local test
`pip install -r requirements.txt`
`uvicorn server:app --reload --port 8000`
Open http://127.0.0.1:8000. `/health` shows whether AI is configured and number of approved products.

## Catalog example (illustrative schema only; NOT a verified product)
```json
[
  {
    "id":"verified-sku-id",
    "brand":"Persil",
    "name":"EXACT VERIFIED PRODUCT NAME",
    "factory":"Pakshoo",
    "approved":true,
    "usage":"laundry",
    "allowed_fabrics":["cotton"],
    "allowed_colors":["colored"],
    "instructions":"Manufacturer-verified instructions"
  }
]
```
Do not publish example entries as real products. Pril dishwashing liquid must not be recommended for clothes.

**Disclaimer:** Independent prototype; not an official Henkel application. AI cannot reliably establish fiber composition from photos alone. Always prioritize garment care labels.
