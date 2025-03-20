// 環境配置
const config = {
    // 本地開發環境
    development: {
        API_BASE_URL: 'http://localhost:5000'
    },
    // 生產環境
    production: {
        API_BASE_URL: 'https://prime-sum-backend.onrender.com'
    }
};

// 根據當前環境選擇配置
const currentConfig = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? config.development
    : config.production;

export default currentConfig;
