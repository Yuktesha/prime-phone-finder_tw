// DOM 元素
const elements = {
    // 頁面元素
    primeSearchPage: document.getElementById('primeSearchPage'),
    primePhonePage: document.getElementById('primePhonePage'),
    primeSearchTab: document.getElementById('primeSearchTab'),
    primePhoneTab: document.getElementById('primePhoneTab'),
    
    // 表單元素
    primeSearchForm: document.getElementById('primeSearchForm'),
    primePhoneForm: document.getElementById('primePhoneForm'),
    start: document.getElementById('startRange'),
    end: document.getElementById('endRange'),
    minSequences: document.getElementById('minSequences'),
    maxSequences: document.getElementById('maxSequences'),
    minLength: document.getElementById('minLength'),
    maxLength: document.getElementById('maxLength'),
    prefix: document.getElementById('phonePrefix'),
    
    // 結果顯示元素
    loading: document.getElementById('loading'),
    estimatedTime: document.getElementById('estimatedTime'),
    elapsedTime: document.getElementById('elapsedTime'),
    remainingTime: document.getElementById('remainingTime'),
    stats: document.getElementById('stats'),
    results: document.getElementById('resultsTable'),
    phoneResults: document.getElementById('phoneResults'),
    prefixes: document.getElementById('prefixResults'),
    
    // 按鈕
    themeToggle: document.getElementById('themeToggle'),
    copyResults: document.getElementById('copyResults'),
    saveResults: document.getElementById('saveResults'),
    
    // 錯誤訊息
    errorMessage: document.getElementById('errorMessage'),
    progressDiv: document.getElementById('progress')
};

const API_BASE_URL = 'http://localhost:5000';

// 顯示/隱藏載入中
function showLoading() {
    elements.loading.style.display = 'flex';
}

function hideLoading() {
    elements.loading.style.display = 'none';
}

// 顯示錯誤訊息
function showError(message) {
    elements.errorMessage.textContent = message;
    elements.errorMessage.style.display = 'block';
    setTimeout(() => {
        elements.errorMessage.style.display = 'none';
    }, 5000);
}

// 初始化頁面
async function initializePage() {
    // 載入可用的前綴
    await listPrimePrefixes();
    
    // 註冊事件監聽器
    elements.primeSearchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await findPrimesWithSequences();
    });
    
    elements.primePhoneForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await findPrimePhones();
    });
}

// 搜索質數序列
async function findPrimesWithSequences() {
    const startInput = elements.start;
    const endInput = elements.end;
    const minSeqInput = elements.minSequences;
    const maxSeqInput = elements.maxSequences;
    const minLenInput = elements.minLength;
    const maxLenInput = elements.maxLength;
    const resultsDiv = elements.results;
    
    try {
        // 顯示載入中
        showLoading();
        elements.progressDiv.textContent = '正在搜索質數...';
        resultsDiv.innerHTML = '';
        
        const params = new URLSearchParams({
            start: startInput.value,
            end: endInput.value,
            min_sequences: minSeqInput.value,
            max_sequences: maxSeqInput.value || -1,
            min_length: minLenInput.value,
            max_length: maxLenInput.value || -1
        });

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);  // 30 秒超時

        const response = await fetch(`${API_BASE_URL}/api/find_primes_with_sequences?${params}`, {
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(await response.text());
        }

        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }

        // 更新進度
        elements.progressDiv.textContent = '搜索完成，正在處理結果...';
        
        // 顯示結果
        const results = data.results || [];
        if (results.length === 0) {
            resultsDiv.innerHTML = '<p>未找到符合條件的質數</p>';
        } else {
            const table = document.createElement('table');
            table.innerHTML = `
                <tr>
                    <th>質數</th>
                    <th>序列數量</th>
                    <th>序列</th>
                </tr>
            `;
            
            results.forEach(result => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${result.prime}</td>
                    <td>${result.sequences.length}</td>
                    <td>${result.sequences.map(seq => seq.join(' + ')).join('<br>')}</td>
                `;
                table.appendChild(row);
            });
            
            resultsDiv.innerHTML = '';
            resultsDiv.appendChild(table);
            resultsDiv.innerHTML += `
                <p>
                    共找到 ${results.length} 個質數
                    <br>
                    搜索時間：${data.total_time ? data.total_time.toFixed(2) : '未知'} 秒
                </p>
            `;
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            elements.results.innerHTML = '<p class="error">請求超時。請縮小搜索範圍或調整參數後重試。</p>';
        } else {
            elements.results.innerHTML = `<p class="error">錯誤：${error.message}</p>`;
        }
    } finally {
        hideLoading();
        elements.progressDiv.textContent = '';
    }
}

// 列出可用的前綴
async function listPrimePrefixes() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/list_prime_phone_prefixes`);
        if (!response.ok) {
            throw new Error(await response.text());
        }
        
        const data = await response.json();
        if (data.error) {
            throw new Error(data.error);
        }
        
        const prefixes = data.prefixes || [];
        if (prefixes.length === 0) {
            elements.prefixes.innerHTML = '<p>目前沒有可用的前綴</p>';
            return;
        }
        
        // 建立前綴按鈕列表
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'prefix-buttons';
        
        prefixes.forEach(prefix => {
            const button = document.createElement('button');
            button.textContent = prefix;
            button.type = 'button';  // 防止在表單中觸發提交
            button.onclick = () => {
                // 移除 "09" 前綴並更新輸入框
                elements.prefix.value = prefix.slice(2);
                // 自動觸發生成
                findPrimePhones();
            };
            buttonContainer.appendChild(button);
        });
        
        elements.prefixes.innerHTML = '<h3>可用的前綴：</h3>';
        elements.prefixes.appendChild(buttonContainer);
        
    } catch (error) {
        elements.prefixes.innerHTML = `<p class="error">載入前綴失敗：${error.message}</p>`;
    }
}

// 搜索質數手機號碼
async function findPrimePhones() {
    try {
        const inputPrefix = elements.prefix.value.trim();
        if (!inputPrefix || inputPrefix.length !== 2 || !/^\d{2}$/.test(inputPrefix)) {
            throw new Error('請輸入 2 位數字的前綴');
        }
        
        showLoading();
        elements.progressDiv.textContent = '正在搜索質數手機號碼...';
        elements.phoneResults.innerHTML = '';
        
        const response = await fetch(`${API_BASE_URL}/api/find_prime_phones?prefix=${inputPrefix}`);
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText);
        }
        
        const data = await response.json();
        if (data.error) {
            throw new Error(data.error);
        }
        
        // 更新進度
        elements.progressDiv.textContent = '搜索完成，正在處理結果...';
        
        const primePhones = data.prime_phones || [];
        if (primePhones.length === 0) {
            elements.phoneResults.innerHTML = '<p>未找到符合條件的質數手機號碼</p>';
        } else {
            elements.phoneResults.innerHTML = `
                <h3>找到 ${primePhones.length} 個質數手機號碼：</h3>
                <div class="phone-grid">
                    ${primePhones.map(phone => `
                        <div class="phone-number">
                            ${phone}
                            <button onclick="copyToClipboard('${phone}')">複製</button>
                        </div>
                    `).join('')}
                </div>
            `;
        }
    } catch (error) {
        elements.phoneResults.innerHTML = `<p class="error">錯誤：${error.message}</p>`;
    } finally {
        hideLoading();
        elements.progressDiv.textContent = '';
    }
}

// 複製到剪貼簿
window.copyToClipboard = function(text) {
    navigator.clipboard.writeText(text).then(() => {
        showError('已複製到剪貼簿');
    }).catch(err => {
        showError('複製失敗：' + err.message);
    });
}

// 儲存主題設定
function saveTheme(isDark) {
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    document.body.classList.toggle('dark-theme', isDark);
}

// 載入主題設定
function loadSavedTheme() {
    const savedTheme = localStorage.getItem('theme') || 'auto';
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const isDark = savedTheme === 'dark' || (savedTheme === 'auto' && prefersDark);
    document.body.classList.toggle('dark-theme', isDark);
}

// 切換主題
function toggleTheme() {
    const isDark = !document.body.classList.contains('dark-theme');
    saveTheme(isDark);
}

// 監聽系統主題變化
function setupThemeListener() {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addListener((e) => {
        if (localStorage.getItem('theme') === 'auto') {
            document.body.classList.toggle('dark-theme', e.matches);
        }
    });
}

// 事件監聽器
document.addEventListener('DOMContentLoaded', () => {
    loadSavedTheme();
    setupThemeListener();
    
    // 頁面切換
    elements.primeSearchTab.addEventListener('click', () => {
        elements.primeSearchPage.classList.add('active');
        elements.primePhonePage.classList.remove('active');
        elements.primeSearchTab.classList.add('active');
        elements.primePhoneTab.classList.remove('active');
    });
    
    elements.primePhoneTab.addEventListener('click', () => {
        elements.primeSearchPage.classList.remove('active');
        elements.primePhonePage.classList.add('active');
        elements.primeSearchTab.classList.remove('active');
        elements.primePhoneTab.classList.add('active');
    });
    
    // 主題切換
    elements.themeToggle.addEventListener('click', toggleTheme);
    
    initializePage();
    
    // 複製和儲存結果
    elements.copyResults.addEventListener('click', () => {
        const tableData = elements.results.textContent;
        copyToClipboard(tableData);
        showError('已複製到剪貼簿');
    });
    
    elements.saveResults.addEventListener('click', () => {
        const rows = [];
        const table = elements.results.querySelector('table');
        if (table) {
            const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent);
            rows.push(headers.join(','));
            
            const cells = Array.from(table.querySelectorAll('tbody tr')).map(tr => 
                Array.from(tr.querySelectorAll('td')).map(td => `"${td.textContent}"`).join(',')
            );
            rows.push(...cells);
        }
        const csvContent = rows.join('\n');
        const link = document.createElement('a');
        link.setAttribute('href', encodeURI(`data:text/csv;charset=utf-8,${csvContent}`));
        link.setAttribute('download', '質數搜索結果.csv');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });
});
