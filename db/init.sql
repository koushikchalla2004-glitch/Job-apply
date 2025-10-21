CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, source TEXT, company TEXT, title TEXT, location TEXT, url TEXT, raw_json JSONB, ats_type TEXT, contact_email TEXT, found_at TIMESTAMP DEFAULT now());
CREATE TABLE IF NOT EXISTS job_matches (job_id TEXT REFERENCES jobs(id) ON DELETE CASCADE, match_score NUMERIC, reasons JSONB, created_at TIMESTAMP DEFAULT now());
CREATE TABLE IF NOT EXISTS resumes (id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), role TEXT, template TEXT, pdf_path TEXT, txt_path TEXT, created_at TIMESTAMP DEFAULT now());
CREATE TABLE IF NOT EXISTS applications (id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), job_id TEXT REFERENCES jobs(id) ON DELETE CASCADE, resume_id UUID REFERENCES resumes(id) ON DELETE SET NULL, channel TEXT, status TEXT, sent_at TIMESTAMP, meta JSONB);
CREATE TABLE IF NOT EXISTS events (id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), job_id TEXT, type TEXT, detail JSONB, created_at TIMESTAMP DEFAULT now());
