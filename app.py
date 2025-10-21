from flask import Flask, render_template, request, jsonify
import requests
import urllib3
import os
from google import genai
from google.genai.errors import APIError

# ปิด Warning สำหรับการเชื่อมต่อที่ไม่ได้ Verify SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# --- NEW: ตั้งค่า Gemini API Key ---
# API Key ของคุณ: AIzaSyDYNdXEKQk9_OnhuexBVkLwLQVS-coYHko
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDYNdXEKQk9_OnhuexBVkLwLQVS-coYHko") # <--- UPDATED API KEY
client = None
AI_MODEL = 'gemini-2.5-flash' 

try:
    if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_DEFAULT_API_KEY_HERE":
        client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Error initializing Gemini client: {e}. Check your GEMINI_API_KEY.")
# ----------------------------------


# --- ข้อมูลคำอธิบายเชิงลึกสำหรับ Headers ทั้งหมด (ชุดเดิม) ---
HEADER_DESCRIPTIONS = {
# ... (rest of HEADER_DESCRIPTIONS remains the same)
    'HSTS': {
        'title': 'Strict-Transport-Security (HSTS)',
        'expert_info': 'Header นี้บังคับให้เบราว์เซอร์เข้าถึงเว็บไซต์ผ่าน HTTPS เท่านั้นเพื่อป้องกันการโจมตีแบบ MITM และบังคับการใช้ SSL/TLS เพื่อความปลอดภัยสูงสุด',
        'ref_link': 'https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security'
    },
    'CSP': {
        'title': 'Content-Security-Policy (CSP)',
        'expert_info': 'Header ที่เป็นชั้นป้องกัน XSS ที่แข็งแกร่งที่สุด โดยกำหนดว่าเนื้อหาใดที่สามารถโหลดและรันบนหน้าเว็บได้ (เช่น สคริปต์, รูปภาพ, สไตล์)',
        'ref_link': 'https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy'
    },
    'X-Content-Type-Options': {
        'title': 'X-Content-Type-Options',
        'expert_info': 'การตั้งค่าเป็น "nosniff" จะป้องกันไม่ให้เบราว์เซอร์ "เดา" ประเภทของเนื้อหา (MIME type) ซึ่งเป็นช่องโหว่ที่ช่วยในการโจมตีแบบ MIME-sniffing',
        'ref_link': 'https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Content-Type-Options'
    },
    'X-Frame-Options': {
        'title': 'X-Frame-Options (XFO)',
        'expert_info': 'Header นี้ใช้ป้องกัน Clickjacking โดยควบคุมว่าหน้าเว็บสามารถถูกฝังใน <iframe>, <frame>, หรือ <object> บนโดเมนอื่นได้หรือไม่',
        'ref_link': 'https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options'
    },
    'Referrer-Policy': {
        'title': 'Referrer-Policy',
        'expert_info': 'ควบคุมปริมาณข้อมูล URL ของหน้าเว็บก่อนหน้าที่เบราว์เซอร์จะส่งไปในการ Request ใหม่ ข้อมูล Referrer สามารถมีข้อมูลที่ละเอียดอ่อนได้ จึงควรตั้งค่าให้รัดกุม',
        'ref_link': 'https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Referrer-Policy'
    },
    'Permissions-Policy': {
        'title': 'Permissions-Policy',
        'expert_info': 'Header ใหม่ที่อนุญาตให้เว็บไซต์ควบคุมและจำกัดการเข้าถึงฟีเจอร์และ API ของเบราว์เซอร์ เช่น กล้อง, ไมโครโฟน, ตำแหน่งที่ตั้ง เพื่อเสริมความปลอดภัยและความเป็นส่วนตัว',
        'ref_link': 'https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Permissions-Policy'
    },
    'COEP': {
        'title': 'Cross-Origin-Embedder-Policy (COEP)',
        'expert_info': 'Header สำคัญสำหรับการเปิดใช้งาน Cross-Origin Isolation ซึ่งป้องกันไม่ให้มีการโหลดทรัพยากรจากต่างโดเมนที่ไม่ได้รับอนุญาต เพื่อป้องกันช่องโหว่ประเภท Spectre',
        'ref_link': 'https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cross-Origin-Embedder-Policy'
    },
    'COOP': {
        'title': 'Cross-Origin-Opener-Policy (COOP)',
        'expert_info': 'Header นี้แยกหน้าต่างที่เปิดจากต่างโดเมนออกจากกัน ทำให้ไม่สามารถเข้าถึงอ็อบเจกต์ `window.opener` ได้ เพื่อป้องกันการโจมตีแบบ Tabnapping',
        'ref_link': 'https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cross-Origin-Opener-Policy'
    },
    'CORP': {
        'title': 'Cross-Origin-Resource-Policy (CORP)',
        'expert_info': 'Header นี้ช่วยให้เจ้าของทรัพยากรกำหนดว่าใครสามารถโหลดทรัพยากรนั้นได้ ซึ่งช่วยป้องกันการโจมตีแบบ Cross-Site Leaks',
        'ref_link': 'https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cross-Origin-Resource-Policy'
    },
    'Report-To': {
        'title': 'Report-To',
        'expert_info': 'Header สำหรับการกำหนด Endpoint เพื่อรับรายงานเกี่ยวกับข้อผิดพลาดของ Header หรือการละเมิดนโยบายที่เกิดขึ้นบนเบราว์เซอร์ของผู้ใช้',
        'ref_link': 'https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Report-To'
    },
    'NEL': {
        'title': 'Network Error Logging (NEL)',
        'expert_info': 'Header ที่กำหนด Endpoint เพื่อให้เบราว์เซอร์ส่งรายงานเกี่ยวกับความล้มเหลวของเครือข่ายกลับไปยังเซิร์ฟเวอร์',
        'ref_link': 'https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/NEL'
    },
    'Server': {
        'title': 'Server Header',
        'expert_info': 'Header ที่มักจะเปิดเผยข้อมูลเกี่ยวกับซอฟต์แวร์เซิร์ฟเวอร์ที่ใช้อยู่ ควรถูกซ่อน (Obfuscated) เพื่อป้องกันการโจมตีแบบ Fingerprinting',
        'ref_link': ''
    },
}
# ----------------------------------------------------------------------


# ฟังก์ชันหลักในการวิเคราะห์และให้เกรด (ใช้โค้ดเดิม)
def analyze_headers(headers):
# ... (rest of analyze_headers remains the same)
    score = 0
    results = {}
    
    # 1. Strict-Transport-Security (HSTS) - 20 คะแนน
    hsts = headers.get('Strict-Transport-Security')
    if hsts and 'max-age' in hsts and int(hsts.split('max-age=')[1].split(';')[0].strip()) >= 31536000:
        score += 20
        results['HSTS'] = {'status': 'PASS', 'value': hsts, 'info': 'HSTS ถูกตั้งค่าอย่างถูกต้องและมี max-age ≥ 1 ปี'}
    else:
        results['HSTS'] = {'status': 'FAIL', 'value': hsts, 'info': 'ควรตั้งค่า HSTS ให้มี max-age ≥ 1 ปี และควรมี includeSubDomains'}

    # 2. Content-Security-Policy (CSP) - 20 คะแนน
    csp = headers.get('Content-Security-Policy')
    if csp:
        if 'unsafe-inline' not in csp.lower() and 'unsafe-eval' not in csp.lower():
            score += 20
            results['CSP'] = {'status': 'PASS', 'value': csp, 'info': 'CSP ถูกตั้งค่าแล้ว และตั้งค่าได้ดี'}
        else:
            score += 10
            # แยกสถานะเป็น WARNING เมื่อ Header อยู่ แต่ค่าไม่ปลอดภัย
            results['CSP'] = {'status': 'WARN', 'value': csp, 'info': 'CSP ถูกตั้งค่า แต่มีคำสั่งที่อันตราย (unsafe-inline/unsafe-eval)'}
    else:
        results['CSP'] = {'status': 'FAIL', 'value': 'NOT FOUND', 'info': 'ไม่มี Content-Security-Policy!'}

    # 3. X-Content-Type-Options - 10 คะแนน
    xcto = headers.get('X-Content-Type-Options')
    if xcto == 'nosniff':
        score += 10
        results['X-Content-Type-Options'] = {'status': 'PASS', 'value': xcto, 'info': 'ป้องกันการเดา Content Type'}
    else:
        results['X-Content-Type-Options'] = {'status': 'FAIL', 'value': xcto, 'info': 'ควรตั้งค่าเป็น nosniff'}

    # 4. X-Frame-Options - 10 คะแนน
    xfo = headers.get('X-Frame-Options')
    if xfo in ['DENY', 'SAMEORIGIN']:
        score += 10
        results['X-Frame-Options'] = {'status': 'PASS', 'value': xfo, 'info': 'ป้องกัน Clickjacking'}
    else:
        results['X-Frame-Options'] = {'status': 'FAIL', 'value': xfo, 'info': 'ควรตั้งค่าเป็น DENY หรือ SAMEORIGIN'}

    # 5. Referrer-Policy - 10 คะแนน
    rp = headers.get('Referrer-Policy')
    if rp in ['no-referrer', 'same-origin', 'strict-origin-when-cross-origin']:
        score += 10
        results['Referrer-Policy'] = {'status': 'PASS', 'value': rp, 'info': 'ตั้งค่าเพื่อควบคุมการส่งข้อมูล Referrer'}
    else:
        results['Referrer-Policy'] = {'status': 'FAIL', 'value': rp, 'info': 'ควรตั้งค่า Referrer-Policy ที่ปลอดภัย'}

    # 6. Permissions-Policy - 10 คะแนน
    pp = headers.get('Permissions-Policy')
    if pp and (not pp.strip() or '()' in pp):
        score += 10
        results['Permissions-Policy'] = {'status': 'PASS', 'value': pp, 'info': 'Permissions-Policy ถูกตั้งค่าและปิดการเข้าถึงฟีเจอร์ที่ไม่จำเป็น'}
    elif pp:
        # แยกสถานะเป็น WARNING เมื่อ Header อยู่ แต่ค่าไม่เข้มงวดพอ
        results['Permissions-Policy'] = {'status': 'WARN', 'value': pp, 'info': 'Permissions-Policy ถูกตั้งค่า แต่ควรจำกัดฟีเจอร์ที่ไม่จำเป็นให้เข้มงวดกว่านี้'}
    else:
        results['Permissions-Policy'] = {'status': 'FAIL', 'value': 'NOT FOUND', 'info': 'ควรตั้งค่า Permissions-Policy เพื่อจำกัดการเข้าถึง API'}

    # 7. Cross-Origin-Embedder-Policy (COEP) - 10 คะแนน
    coep = headers.get('Cross-Origin-Embedder-Policy')
    if coep == 'require-corp':
        score += 10
        results['COEP'] = {'status': 'PASS', 'value': coep, 'info': 'ตั้งค่า COEP เป็น require-corp เพื่อเปิดใช้งาน Cross-Origin Isolation'}
    else:
        results['COEP'] = {'status': 'FAIL', 'value': coep, 'info': 'ควรตั้งค่า COEP เป็น require-corp'}

    # 8. Cross-Origin-Opener-Policy (COOP) - 5 คะแนน
    coop = headers.get('Cross-Origin-Opener-Policy')
    if coop in ['same-origin', 'same-origin-allow-popups']:
        score += 5
        results['COOP'] = {'status': 'PASS', 'value': coop, 'info': 'ตั้งค่า COOP อย่างถูกต้องเพื่อป้องกัน Tabnabbing'}
    else:
        results['COOP'] = {'status': 'FAIL', 'value': coop, 'info': 'ควรตั้งค่า COOP เป็น same-origin'}
        
    # 9. Cross-Origin-Resource-Policy (CORP) - 5 คะแนน
    corp = headers.get('Cross-Origin-Resource-Policy')
    if corp in ['same-origin', 'same-site']:
        score += 5
        results['CORP'] = {'status': 'PASS', 'value': corp, 'info': 'ตั้งค่า CORP เป็น same-origin/same-site เพื่อป้องกัน Cross-Site Leaks'}
    elif corp == 'cross-origin':
        results['CORP'] = {'status': 'WARN', 'value': corp, 'info': 'ตั้งค่า CORP เป็น cross-origin ซึ่งมีความเสี่ยงสูงกว่า same-origin/same-site'}
    else:
        results['CORP'] = {'status': 'FAIL', 'value': corp, 'info': 'ควรตั้งค่า CORP ที่เหมาะสม'}

    # 10. Report-To และ NEL (ไม่นับคะแนน แต่มีการวิเคราะห์)
    results['Report-To'] = {'status': 'WARN' if headers.get('Report-To') else 'FAIL', 
                            'value': headers.get('Report-To') or 'NOT FOUND', 
                            'info': 'แนะนำให้ตั้งค่า Report-To เพื่อรับรายงานข้อผิดพลาด'}
    
    results['NEL'] = {'status': 'WARN' if headers.get('NEL') else 'FAIL', 
                      'value': headers.get('NEL') or 'NOT FOUND', 
                      'info': 'แนะนำให้ตั้งค่า Network Error Logging (NEL) เพื่อตรวจสอบปัญหาเครือข่าย'}

    # 11. Server Header (ไม่นับคะแนน)
    server = headers.get('Server')
    if server:
        # แยกสถานะเป็น WARNING เมื่อ Header อยู่และเปิดเผยข้อมูล
        results['Server'] = {'status': 'WARN', 'value': server, 'info': 'Server Header ถูกเปิดเผย ควรพิจารณาซ่อนเพื่อป้องกัน Fingerprinting'}
    else:
        results['Server'] = {'status': 'PASS', 'value': 'OBFUSCATED/NOT FOUND', 'info': 'Server Header ถูกซ่อนอย่างเหมาะสม'}

    # สรุปเกรด
    if score >= 90: grade = 'A+'
    elif score >= 80: grade = 'A'
    elif score >= 65: grade = 'B'
    elif score >= 50: grade = 'C'
    else: grade = 'F'

    return {'grade': grade, 'score': score, 'details': results}

# Route สำหรับหน้าแรก
@app.route('/')
def index():
    return render_template('index.html')

# Route สำหรับการสแกน (ใช้โค้ดเดิม)
@app.route('/scan', methods=['POST'])
def scan():
# ... (rest of scan remains the same)
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "กรุณาใส่ URL"}), 400

    if not url.startswith(('http://', 'https://')):
        url_to_fetch = 'https://' + url
    else:
        url_to_fetch = url
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(
            url_to_fetch, 
            allow_redirects=True, 
            timeout=15, 
            headers=headers,
            verify=False 
        )
        
        if response.status_code >= 400 and response.status_code != 404:
            return jsonify({
                "success": False, 
                "error": f"การเชื่อมต่อสำเร็จ แต่เซิร์ฟเวอร์ปฏิเสธการเข้าถึง (HTTP Status Code: {response.status_code})"
            }), 500

        analysis_result = analyze_headers(response.headers)
        
        return jsonify({
            'success': True,
            'url': url_to_fetch,
            'status_code': response.status_code,
            'result': analysis_result,
            'raw_headers': dict(response.headers),
            'descriptions': HEADER_DESCRIPTIONS
        })

    except requests.exceptions.Timeout:
        return jsonify({"success": False, "error": "การเชื่อมต่อหมดเวลา (Timeout). เว็บไซต์โหลดช้าเกินไป."}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"Network/Connection Error: ไม่สามารถเชื่อมต่อได้: {e}"}), 500

# --- NEW: Route สำหรับเรียกใช้ AI เพื่อหาโค้ดแก้ไข (ปรับปรุง Prompt) ---
@app.route('/suggest_fix', methods=['POST'])
def suggest_fix():
# ... (rest of suggest_fix remains the same)
    data = request.get_json()
    header_name = data.get('header_name')
    current_value = data.get('current_value')
    analysis_info = data.get('analysis_info')
    
    # ตรวจสอบการเริ่มต้น Client
    if not client or not AI_MODEL:
        return jsonify({
            "success": False,
            "error": "Gemini AI Client is not initialized. Please ensure GEMINI_API_KEY is set correctly."
        }), 500
        
    if not header_name:
        return jsonify({"success": False, "error": "Missing header_name"}), 400

    # Prompt ที่ปรับปรุง: ต้องการคำอธิบายและโค้ด 3 รูปแบบ (Nginx, Apache, Node.js/Python/PHP)
    prompt = f"""
    You are an expert web security consultant. The following security header was analyzed:
    Header Name: {header_name}
    Current Value: {current_value or 'MISSING'}
    Analysis Result: {analysis_info}

    Provide the **best secure configuration** for this header. Your response MUST be structured as follows:

    1. A brief Thai explanation (1-2 sentences) of why this header is important and what the suggested fix does.
    2. A suggested configuration line in **Nginx** format (using `add_header`).
    3. A suggested configuration line in **Apache (.htaccess or httpd.conf)** format (using `Header always set`).
    4. A suggested configuration line in a **Node.js (Express) or similar backend framework (Python/PHP)** format.

    Enclose each type of suggested code (Nginx, Apache, Backend) in a separate, labeled markdown code block. Do not add any extra text or code outside the explanation and the three code blocks.

    Example Output Structure:
    [Explanation Text]
    ```nginx
    add_header Content-Security-Policy "default-src 'self'; frame-ancestors 'self'; object-src 'none';";
    ```
    ```apache
    Header always set Content-Security-Policy "default-src 'self'; frame-ancestors 'self'; object-src 'none';"
    ```
    ```javascript
    res.setHeader('Content-Security-Policy', "default-src 'self'; frame-ancestors 'self'; object-src 'none';");
    ```
    """

    try:
        response = client.models.generate_content(
            model=AI_MODEL,
            contents=prompt
        )
        
        return jsonify({
            "success": True,
            "suggestion": response.text
        })

    except APIError as e:
        return jsonify({
            "success": False,
            "error": f"Gemini API Error: {e}. (API Key or quota issue)."
        }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"An unexpected error occurred: {e}"
        }), 500


if __name__ == '__main__':
    app.run(debug=True)