import os
import httpx
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# CORS ፈቃድ መስጫ (Frontend እና Backend በቀላሉ እንዲገናኙ)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🟢 ያንተ የቴሌግራም ቦት መረጃዎች እዚህ ገብተዋል
TOKEN = "8847929104:AAHe7yo9CcWm3V1ysjfHnHUtCy7YnE1LbPg"
CHAT_ID = "6809358372"
ADMIN_PASSWORD = "wasa"  # የአስተዳዳሪ ፎቶ መጫኛ ፓስዋርድ

# የፎቶዎች ማከማቻ ዳታቤዝ (ጊዜያዊ በሜሞሪ)
photos_db = []

class BookingData(BaseModel):
    name: str
    phone: str
    type: str
    date: str
    message: Optional[str] = ""

class DeleteRequest(BaseModel):
    url: str

# 1. ዌብሳይቱ ሲከፈት HTML ፋይሉን እንዲያሳይ ማድረግ
@app.get("/", response_class=HTMLResponse)
def read_root():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>index.html file not found! Please check the filename.</h1>"

# 2. የፎቶዎች ሊስት ማግኛ
@app.get("/photos")
def get_photos():
    return photos_db

# 3. ፎቶ መጫኛ (Upload)
@app.post("/photos")
async def upload_photo(
    request: Request,
    x_photo_title: str = Header(None),
    x_photo_category: str = Header(None),
    x_admin_password: str = Header(None)
):
    if x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    photo_bytes = await request.body()
    
    # ሰርቨር ላይ ለጊዜው ፎቶ በፋይል ከማስቀመጥ ይልቅ በሊንክ እንዲሰራ የሚያደርግ
    mock_url = f"https://picsum.photos/800/600?random={len(photos_db) + 1}"
    
    new_photo = {
        "title": x_photo_title,
        "category": x_photo_category,
        "url": mock_url
    }
    photos_db.append(new_photo)
    return new_photo

# 4. ፎቶ መሰረዣ (Delete)
@app.delete("/photos")
def delete_photo(req: DeleteRequest, x_admin_password: str = Header(None)):
    if x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    global photos_db
    photos_db = [p for p in photos_db if p["url"] != req.url]
    return {"message": "Deleted successfully"}

# 5. የቡኪንግ መልእክት ወደ ቴሌግራም መላኪያ
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