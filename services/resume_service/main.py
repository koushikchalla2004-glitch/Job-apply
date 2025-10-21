from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Resume Service", version="0.1.0")

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
