import os
import requests
import json
from flask import Flask, request, jsonify
from google import genai
from google.genai import types

# --- 1. การตั้งค่า Flask และ Gemini ---
app = Flask(__name__)

# ใช้ Environment Variable สำหรับ API Key (สำคัญมากด้านความปลอดภัย)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 🔴 FIX: Hardcode Key ชั่วคราวสำหรับการทดสอบบน Local PC
# 🔴 ลบ 3 บรรทัดนี้ก่อน COMMIT & PUSH ขึ้น Render/Production!
if not GEMINI_API_KEY:
    GEMINI_API_KEY = "AIzaSyARP5crkNC_WxLuPI6OI8mRdyHB5wjPFg4"
    print("Warning: GEMINI_API_KEY was hardcoded for testing. REMOVE THIS CODE BEFORE DEPLOYMENT.")
# --------------------------------------------------------------------------

try:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")
    
    # Initialize Gemini Client
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Error initializing Gemini: {e}")
    client = None

# --- 2. ฟังก์ชันการวิเคราะห์หลัก (The 'Fix-it Summary') ---
def analyze_with_gemini(scan_results):
    """ใช้ Gemini เพื่อวิเคราะห์ผลการสแกนและสร้างบทสรุปที่นำไปปฏิบัติได้"""
    
    # Prompt สำหรับ Gemini (กำหนด Output เป็น JSON Object)
    prompt = f"""
    คุณคือผู้เชี่ยวชาญด้านความปลอดภัยเว็บ (Web Security Expert) ที่สุภาพและเป็นมิตร
    โปรดวิเคราะห์ผลการสแกน HTTP Security Headers ต่อไปนี้ และสร้างบทสรุปที่เน้น
    "สิ่งที่ต้องทำ 3 ขั้นตอน" เพื่อปรับปรุงความปลอดภัยให้ดีที่สุด

    ภาษาที่ใช้: ภาษาไทย
    รูปแบบผลลัพธ์: JSON Object เท่านั้น มี 3 Keys คือ 'summary_th', 'risk_th', และ 'actionable_steps'
    - 'summary_th': สรุปสถานะความปลอดภัยใน 1-2 ประโยค
    - 'risk_th': การประเมินความเสี่ยงโดยรวม (ต่ำ/ปานกลาง/สูง)
    - 'actionable_steps': รายการ (Array) ของ 3 ขั้นตอนสำคัญที่ต้องทำทันทีเพื่อแก้ไขปัญหาที่ตรวจพบ

    ผลลัพธ์การสแกน:
    {json.dumps(scan_results, indent=2)}
    """
    
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema={"type": "object"}
    )
    
    try:
        if not client:
            print("Gemini Client is not initialized. Skipping analysis.")
            return {"summary_th": "ไม่สามารถวิเคราะห์ด้วย AI ได้", "risk_th": "N/A", "actionable_steps": ["ตรวจสอบ GEMINI_API_KEY"]}
            
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=config,
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return None

# --- 3. Flask Routes ---

@app.route('/')
def index():
    """แสดงหน้าเว็บหลัก"""
    # ต้องมีไฟล์ index.html ในโฟลเดอร์เดียวกัน
    return open('index.html').read()

@app.route('/scan', methods=['POST'])
def scan_url():
    """Endpoint สำหรับรับ URL และเริ่มการสแกน/วิเคราะห์"""
    
    data = request.json
    url_to_scan = data.get('url')
    
    if not url_to_scan:
        return jsonify({"error": "Missing URL"}), 400

    # User-Agent Rotation (สุ่ม User-Agent เพื่อหลีกเลี่ยงการถูกบล็อก)
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    ]
    
    # ใช้ hash ของ URL เพื่อ "สุ่ม" User-Agent อย่างคงที่ (เพื่อให้ Request ซ้ำๆ ดูเหมือนกัน)
    headers = {
        'User-Agent': user_agents[hash(url_to_scan) % len(user_agents)],
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Cache-Control': 'no-cache'
    }

    try:
        # ส่ง Request ไปยังเว็บไซต์เป้าหมาย
        response = requests.get(url_to_scan, headers=headers, timeout=10, allow_redirects=True)
        
        # 2. การประมวลผล Header
        security_headers = {
            "Content-Security-Policy": response.headers.get("Content-Security-Policy"),
            "Strict-Transport-Security": response.headers.get("Strict-Transport-Security"),
            "X-Content-Type-Options": response.headers.get("X-Content-Type-Options"),
            "X-Frame-Options": response.headers.get("X-Frame-Options"),
            "Referrer-Policy": response.headers.get("Referrer-Policy"),
            "Permissions-Policy": response.headers.get("Permissions-Policy"),
        }
        
        # ตรวจสอบสถานะการถูกบล็อก/ล้มเหลว
        if response.status_code >= 400:
            return jsonify({
                "error": f"Scan Failed: Server returned status code {response.status_code}. (Possible block or not reachable)",
                "status_code": response.status_code,
                "raw_headers": dict(response.headers)
            }), 400

        # 3. การวิเคราะห์ด้วย Gemini
        gemini_analysis = analyze_with_gemini(security_headers)
        
        # 4. ส่งผลลัพธ์ทั้งหมดกลับไป Frontend
        return jsonify({
            "status": "success",
            "headers": security_headers,
            "raw_headers": dict(response.headers),
            "gemini_analysis": gemini_analysis
        })

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out after 10 seconds."}), 408
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"An error occurred during connection: {e}"}), 400