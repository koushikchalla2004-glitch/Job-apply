import os
import io
import requests
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors

app = FastAPI(title="Resume Service", version="0.3.0")

# ----- CORS -----
origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS","*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Supabase env -----
SB_URL  = os.getenv("SUPABASE_URL")                 # e.g. https://xxxx.supabase.co
SB_KEY  = os.getenv("SUPABASE_SERVICE_ROLE_KEY")    # service_role (server-side only)
SB_BUCKET = os.getenv("SUPABASE_BUCKET", "resumes")

PUBLIC_BASE = f"{SB_URL}/storage/v1/object/public/{SB_BUCKET}" if SB_URL else None

class BuildReq(BaseModel):
    role: str
    jd_skills: List[str]
    name: str = "Your Name"
    email: str | None = None
    phone: str | None = None
    summary: str | None = "Results-driven candidate aligned to the job description."
    projects: List[str] = []
    experience: List[str] = []
    education: List[str] = ["M.S. in Data Science (in progress)"]

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.3.0"}

def wrap_text(text: str, width_chars: int):
    words = (text or "").split()
    lines, cur, n = [], [], 0
    for w in words:
        add = len(w) + (1 if cur else 0)
        if n + add > width_chars:
            lines.append(" ".join(cur)); cur = [w]; n = len(w)
        else:
            cur.append(w); n += add
    if cur: lines.append(" ".join(cur))
    return lines

def build_pdf_bytes(req: BuildReq) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter
    margin = 0.65 * inch
    y = height - margin

    def write_line(text, font="Helvetica", size=10, color=colors.black, leading=14):
        nonlocal y
        if y < margin:
            c.showPage(); y = height - margin
        c.setFillColor(color); c.setFont(font, size); c.drawString(margin, y, text); y -= leading

    # Header
    write_line(req.name, font="Helvetica-Bold", size=16, leading=18)
    contact = " | ".join([v for v in [req.email, req.phone] if v])
    if contact: write_line(contact, size=9, color=colors.gray)
    write_line(req.role, font="Helvetica-Bold", size=11, leading=16)

    # Summary
    write_line("SUMMARY", font="Helvetica-Bold", size=10, leading=16)
    for line in wrap_text(req.summary or "", 95): write_line(line, size=10, leading=12)

    # Skills
    write_line("SKILLS", font="Helvetica-Bold", size=10, leading=16)
    skills_line = ", ".join(req.jd_skills)
    for line in wrap_text(skills_line, 95): write_line(line, size=10, leading=12)

    # Experience
    if req.experience:
        write_line("EXPERIENCE", font="Helvetica-Bold", size=10, leading=16)
        for bullet in req.experience:
            for i, line in enumerate(wrap_text(bullet, 92)):
                prefix = "• " if i == 0 else "  "
                write_line(prefix + line, size=10, leading=12)

    # Projects
    if req.projects:
        write_line("PROJECTS", font="Helvetica-Bold", size=10, leading=16)
        for bullet in req.projects:
            for i, line in enumerate(wrap_text(bullet, 92)):
                prefix = "• " if i == 0 else "  "
                write_line(prefix + line, size=10, leading=12)

    # Education
    if req.education:
        write_line("EDUCATION", font="Helvetica-Bold", size=10, leading=16)
        for line in req.education:
            write_line("• " + line, size=10, leading=12)

    c.save()
    return buf.getvalue()

def upload_to_supabase(file_bytes: bytes, object_path: str) -> str:
    """
    Uploads bytes to Supabase Storage via REST.
    Returns a public URL if bucket is public.
    """
    if not (SB_URL and SB_KEY):
        raise RuntimeError("Supabase env vars missing")
    # PUT /storage/v1/object/{bucket}/{path}
    url = f"{SB_URL}/storage/v1/object/{SB_BUCKET}/{object_path}"
    headers = {
        "Authorization": f"Bearer {SB_KEY}",
        "Content-Type": "application/pdf",
        "x-upsert": "true",   # overwrite if same path
    }
    resp = requests.put(url, data=file_bytes, headers=headers, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"Supabase upload failed: {resp.status_code} {resp.text}")
    # Public URL (works if bucket is public)
    return f"{PUBLIC_BASE}/{object_path}"

@app.post("/build_resume")
def build_resume(req: BuildReq):
    pdf_bytes = build_pdf_bytes(req)
    slug_name = req.name.lower().replace(" ", "_")
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    object_path = f"{slug_name}_{ts}.pdf"  # stored at root of bucket

    public_url = upload_to_supabase(pdf_bytes, object_path)
    return {
        "pdf_url": public_url,
        "template": f"ats_{(req.role or 'role').lower().replace(' ', '_')}",
        "generated_at": ts
    }
