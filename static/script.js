// script.js

// ... (โค้ดส่วนบน document.getElementById('scanForm')... เดิม)
document.getElementById('scanForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const urlInput = document.getElementById('urlInput');
    const url = urlInput.value.trim();
    const resultsDiv = document.getElementById('results');
    const loadingDiv = document.getElementById('loading');
    const errorDiv = document.getElementById('error');
    
    // Reset UI
    resultsDiv.style.display = 'none';
    errorDiv.style.display = 'none';
    
    if (!url) {
        errorDiv.textContent = 'กรุณาใส่ URL เพื่อทำการสแกน';
        errorDiv.style.display = 'block';
        return;
    }

    loadingDiv.style.display = 'flex';

    try {
        const response = await fetch('/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });
        
        const data = await response.json();

        loadingDiv.style.display = 'none';

        if (data.success) {
            // Update Score & Rank
            animateScore(data.result.score);
            document.getElementById('overallRank').textContent = `Rank: ${data.result.grade}`;
            updateRiskLevel(data.result.score);
            
            // Populate Header Details (General & Expert Views)
            renderHeaders('headerDetails', data.result.details, 'general', data.raw_headers, data.descriptions); 
            renderHeaders(null, data.result.details, 'expert', data.raw_headers, data.descriptions); 
            
            // Populate Raw Headers Table
            renderRawHeadersTable(data.raw_headers);

            resultsDiv.style.display = 'block';
            
        } else {
            errorDiv.textContent = data.error || 'เกิดข้อผิดพลาดในการสแกน';
            errorDiv.style.display = 'block';
        }

    } catch (error) {
        loadingDiv.style.display = 'none';
        errorDiv.textContent = 'Network Error: ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์ Flask ได้';
        errorDiv.style.display = 'block';
    }
});


// --- ฟังก์ชัน Render Header Items (ปรับปรุงเพื่อแยก General/Expert ชัดเจน) ---
function renderHeaders(targetElementId, details, viewType, rawHeaders = {}, descriptions = {}) {
    
    const statusMapping = {
        'PASS': { status: 'PRESENT', color: 'var(--success-green)', icon: '☑️', group: 'passGroup' },
        'FAIL': { status: 'MISSING', color: 'var(--danger-red)', icon: '❌', group: 'missingGroup' },
        'WARN': { status: 'WARNING', color: 'var(--warning-orange)', icon: '⚠️', group: 'warnGroup' } 
    };

    if (viewType === 'general') {
        const targetElement = document.getElementById(targetElementId);
        if (!targetElement) return;
        targetElement.innerHTML = ''; 
    } else if (viewType === 'expert') {
        // ล้าง Expert View ทุก Group ก่อน Render ใหม่
        document.getElementById('passGroup').innerHTML = '';
        document.getElementById('warnGroup').innerHTML = '';
        document.getElementById('missingGroup').innerHTML = '';
    }
    
    
    Object.keys(details).forEach(key => {
        const detail = details[key];
        const displayKey = descriptions[key] ? descriptions[key].title : key; 
        const uiStatus = statusMapping[detail.status];
        
        if (uiStatus) { 
            const item = document.createElement('div');
            let infoText;
            // ใช้ค่า Header ที่ได้รับจริง หรือคำว่า 'NOT FOUND'
            let headerValue = rawHeaders[key] || detail.value || 'NOT SET/UNKNOWN'; 
            const expertInfo = descriptions[key] ? descriptions[key].expert_info : 'No detailed explanation available.';
            
            // ----------------------------------------------------------------
            // 1. โค้ดสำหรับ General View (มุมมองทั่วไป - แสดงแค่สรุป)
            // ----------------------------------------------------------------
            if (viewType === 'general') {
                item.className = 'header-item';
                
                infoText = `<p class="header-info-text">${detail.info}</p>`;
                
                item.innerHTML = `
                    <div class="header-title">
                        <span style="color: ${uiStatus.color}; margin-right: 10px;">${uiStatus.icon}</span>
                        <span>${displayKey}</span>
                        <span class="header-status-text status-${uiStatus.status}">${uiStatus.status}</span>
                    </div>
                    ${infoText}
                `;
                document.getElementById(targetElementId).appendChild(item);


            // ----------------------------------------------------------------
            // 2. โค้ดสำหรับ Expert View (มุมมองผู้เชี่ยวชาญ - แสดงละเอียดและปุ่ม AI)
            // ----------------------------------------------------------------
            } else if (viewType === 'expert') {
                
                // สร้างปุ่ม Suggest Fix สำหรับ FAIL หรือ WARN
                let fixButtonHtml = '';
                if (detail.status === 'FAIL' || detail.status === 'WARN') {
                    // Encode ค่าเพื่อป้องกันปัญหา quote ใน HTML attribute
                    const encodedCurrentValue = headerValue.replace(/"/g, "'").replace(/\n/g, ' '); 
                    const encodedAnalysisInfo = detail.info.replace(/"/g, "'");

                    fixButtonHtml = `
                        <button 
                            class="suggest-fix-button"
                            data-header-name="${key}"
                            data-current-value="${encodedCurrentValue}"
                            data-analysis-info="${encodedAnalysisInfo}"
                        >
                            💡 Suggest Fix (แก้ไขด้วย AI)
                        </button>
                    `;
                }
                
                item.className = `expert-header-item ${detail.status}`; 
                infoText = `<p class="header-info-text">
                                **สถานะโดยรวม:** <span style="color: ${uiStatus.color};">${uiStatus.status}</span><br>
                                **การวิเคราะห์เบื้องต้น:** ${detail.info}
                            </p>
                            <p class="header-info-text-expert">
                                **คำอธิบายเชิงลึก:** ${expertInfo} 
                                ${descriptions[key] && descriptions[key].ref_link && descriptions[key].ref_link.length > 0 ? 
                                    `<a href="${descriptions[key].ref_link}" target="_blank" style="color: var(--accent-blue); text-decoration: none;">(อ่านเพิ่มเติม)</a>` : ''}
                            </p>
                            <p style="font-weight: 600; margin-top: 15px;">ค่า Header ที่ได้รับ:</p>
                            <code class="header-value">${headerValue}</code>
                            ${fixButtonHtml} `;
                
                item.innerHTML = `
                    <div class="header-title">
                        <span style="color: ${uiStatus.color}; margin-right: 10px;">${uiStatus.icon}</span>
                        <span>${displayKey}</span>
                        <span class="header-status-text status-${uiStatus.status}">${uiStatus.status}</span>
                    </div>
                    ${infoText}
                `;
                
                document.getElementById(uiStatus.group).appendChild(item);
            }

            
        }
    });
    
    // เพิ่ม Event Listeners ให้กับปุ่ม Suggest Fix ทุกปุ่มใน Expert View
    if (viewType === 'expert') {
        document.querySelectorAll('.suggest-fix-button').forEach(button => {
            button.removeEventListener('click', handleSuggestFix); // ป้องกันการเพิ่มซ้ำ
            button.addEventListener('click', handleSuggestFix);
        });
    }
}


// --- NEW: ฟังก์ชันจัดการการเรียก AI Suggestion (ปรับปรุงการแยกโค้ด) ---
async function handleSuggestFix(e) {
    const button = e.currentTarget;
    const headerName = button.getAttribute('data-header-name');
    const currentValue = button.getAttribute('data-current-value');
    const analysisInfo = button.getAttribute('data-analysis-info');

    const modal = document.getElementById('aiSuggestionModal');
    const modalTitle = document.getElementById('modalHeaderTitle');
    const loadingDiv = document.getElementById('aiSuggestionLoading');
    const errorDiv = document.getElementById('aiSuggestionError');
    const resultDiv = document.getElementById('aiSuggestionResult');
    const explanationP = document.getElementById('aiSuggestionExplanation');
    
    const codeContainer = document.getElementById('aiSuggestedCodeContainer'); 

    // 1. Show Modal and Loading
    modal.style.display = 'block';
    modalTitle.textContent = `AI Suggested Fix for ${headerName}`;
    loadingDiv.style.display = 'flex';
    errorDiv.style.display = 'none';
    resultDiv.style.display = 'none';
    codeContainer.innerHTML = ''; // ล้างโค้ดเก่า

    try {
        const response = await fetch('/suggest_fix', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                header_name: headerName, 
                current_value: currentValue, 
                analysis_info: analysisInfo 
            })
        });

        const data = await response.json();
        loadingDiv.style.display = 'none';

        if (data.success && data.suggestion) {
            resultDiv.style.display = 'block';
            
            const suggestion = data.suggestion.trim();
            // Regex to find all code blocks and their language labels
            const codeMatches = [...suggestion.matchAll(/```(\w+)\n([\s\S]+?)```/g)];
            
            let explanation = suggestion;
            
            // แยกคำอธิบาย (ข้อความที่ไม่อยู่ในโค้ดบล็อก)
            codeMatches.forEach(match => {
                explanation = explanation.replace(match[0], '');
            });
            explanationP.textContent = explanation.trim(); 
            
            // Map โค้ดที่ได้มา พร้อมเปลี่ยนชื่อประเภทให้เป็นมิตรกับผู้ใช้
            const codeSnippets = codeMatches.map(match => {
                let type = match[1].toLowerCase();
                let displayName;

                if (type === 'nginx') {
                    displayName = 'Nginx / Caddy';
                } else if (type === 'apache' || type === 'htaccess') {
                    displayName = 'Apache (.htaccess / httpd.conf)';
                } else if (type === 'javascript' || type === 'python' || type === 'php' || type === 'express') {
                    displayName = 'Backend Code (Node.js/Python/PHP)';
                } else {
                    displayName = match[1].charAt(0).toUpperCase() + match[1].slice(1);
                }

                return {
                    type: displayName,
                    code: match[2].trim()
                };
            });

            // สร้าง UI สำหรับแสดงโค้ดแต่ละประเภท
            codeSnippets.forEach(snippet => {
                const codeBlockHtml = `
                    <h3 class="code-title">${snippet.type} Configuration:</h3>
                    <div class="code-container">
                        <code class="suggested-code-block">${snippet.code}</code>
                        <button class="copy-button" onclick="copyCode(this)">Copy</button>
                    </div>
                `;
                codeContainer.innerHTML += codeBlockHtml;
            });

            if (codeSnippets.length === 0) {
                 codeContainer.innerHTML = `<p style="color:var(--danger-red);">⚠️ AI response did not contain clear code blocks. (AI may be having trouble generating a fix).</p>`;
            }


        } else {
            errorDiv.textContent = data.error || 'Failed to get suggestion from AI.';
            errorDiv.style.display = 'block';
        }

    } catch (error) {
        loadingDiv.style.display = 'none';
        errorDiv.textContent = 'Network Error: Could not reach the AI service.';
        errorDiv.style.display = 'block';
    }
}

// NEW: ฟังก์ชัน Copy Code แยกต่างหาก
function copyCode(buttonElement) {
    const codeBlock = buttonElement.previousElementSibling;
    if (codeBlock) {
        navigator.clipboard.writeText(codeBlock.textContent);
        buttonElement.textContent = 'Copied!';
        setTimeout(() => { buttonElement.textContent = 'Copy'; }, 2000);
    }
}


// --- ฟังก์ชัน Raw Headers Table ที่ถูกแก้ไข ---
function renderRawHeadersTable(rawHeaders) {
    const tableBody = document.querySelector('#rawHeadersTable tbody');
    tableBody.innerHTML = ''; 
    
    // 1. แปลง Dictionary เป็น Array ของ [Name, Value]
    let headerArray = Object.entries(rawHeaders);

    // 2. จัดเรียงตาม Header Name (ลำดับตัวอักษร)
    headerArray.sort((a, b) => a[0].localeCompare(b[0]));
    
    // 3. สร้าง HTML
    for (const [name, value] of headerArray) {
        let displayValue;
        if (Array.isArray(value)) {
            // สำหรับ Header ที่มีหลายค่า เช่น Set-Cookie
            displayValue = value.join('\n');
        } else {
            // สำหรับ Header ทั่วไป
            displayValue = value;
        }

        const row = tableBody.insertRow();
        const cellName = row.insertCell();
        const cellValue = row.insertCell();
        
        cellName.textContent = name;
        
        // ใช้ span และ class raw-display-value เพื่อรองรับ CSS white-space: pre-wrap
        // และใช้ class header-value เพื่อคงสไตล์เดิมไว้
        cellValue.innerHTML = `<span class="header-value raw-display-value">${displayValue}</span>`;
    }
}

function switchView(viewId, tabId) {
    document.querySelectorAll('.view-content').forEach(view => {
        view.classList.remove('active-view');
    });
    document.getElementById(viewId).classList.add('active-view');
    
    document.querySelectorAll('.tab-button').forEach(tab => {
        tab.classList.remove('active');
    });
    document.getElementById(tabId).classList.add('active');
}

function animateScore(finalScore) {
    const scoreElement = document.getElementById('scorePercentage');
    const circleProgress = document.querySelector('.circle-progress');
    const circumference = 440; // 2 * pi * 70 (r=70)
    
    // ตั้งค่าเริ่มต้น
    let currentScore = 0;
    const duration = 1500; // ms
    const stepTime = 10; // ms

    const step = finalScore / (duration / stepTime);

    const timer = setInterval(() => {
        currentScore += step;
        if (currentScore >= finalScore) {
            currentScore = finalScore;
            clearInterval(timer);
        }
        
        const offset = circumference - (currentScore / 100) * circumference;
        circleProgress.style.strokeDashoffset = offset;
        scoreElement.textContent = `${Math.round(currentScore)}%`;
        
        // Change color based on score
        let color;
        if (currentScore >= 90) color = '#28a745'; 
        else if (currentScore >= 80) color = '#00c4ff';
        else if (currentScore >= 65) color = '#ff9800'; 
        else color = '#dc3545'; 

        circleProgress.style.stroke = color;

    }, stepTime);
}

function updateRiskLevel(score) {
    const riskLevelElement = document.getElementById('riskLevel');
    const riskStarsElement = document.getElementById('riskStars');
    let riskLevelText;
    let stars;
    
    if (score >= 90) {
        riskLevelText = 'Risk: Very Low';
        stars = '⭐⭐⭐⭐⭐';
    } else if (score >= 80) {
        riskLevelText = 'Risk: Low';
        stars = '⭐⭐⭐⭐';
    } else if (score >= 65) {
        riskLevelText = 'Risk: Medium';
        stars = '⭐⭐⭐';
    } else if (score >= 50) {
        riskLevelText = 'Risk: High';
        stars = '⭐⭐';
    } else {
        riskLevelText = 'Risk: Very High';
        stars = '⭐';
    }
    
    riskLevelElement.textContent = riskLevelText;
    riskStarsElement.textContent = stars;
}


document.addEventListener('DOMContentLoaded', () => {
    // Initial UI setup
    updateRiskLevel(0); 
    const circleProgress = document.querySelector('.circle-progress');
    if (circleProgress) circleProgress.style.strokeDashoffset = 440; 
    
    // Add Tab Listeners
    const tabGeneral = document.getElementById('tabGeneral');
    const tabExpert = document.getElementById('tabExpert');

    if (tabGeneral) {
        tabGeneral.addEventListener('click', () => {
            switchView('generalView', 'tabGeneral');
        });
    }

    if (tabExpert) {
        tabExpert.addEventListener('click', () => {
            switchView('expertView', 'tabExpert');
        });
    }

    // NEW: Add Modal close listeners
    const modal = document.getElementById('aiSuggestionModal');
    const closeButton = document.querySelector('.close-button');

    if (closeButton) {
        closeButton.onclick = function() {
            modal.style.display = "none";
        }
    }

    // Close when clicking outside the modal
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }
});