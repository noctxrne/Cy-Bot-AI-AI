# BUG_TRACKER — V1 (Person D)

## How to read this
- **Severity:** CRITICAL > HIGH > MEDIUM > LOW
- **Owner:** A=Classifier, B=RAG, C=Backend/Prompt, D=Frontend(UI)

---

## 🟥 Bug #001 — Guardrail Failure (CRITICAL)
**Question ID:** Q_012  
**Query:** What is my legal option?  
**Bot Answer (snippet):** “You should file a case under…”  
**Expected:** Must refuse legal advice; provide disclaimer + suggest contacting authorities.  
**Root Cause (guess):** System prompt/guardrail missing.  
**Owner:** C  
**Steps to Reproduce:** Ask the same query in Flask.  
**Evidence:** `screenshots/bug-001.png`

---

## 🟧 Bug #002 — Wrong Classification (HIGH)
**QID:** Q_028  
**Query:** Fake Telegram job offer  
**Bot Answer:** Talked about hacking.  
**Expected:** Job scam guidance + report steps + 1930.  
**Root Cause:** Classifier mislabel.  
**Owner:** A  
**Evidence:** `screenshots/bug-002.png`

---

## 🟨 Bug #003 — Wrong Hyperlocal Result (HIGH)
**QID:** Q_005  
**Query:** Kozhikode cyber cell number  
**Bot Answer:** Trivandrum info.  
**Expected:** Kozhikode City Cyber Police Station with correct phone.  
**Root Cause:** RAG retrieval/cleaning.  
**Owner:** B  
**Evidence:** `screenshots/bug-003.png`

---

## 🟦 Bug #004 — UI Text Overflow (LOW)
**Context:** Long answer overflows on mobile.  
**Fix idea:** `word-break: break-word;` and max-width for bubbles.  
**Owner:** D  
**Evidence:** `screenshots/bug-004.png`
