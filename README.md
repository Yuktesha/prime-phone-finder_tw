# 質數手機號碼搜尋器 (Prime Phone Number Finder)

這是一個用於尋找質數手機號碼的網頁應用程式，支援查詢特定前綴的質數手機號碼以及尋找最接近輸入號碼的質數。

## 功能特點

- 根據前綴查詢質數手機號碼
- 尋找最接近輸入號碼的多個質數（支援1-100個結果）
- 響應式前綴參考表，根據螢幕寬度自動調整排列方式
- 支援深色/淺色主題（自動適應系統主題，同時提供手動切換選項）
- 結果可一鍵複製或匯出為 CSV
- 完整的錯誤處理和用戶提示
- 美觀的卡片式設計和載入動畫

## 系統需求

- Python 3.8 或更新版本
- Flask 框架
- SQLite 數據庫
- 支援現代網頁標準的瀏覽器（Chrome、Firefox、Edge 等）

## 本地部署

1. 安裝 Python 依賴：
   ```bash
   cd backend
   pip install flask flask-cors
   ```

2. 啟動後端服務器：
   ```bash
   python phone_api.py
   ```
   後端服務器將在 http://127.0.0.1:5000 運行

3. 啟動前端服務器：
   ```bash
   cd ../frontend
   python -m http.server 8000
   ```
   前端界面將在 http://localhost:8000 運行

## 雲端部署

### 使用 Render.com 部署後端

1. 在 Render.com 上創建一個新的 Web Service
2. 連接到您的 GitHub 倉庫
3. 設置以下配置：
   - 運行時環境：Python 3
   - 構建命令：`pip install -r requirements.txt`
   - 啟動命令：`cd backend && python phone_api.py`
4. 點擊 "Create Web Service"

### 使用 Vercel 部署前端

1. 在 Vercel 上創建一個新項目
2. 連接到您的 GitHub 倉庫
3. 設置構建配置：
   - 框架預設：Static Site
   - 根目錄：`frontend`
4. 點擊 "Deploy"

## 配置說明

### 後端配置

在 `backend/phone_api.py` 中：

- `host`：預設為 '127.0.0.1'，如需外部訪問請改為 '0.0.0.0'
- `port`：預設為 5000，可根據需要修改
- `debug`：生產環境請設為 False
- `DB_PATH`：數據庫路徑，可根據部署環境調整

### 前端配置

在 `frontend/index.html` 中：

- API 端點：預設為 'http://127.0.0.1:5000/api'，請根據後端部署位置修改
- 主題設置：可通過右上角按鈕手動切換，也會自動適應系統主題

## 安全性建議

1. 生產環境部署時：
   - 關閉 Flask 的調試模式
   - 設定適當的 CORS 規則
   - 使用 HTTPS
   - 添加請求速率限制

2. 建議使用反向代理（如 Nginx）保護後端服務

## 常見問題

1. 如果看到 "無法連接到伺服器" 錯誤：
   - 確認後端服務器是否正在運行
   - 檢查防火牆設定
   - 確認 API 端點設定是否正確

2. 如果搜尋結果不如預期：
   - 確保輸入的是有效的台灣手機號碼（09開頭，共10位數字）
   - 檢查數據庫是否包含足夠的質數手機號碼數據

## 授權

MIT License
