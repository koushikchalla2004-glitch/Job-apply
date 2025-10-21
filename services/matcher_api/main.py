from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import re

app = FastAPI(title="Matcher API", version="0.1.0")

class MatchRequest(BaseModel):
    jd_text: str
    profile_skills: List[str]

class MatchResponse(BaseModel):
    score: float
    skills_found: List[str]
    email_found: Optional[str] = None

EMAIL_REGEX = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/parse_and_score", response_model=MatchResponse)
def parse_and_score(req: MatchRequest):
    jd_lower = req.jd_text.lower()
    hits = [s for s in req.profile_skills if s.lower() in jd_lower]
    score = round(len(hits) / max(len(req.profile_skills), 1), 2)
    m = re.search(EMAIL_REGEX, req.jd_text)
    email = m.group(0) if m else None
    return MatchResponse(score=score, skills_found=hits, email_found=email)
