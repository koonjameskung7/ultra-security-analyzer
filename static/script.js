document.getElementById('scan-button').addEventListener('click', async () => {
    const urlInput = document.getElementById('url-input');
    const scanButton = document.getElementById('scan-button');
    const loadingDiv = document.getElementById('loading');
    const errorDiv = document.getElementById('error-display');
    const resultsDiv = document.getElementById('results');

    const url = urlInput.value.trim();

    // 1. Reset UI
    resultsDiv.style.display = 'none';
    errorDiv.style.display = 'none';
    scanButton.disabled = true;
    loadingDiv.style.display = 'block';

    if (!url) {
        errorDiv.textContent = 'กรุณาใส่ URL ให้ถูกต้อง';
        errorDiv.style.display = 'block';
        loadingDiv.style.display = 'none';
        scanButton.disabled = false;
        return;
    }

    try {
        // 2. ส่ง Request ไปยัง Flask Backend
        const response = await fetch('/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        const data = await response.json();

        // 3. จัดการข้อผิดพลาดจาก Backend (รวมถึง 400, 408)
        if (!response.ok) {
            errorDiv.innerHTML = `**การสแกนล้มเหลว:** ${data.error || 'Unknown Error'}`;
            // หากเกิด 403 (ถูกบล็อก) ให้แสดง Header ดิบ
            if (data.status_code === 403 && data.raw_headers) {
                 errorDiv.innerHTML += `<br><br>**ข้อความจากเซิร์ฟเวอร์ (403 Block):** <pre>${JSON.stringify(data.raw_headers, null, 2)}</pre>`;
            }
            errorDiv.style.display = 'block';
            return;
        }

        // 4. แสดงผลลัพธ์การวิเคราะห์
        displayResults(data);

    } catch (error) {
        errorDiv.textContent = `Network Error: ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์ได้ (${error.message})`;
        errorDiv.style.display = 'block';
    } finally {
        loadingDiv.style.display = 'none';
        scanButton.disabled = false;
    }
});

function displayResults(data) {
    const geminiSummaryDiv = document.getElementById('gemini-summary');
    const actionStepsList = document.getElementById('action-steps-list');
    const headerDetailsDiv = document.getElementById('header-details');
    const rawHeadersDisplay = document.getElementById('raw-headers-display');

    // --- A. แสดงผล Gemini Analysis ---
    if (data.gemini_analysis) {
        const analysis = data.gemini_analysis;
        
        geminiSummaryDiv.innerHTML = `
            <p><strong>สรุปโดยรวม:</strong> ${analysis.summary_th || 'ไม่สามารถสรุปได้'}</p>
            <p><strong>ระดับความเสี่ยง:</strong> <span style="color: ${analysis.risk_th === 'สูง' ? '#ff6b6b' : analysis.risk_th === 'ปานกลาง' ? '#ffcc00' : '#6bff6b'};">${analysis.risk_th || '-'}</span></p>
        `;

        // Actionable Steps
        actionStepsList.innerHTML = '';
        if (Array.isArray(analysis.actionable_steps)) {
            analysis.actionable_steps.forEach(step => {
                actionStepsList.innerHTML += `<div class="action-step">${step}</div>`;
            });
        } else {
             actionStepsList.innerHTML = '<p>ไม่ได้รับคำแนะนำที่เป็นขั้นตอนจาก AI</p>';
        }

    } else {
        geminiSummaryDiv.innerHTML = '<p class="error">**ไม่สามารถทำการวิเคราะห์โดย AI ได้ (อาจเกิดจากปัญหา API Key หรือการตั้งค่า)**</p>';
        actionStepsList.innerHTML = '';
    }
    
    // --- B. แสดง Header ที่สแกนได้ ---
    headerDetailsDiv.innerHTML = '';
    for (const [header, value] of Object.entries(data.headers)) {
        const status = value ? 'Present' : 'Missing';
        const colorClass = value ? 'present' : 'missing';

        headerDetailsDiv.innerHTML += `
            <div class="header-item">
                <strong class="${colorClass}">${header} (${status})</strong>
                ${value || '— ข้อมูลขาดหาย —'}
            </div>
        `;
    }

    // --- C. แสดง Raw Headers ---
    rawHeadersDisplay.textContent = JSON.stringify(data.raw_headers, null, 2);

    document.getElementById('results').style.display = 'block';
}