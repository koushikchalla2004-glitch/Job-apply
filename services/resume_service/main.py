import os
import io
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors

app = FastAPI(title="Resume Service", version="0.2.0")

origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS","*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FILE_BASE = os.getenv("FILE_BASE", "/app/static/resumes")
os.makedirs(FILE_BASE, exist_ok=True)
app.mount("/files", StaticFiles(directory="/app/static"), name="static")

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
    return {"status": "ok", "version": "0.2.0"}

def wrap_text(text: str, width_chars: int):
    words = (text or "").split()
    lines = []
    cur = []
    n = 0
    for w in words:
        add = len(w) + (1 if cur else 0)
        if n + add > width_chars:
            lines.append(" ".join(cur))
            cur = [w]
            n = len(w)
        else:
            cur.append(w)
            n += add
    if cur:
        lines.append(" ".join(cur))
    return lines

@app.post("/build_resume")
def build_resume(req: BuildReq):
    slug_name = req.name.lower().replace(" ", "_")
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = f"{slug_name}_{timestamp}.pdf"
    out_path = os.path.join(FILE_BASE, filename)

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter
    margin = 0.65 * inch
    y = height - margin

    def write_line(text, font="Helvetica", size=10, color=colors.black, leading=14):
        nonlocal y
        if y < margin:
            c.showPage()
            y = height - margin
        c.setFillColor(color)
        c.setFont(font, size)
        c.drawString(margin, y, text)
        y -= leading

    # Header
    write_line(req.name, font="Helvetica-Bold", size=16, leading=18)
    contact = " | ".join([v for v in [req.email, req.phone] if v])
    if contact:
        write_line(contact, size=9, color=colors.gray)
    write_line(req.role, font="Helvetica-Bold", size=11, leading=16)

    # Summary
    write_line("SUMMARY", font="Helvetica-Bold", size=10, leading=16)
    for line in wrap_text(req.summary or "", 95):
        write_line(line, size=10, leading=12)

    # Skills
    write_line("SKILLS", font="Helvetica-Bold", size=10, leading=16)
    skills_line = ", ".join(req.jd_skills)
    for line in wrap_text(skills_line, 95):
        write_line(line, size=10, leading=12)

    # Experience
    if req.experience:
        write_line("EXPERIENCE", font="Helvetica-Bold", size=10, leading=16)
        for bullet in req.experience:
            lines = wrap_text(bullet, 92)
            for i, line in enumerate(lines):
                prefix = "• " if i == 0 else "  "
                write_line(prefix + line, size=10, leading=12)

    # Projects
    if req.projects:
        write_line("PROJECTS", font="Helvetica-Bold", size=10, leading=16)
        for bullet in req.projects:
            lines = wrap_text(bullet, 92)
            for i, line in enumerate(lines):
                prefix = "• " if i == 0 else "  "
                write_line(prefix + line, size=10, leading=12)

    # Education
    if req.education:
        write_line("EDUCATION", font="Helvetica-Bold", size=10, leading=16)
        for line in req.education:
            write_line("• " + line, size=10, leading=12)

    c.save()
    with open(out_path, "wb") as f:
        f.write(buf.getvalue())

    public_url = f"/files/resumes/{filename}"
    return {"pdf_url": public_url, "template": f"ats_{(req.role or 'role').lower().replace(' ', '_')}", "generated_at": timestamp}
