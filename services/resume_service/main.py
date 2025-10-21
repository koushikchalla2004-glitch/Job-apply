from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import os


app = FastAPI(title="Resume Service", version="0.1.0")

origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS","*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BuildReq(BaseModel):
    role: str
    jd_skills: List[str]
    name: str = "Your Name"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/build_resume")
def build_resume(req: BuildReq):
    return {
        "pdf_path": "/storage/resumes/sample.pdf",
        "txt_path": "/storage/resumes/sample.txt",
        "template": f"ats_{req.role.lower().replace(' ', '_')}"
    }
