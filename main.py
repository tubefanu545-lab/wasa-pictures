import os
import httpx
import cloudinary
import cloudinary.uploader
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# 🟢 CORS ፈቃድ - ከሁሉም ቦታ (ከብሮውዘርህ) የሚመጣን ጥያቄ ለመቀበል
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🟢 ያንተ የቴሌግራም መረጃዎች
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

# የፎቶዎች ጊዜያዊ ማከማቻ (ዳታቤዝ)
photos_db = []

# ከብሮውዘሩ በ Base64 (በጽሑፍ መልክ) የሚመጣውን ፎቶ መቀበያ ፎርማት
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

@app.get("/photos")
def get_photos():
    return photos_db

# 🔥 100% አስተማማኙ የፎቶ አፕሎድ መቀበያ
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
        # ብሮውዘሩ የላከውን የ Base64 ጽሑፍ በቀጥታ ወደ Cloudinary ሰቅሎ ሊንክ ማውጫ
        upload_result = cloudinary.uploader.upload(
            photo.url,
            folder="wasa_gallery"
        )
        secure_url = upload_result.get("secure_url")
        
        # የተገኘውን የ Cloudinary ሊንክ በዳታቤዙ ውስጥ ማስቀመጥ
        new_photo = {
            "title": x_photo_title,
            "category": x_photo_category,
            "url": secure_url
        }
        photos_db.append(new_photo)
        return new_photo
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {str(e)}")

@app.delete("/photos")
def delete_photo(req: DeleteRequest, x_admin_password: str = Header(None)):
    if x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    global photos_db
    photos_db = [p for p in photos_db if p["url"] != req.url]
    return {"message": "Deleted successfully"}

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