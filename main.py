from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
import httpx
import asyncio
import logging
import secrets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Suno AI Music Generator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./leads.db")
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    style = Column(String(50), nullable=False)
    has_text = Column(Integer, default=0)  # 0 = no, 1 = yes
    text_description = Column(Text, nullable=True)
    message = Column(Text, nullable=True)
    source = Column(String(50), default="landing")
    status = Column(String(20), default="new")
    created_at = Column(DateTime, default=datetime.utcnow)
    telegram_sent = Column(Integer, default=0)

class TrackRequest(Base):
    __tablename__ = "track_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, nullable=True)
    prompt = Column(Text, nullable=False)
    style = Column(String(50), default="pop")
    status = Column(String(20), default="pending")
    audio_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Config
SUNO_API_KEY = os.getenv("SUNO_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID", "")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")  # Change in production!

# Simple session storage for admin auth (use Redis in production)
admin_sessions = {}

# Pydantic Models
class LeadCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    style: str
    has_text: bool = False
    text_description: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = "landing"

class LeadResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    style: str
    has_text: bool
    text_description: Optional[str]
    message: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class AdminLoginRequest(BaseModel):
    password: str

class AdminLoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    message: str

class TrackGenerateRequest(BaseModel):
    prompt: str
    style: Optional[str] = "pop"
    duration: Optional[int] = 30
    lead_id: Optional[int] = None

class TrackResponse(BaseModel):
    id: int
    prompt: str
    style: str
    status: str
    audio_url: Optional[str]
    created_at: datetime

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def send_telegram_notification(lead: Lead):
    """Send notification to admin via Telegram bot"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_ADMIN_ID:
        logger.warning("Telegram bot not configured")
        return False
    
    try:
        style_emojis = {
            "pop": "🎵",
            "rock": "🎸", 
            "jazz": "🎺",
            "classical": "🎹",
            "electronic": "🎧",
            "hip-hop": "🎤",
            "ambient": "🌙",
            "cinematic": "🎬"
        }
        style_emoji = style_emojis.get(lead.style, "🎵")
        style_name = lead.style.title() if lead.style else "Не указан"
        
        has_text_str = "✅ Да" if lead.has_text else "❌ Нет"
        text_desc = lead.text_description if lead.has_text and lead.text_description else "-"
        
        message = f"""
🔔 <b>НОВАЯ ЗАЯВКА С ЛЕНДИНГА!</b>

👤 <b>Имя:</b> {lead.name}
📧 <b>Email:</b> {lead.email}
📱 <b>Телефон:</b> {lead.phone}

🎵 <b>Музыкальный стиль:</b> {style_emoji} {style_name}
� <b>Нужен текст:</b> {has_text_str}
"""
        if lead.has_text and lead.text_description:
            message += f"📄 <b>Описание текста:</b> {text_desc}\n"
        
        if lead.message:
            message += f"\n� <b>Комментарий:</b> {lead.message}\n"
        
        message += f"""
🕐 <b>Время:</b> {lead.created_at.strftime('%d.%m.%Y %H:%M')}
📊 <b>ID заявки:</b> #{lead.id}
"""
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TELEGRAM_API_URL}/sendMessage",
                json={
                    "chat_id": TELEGRAM_ADMIN_ID,
                    "text": message,
                    "parse_mode": "HTML"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                logger.info(f"Telegram notification sent for lead {lead.id}")
                return True
            else:
                logger.error(f"Failed to send telegram notification: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error sending telegram notification: {e}")
        return False

async def process_track_generation(track_id: int, request: TrackGenerateRequest):
    """Process track generation asynchronously"""
    db = SessionLocal()
    
    try:
        await asyncio.sleep(10)
        
        track = db.query(TrackRequest).filter(TrackRequest.id == track_id).first()
        if track:
            track.status = "completed"
            track.audio_url = f"/tracks/{track_id}/audio.mp3"
            db.commit()
            logger.info(f"Track {track_id} generation completed")
            
    except Exception as e:
        logger.error(f"Error generating track {track_id}: {e}")
        track = db.query(TrackRequest).filter(TrackRequest.id == track_id).first()
        if track:
            track.status = "failed"
            db.commit()
    finally:
        db.close()

@app.get("/api")
async def api_root():
    return {"message": "Suno AI Music Landing API", "status": "active"}

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/admin")
async def admin_page():
    return FileResponse("static/admin.html")

# Admin Authentication
@app.post("/api/admin/login")
async def admin_login(request: AdminLoginRequest):
    """Admin login endpoint"""
    if request.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Generate session token
    token = secrets.token_urlsafe(32)
    admin_sessions[token] = {
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=24)
    }
    
    return {"success": True, "token": token, "message": "Login successful"}

@app.get("/api/admin/verify")
async def verify_admin_token(token: str):
    """Verify admin token"""
    session = admin_sessions.get(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if datetime.utcnow() > session["expires_at"]:
        del admin_sessions[token]
        raise HTTPException(status_code=401, detail="Token expired")
    
    return {"valid": True}

@app.post("/api/leads", response_model=LeadResponse)
async def create_lead(lead: LeadCreate, background_tasks: BackgroundTasks):
    """Create new lead and send telegram notification"""
    db = next(get_db())
    
    try:
        db_lead = Lead(
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            style=lead.style,
            has_text=1 if lead.has_text else 0,
            text_description=lead.text_description,
            message=lead.message,
            source=lead.source
        )
        db.add(db_lead)
        db.commit()
        db.refresh(db_lead)
        
        logger.info(f"Lead created: {db_lead.id} - {db_lead.email}")
        background_tasks.add_task(send_telegram_notification, db_lead)
        
        return db_lead
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/leads", response_model=List[LeadResponse])
async def list_leads(skip: int = 0, limit: int = 100):
    """List all leads (for admin panel)"""
    db = next(get_db())
    leads = db.query(Lead).order_by(Lead.created_at.desc()).offset(skip).limit(limit).all()
    return leads

@app.get("/api/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: int):
    """Get single lead details"""
    db = next(get_db())
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@app.put("/api/leads/{lead_id}/status")
async def update_lead_status(lead_id: int, status: str):
    """Update lead status"""
    db = next(get_db())
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead.status = status
    db.commit()
    return {"success": True, "message": f"Lead {lead_id} status updated to {status}"}

@app.post("/api/generate", response_model=TrackResponse)
async def generate_track(request: TrackGenerateRequest, background_tasks: BackgroundTasks):
    """Generate music track"""
    db = next(get_db())
    
    try:
        track = TrackRequest(
            lead_id=request.lead_id,
            prompt=request.prompt,
            style=request.style,
            status="processing"
        )
        db.add(track)
        db.commit()
        db.refresh(track)
        
        background_tasks.add_task(process_track_generation, track.id, request)
        
        return TrackResponse(
            id=track.id,
            prompt=track.prompt,
            style=track.style,
            status=track.status,
            audio_url=track.audio_url,
            created_at=track.created_at
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating track: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Get landing statistics"""
    db = next(get_db())
    
    total_leads = db.query(Lead).count()
    new_leads = db.query(Lead).filter(Lead.status == "new").count()
    today_leads = db.query(Lead).filter(
        Lead.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
    ).count()
    total_tracks = db.query(TrackRequest).count()
    
    return {
        "total_leads": total_leads,
        "new_leads": new_leads,
        "today_leads": today_leads,
        "total_tracks": total_tracks
    }

# Serve static files with no caching
from fastapi.responses import Response
import os.path

@app.get("/static/{file_path:path}")
async def serve_static(file_path: str):
    """Serve static files with no caching"""
    file_location = os.path.join("static", file_path)
    
    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get file content
    with open(file_location, "rb") as file:
        content = file.read()
    
    # Determine content type
    if file_path.endswith(".css"):
        content_type = "text/css"
    elif file_path.endswith(".js"):
        content_type = "application/javascript"
    elif file_path.endswith(".html"):
        content_type = "text/html"
    else:
        content_type = "application/octet-stream"
    
    # Return response with no caching headers
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

# Serve landing page for all non-API routes
@app.get("/{full_path:path}")
async def serve_landing(full_path: str):
    """Serve landing page for all non-API routes"""
    # Skip API routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Serve index.html with no caching
    with open("static/index.html", "r", encoding="utf-8") as file:
        content = file.read()
    
    return Response(
        content=content,
        media_type="text/html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
