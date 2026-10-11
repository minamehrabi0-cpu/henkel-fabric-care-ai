"""Run: pip install -r requirements.txt; OPENAI_API_KEY=... uvicorn server:app --host 0.0.0.0 --port 8000"""
import os, json, base64, re
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse


ROOT=Path(__file__).resolve().parent
app=FastAPI(title='Henkel Fabric Care')
@app.get('/')
async def home(): return FileResponse(ROOT/'index.html')

@app.get('/health')
async def health(): return {'server':'ok','ai_configured':bool(os.getenv('OPENAI_API_KEY')),'approved_products':len(catalog())}

@app.get('/offline-demo')
async def offline_demo(): return FileResponse(ROOT/'offline-demo.html')

def catalog():
    data=json.loads((ROOT/'approved_products.json').read_text(encoding='utf-8'))
    return [p for p in data if p.get('approved') is True and p.get('brand','').casefold() in ('persil','pril') and p.get('factory','').casefold() in ('pakshoo','farco') and p.get('id') and p.get('name')]

@app.post('/api/analyze')
async def analyze(image: UploadFile=File(...), language: str=Form("fa")):
    if not os.getenv('OPENAI_API_KEY'): raise HTTPException(503,'کلید API هوش مصنوعی در سرور تنظیم نشده است.')
    if image.content_type not in ('image/jpeg','image/png','image/webp'): raise HTTPException(400,'فرمت تصویر باید JPEG، PNG یا WebP باشد.')
    raw=await image.read(10*1024*1024+1)
    if not raw: raise HTTPException(400,'تصویر خالی است.')
    if len(raw)>10*1024*1024: raise HTTPException(413,'تصویر بزرگ‌تر از ۱۰ مگابایت است.')
    products=catalog()
    safe_catalog=[{'id':p['id'],'brand':p['brand'],'name':p['name'],'allowed_fabrics':p.get('allowed_fabrics',[]),'allowed_colors':p.get('allowed_colors',[]),'instructions':p.get('instructions',''),'usage':'laundry' if p.get('usage')=='laundry' else 'other'} for p in products]
    language='en' if language=='en' else 'fa'
    instructions='''Analyze the photo as a fabric care assistant. Respond ONLY with valid JSON fields: fabric_type, color, confidence (low/medium/high), care_label, washing_advice, recommended_ids (array of catalog IDs), reasons (object keyed by catalog ID). Write descriptive values in {language_name}. Never claim certainty about fiber composition from an image; mark uncertainty. Care label overrides visual guesses. Do not recommend dry-clean-only or delicate items without clear label support. Choose products ONLY from the provided catalog, checking fabric, color, instructions and usage. Pril or any non-laundry product must NEVER be recommended for clothing. If unsure, recommend none. No competitor names. Catalog: '''+json.dumps(safe_catalog,ensure_ascii=False)
    instructions=instructions.replace(chr(123)+'language_name'+chr(125), 'English' if language=='en' else 'Persian')
    from openai import AsyncOpenAI
    client=AsyncOpenAI()
    try:
        completion=await client.chat.completions.create(model=os.getenv('VISION_MODEL','gpt-4o-mini'),response_format={'type':'json_object'},messages=[{'role':'system','content':instructions},{'role':'user','content':[{'type':'text','text':'Analyze this garment photo and recommend only approved catalog products. Respond in '+('English' if language=='en' else 'Persian')},{'type':'image_url','image_url':{'url':f'data:{image.content_type};base64,{base64.b64encode(raw).decode()}'}}]}],temperature=0.1)
        result=json.loads(completion.choices[0].message.content)
    except Exception: raise HTTPException(502,'خطا در سرویس تحلیل تصویر. تنظیمات سرور را بررسی کنید.')
    ids=result.get('recommended_ids',[])
    if not isinstance(ids,list): ids=[]
    matched=[]
    for p in products:
        if p['id'] not in ids or p.get('usage')!='laundry': continue
        if not p.get('allowed_fabrics') or not p.get('allowed_colors'): continue
        # Defense in depth: exact allowed-catalog ID and laundry-only use.
        matched.append({'brand':p['brand'],'name':p['name'],'reason':str(result.get('reasons',{}).get(p['id'],'طبق مشخصات تأییدشده محصول'))})
    return {k:result.get(k,'نامشخص') for k in ('fabric_type','color','confidence','care_label','washing_advice')} | {'products':matched}
