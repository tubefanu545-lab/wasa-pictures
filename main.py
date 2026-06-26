import os
import httpx
import cloudinary
import cloudinary.uploader
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from supabase import create_client, Client

app = FastAPI()

# 🟢 CORS ፈቃድ - ከሁሉም ቦታ የሚመጡ ጥያቄዎችን ለመቀበል
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🟢 ያንተ የቴሌግራም እና አስተዳዳሪ መረጃዎች
TOKEN = "8847929104:AAHe7yo9CcWm3V1ysjfHnHUtCy7YnE1LbPg"
CHAT_ID = "6809358372"
ADMIN_PASSWORD = "wasa"

# 🟢 ያንተ የ Cloudinary መረጃዎች
cloudinary.config( 
  cloud_name = "dytizzbeg", 
  api_key = "239362398592469", 
  api_secret = "B9421YSAPwersBFHeIS0vsLuHoo",
  secure = True
)

# 🟢 ያንተ የራሱ የ Supabase PostgreSQL ዳታቤዝ ማገናኛ (ቋሚ ማከማቻ)
SUPABASE_URL = "https://xubmrxlqtzglnnthvckr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh1Ym1yeGxxdHpnbG5udGh2Y2tyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI0NzAyNDEsImV4cCI6MjA5ODA0NjI0MX0.z871T5FzR8GKGpOeilmq_QIl3PykSX3gJToh6-O5LXo"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ከብሮውዘሩ በ Base64 የሚመጣውን ፎቶ መቀበያ ፎርማት
class PhotoData(BaseModel):
    url: str

class BookingData(BaseModel):
    name: str
    phone: str
    type: str
    date: str
    message: Optional[str] = ""

class DeleteRequest(BaseModel):
    url: str

@app.get("/", response_class=HTMLResponse)
def read_root():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>index.html file not found!</h1>"

# 🔄 ፎቶዎችን ከ Supabase SQL ዳታቤዝ ውስጥ ለቅሞ ማውጫ (Refresh ቢደረግም አይጠፉም!)
@app.get("/photos")
def get_photos():
    try:
        response = supabase.table("photos").select("*").execute()
        return response.data
    except Exception as e:
        return []

# 💾 ፎቶዎችን ወደ Cloudinary ሰቅሎ ሊንኩን SQL ዳታቤዝ ውስጥ ማስቀመጫ
@app.post("/photos")
async def save_photo_url(
    photo: PhotoData,
    x_photo_title: str = Header(None),
    x_photo_category: str = Header(None),
    x_admin_password: str = Header(None)
):
    if x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        # 1. ፎቶውን ወደ Cloudinary መጫን
        upload_result = cloudinary.uploader.upload(photo.url, folder="wasa_gallery")
        secure_url = upload_result.get("secure_url")
        
        # 2. ሊንኩን በSupabase SQL ዳታቤዝ ውስጥ በቋሚነት መጻፍ
        new_photo = {
            "title": x_photo_title,
            "category": x_photo_category,
            "url": secure_url
        }
        supabase.table("photos").insert(new_photo).execute()
        return new_photo
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database or Cloudinary failed: {str(e)}")

# ❌ ፎቶውን ከSQL ዳታቤዝ ውስጥ ማጥፊያ
@app.delete("/photos")
def delete_photo(req: DeleteRequest, x_admin_password: str = Header(None)):
    if x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        supabase.table("photos").delete().eq("url", req.url).execute()
        return {"message": "Deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/bookings")
async def create_booking(booking: BookingData):
    text = (
        "📸 **አዲስ የፎቶግራፊ ቀጠሮ ተይዟል!** 📸\n\n"
        "👤 ስም: {}\n"
        "📞 ስልክ: {}\n"
        "🎉 የክስተት አይነት: {}\n"
        "📅 ቀን: {}\n"
        "✉️ መልእክት: {}"
    ).format(booking.name, booking.phone, booking.type, booking.date, booking.message)
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        if response.status_code == 200:
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send Telegram message")
