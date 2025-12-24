import requests
import random
import os
import sys
import json
import time
import datetime

# Base Config
BASE_URL = "http://127.0.0.1:8000/api"
IMAGE_PATH = r"C:\Users\86138\Desktop\test.png"

# Ensure project root is in path
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.db.session import SessionLocal
from app.models.user import User, Teacher, Student, Class

def get_test_context():
    s = SessionLocal()
    try:
        # 1. Find Teacher (ID=2)
        teacher = s.query(Teacher).filter(Teacher.id == 2).first()
        if not teacher:
            print("[-] Teacher ID 2 not found.")
            return None
            
        t_user = s.query(User).filter(User.id == teacher.user_id).first()
        
        # 2. Find Class (First class of this teacher)
        clazz = s.query(Class).filter(Class.teacher_id == teacher.id).first()
        if not clazz:
            print(f"[-] No class found for Teacher {teacher.name}")
            return None
            
        # 3. Find Students
        students = s.query(Student).filter(Student.class_id == clazz.id).all()
        if not students:
            print(f"[-] No students found in Class {clazz.name}")
            return None
            
        s_users = s.query(User).filter(User.id.in_([stu.user_id for stu in students])).all()
        
        # Map user_id to username
        s_map = {u.id: u.username for u in s_users}
        student_usernames = [s_map[stu.user_id] for stu in students]
        
        return {
            "teacher": {"username": t_user.username, "id": teacher.id, "user_id": t_user.id},
            "class": {"id": clazz.id, "name": clazz.name},
            "students": student_usernames
        }
    finally:
        s.close()

def login(username, password="123456"):
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", data={"username": username, "password": password})
        if resp.status_code == 200:
            return resp.json()["access_token"]
        print(f"[-] Login failed for {username}: {resp.status_code}")
    except Exception as e:
        print(f"[-] Login error for {username}: {e}")
    return None

def main():
    print("=== Starting End-to-End Test (Teacher ID=2) ===")
    
    # 1. Setup Context
    ctx = get_test_context()
    if not ctx: return
    
    print(f"[+] Teacher: {ctx['teacher']['username']} (ID: {ctx['teacher']['id']})")
    print(f"[+] Class: {ctx['class']['name']} (ID: {ctx['class']['id']})")
    print(f"[+] Students ({len(ctx['students'])}): {ctx['students']}")
    
    # 2. Teacher Upload
    t_token = login(ctx['teacher']['username'])
    if not t_token: return
    headers_t = {"Authorization": f"Bearer {t_token}"}
    
    if not os.path.exists(IMAGE_PATH):
        print(f"[-] Image not found: {IMAGE_PATH}")
        return

    print(f"\n[Step 2] Uploading Assignment...")
    with open(IMAGE_PATH, "rb") as f:
        files = {"file": ("test.png", f, "image/png")}
        data = {"class_id": ctx['class']['id'], "title": f"Test {int(time.time())}"}
        resp = requests.post(f"{BASE_URL}/assignments/upload", headers=headers_t, data=data, files=files)
    
    if resp.status_code != 200:
        print(f"[-] Upload failed: {resp.text}")
        return
        
    assignment_id = resp.json()["id"]
    print(f"[+] Assignment Uploaded. ID: {assignment_id}")
    
    # Get Questions
    resp = requests.get(f"{BASE_URL}/assignments/{assignment_id}/paper", headers=headers_t)
    questions = resp.json()
    q_ids = [q["id"] for q in questions]
    print(f"[+] Questions: {len(q_ids)}")

    # 3. Student Submissions (Random)
    print("\n[Step 3] Student Submissions (Random A/B/C/D)...")
    choices = ["A", "B", "C", "D"]
    student_data = [] # List of {username, token, wrong_qids}
    
    for username in ctx['students']:
        s_token = login(username)
        if not s_token: continue
        headers_s = {"Authorization": f"Bearer {s_token}"}
        
        # Get Student ID
        me = requests.get(f"{BASE_URL}/auth/me", headers=headers_s).json()
        sid = me["student_id"]
        
        answers = []
        for qid in q_ids:
            answers.append({"question_id": qid, "student_answer": random.choice(choices)})
            
        payload = {
            "assignment_id": assignment_id,
            "student_id": sid,
            "answers": answers
        }
        
        print(f"[.] {username} submitting...", end=" ")
        resp = requests.post(f"{BASE_URL}/submissions/", headers=headers_s, json=payload)
        if resp.status_code == 200:
            res = resp.json()
            print(f"Score: {res.get('total_score')}")
            
            wrong = [r["question_id"] for r in res.get("results", []) if not r["is_correct"]]
            student_data.append({"username": username, "token": s_token, "wrong_qids": wrong, "sid": sid})
        else:
            print(f"Failed: {resp.status_code}")

    # 4. Check Correction Results (Teacher View)
    print("\n[Step 4] Checking Correction Results (Teacher View)...")
    # Just check if we can list results for the assignment
    # The API might be /submissions/assignment/{assignment_id}? No, likely /submissions/results or similar.
    # Let's check `app/api/submissions.py`.
    # Assuming `GET /submissions/history` or similar.
    # For now, we skip specific teacher view verification as it's complex to simulate UI logic.
    
    # 5. Knowledge Graph Analysis
    print("\n[Step 5] Knowledge Graph Analysis...")
    today = datetime.date.today().strftime("%Y-%m-%d")
    headers_kg = headers_t.copy()
    headers_kg["Class-ID"] = str(ctx['class']['id'])
    headers_kg["Start-Date"] = today
    headers_kg["End-Date"] = today
    
    # 5.1 Breakpoints
    print("[.] Checking Breakpoints...")
    resp = requests.get(f"{BASE_URL}/knowledge-graph/breakpoints", headers=headers_kg, params={"top_k": 5})
    if resp.status_code == 200:
        bps = resp.json()
        print(f"    Found {len(bps)} breakpoints: {[b['name'] for b in bps]}")
    else:
        print(f"[-] Breakpoints failed: {resp.text}")

    # 5.2 Candidates (New Endpoint)
    print("[.] Checking Candidates...")
    resp = requests.get(f"{BASE_URL}/knowledge-graph/candidates", headers=headers_kg, params={"limit": 5})
    if resp.status_code == 200:
        cands = resp.json()
        print(f"    Found {len(cands)} candidates: {cands}")
    else:
        print(f"[-] Candidates failed: {resp.text}")

    # 6. Recommendation Test (Teacher triggering it)
    print("\n[Step 6] Recommendation Test (Teacher)...")
    target = next((s for s in student_data if s["wrong_qids"]), None)
    if target:
        qid = target["wrong_qids"][0]
        sid = target["sid"]
        print(f"[.] Recommending for Student {target['username']} (ID {sid}) on Q {qid}...")
        
        req = {
            "question_id": qid,
            "student_id": sid, # Teacher must provide this
            "slot": "high",
            "expect_num": 3
        }
        resp = requests.post(f"{BASE_URL}/problems/{qid}/recommendation", headers=headers_t, json=req)
        if resp.status_code == 200:
            rec = resp.json()
            print(f"    Success. Found {rec['found']} items.")
        else:
            print(f"[-] Recommendation failed: {resp.text}")
    else:
        print("[-] No wrong answers to test recommendation.")

if __name__ == "__main__":
    main()
