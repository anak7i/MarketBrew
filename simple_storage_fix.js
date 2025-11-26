// MarketBrew 简化存储修复脚本
// 确保订阅数据在关闭浏览器后不丢失

// 修复存储键名
const STORAGE_KEY = 'marketbrew_subscriptions_permanent';

// 保存订阅数据
function saveSubscriptions(subscriptions) {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(subscriptions));
        console.log(`✅ 已保存 ${subscriptions.length} 个订阅`);
    } catch (e) {
        console.error('❌ 保存失败:', e);
    }
}

// 加载订阅数据
function loadSubscriptions() {
    try {
        // 尝试从新键名加载
        let saved = localStorage.getItem(STORAGE_KEY);
        
        // 如果没有数据，尝试从旧键名迁移
        if (!saved) {
            const oldKeys = ['stockSubscriptions', 'marketbrew_subscriptions'];
            for (const oldKey of oldKeys) {
                const oldData = localStorage.getItem(oldKey);
                if (oldData) {
                    saved = oldData;
                    localStorage.setItem(STORAGE_KEY, saved);
                    localStorage.removeItem(oldKey);
                    console.log(`🔄 已迁移数据从 ${oldKey}`);
                    break;
                }
            }
        }
        
        if (saved) {
            const data = JSON.parse(saved);
            console.log(`✅ 加载了 ${data.length} 个订阅`);
            return data;
        }
    } catch (e) {
        console.error('❌ 加载失败:', e);
    }
    
    // 返回默认数据
    return [
        {symbol: '000001', name: '平安银行', addedAt: new Date().toISOString()},
        {symbol: '600519', name: '贵州茅台', addedAt: new Date().toISOString()},
        {symbol: '000858', name: '五粮液', addedAt: new Date().toISOString()},
        {symbol: '300750', name: '宁德时代', addedAt: new Date().toISOString()}
    ];
}

// 页面关闭时强制保存
window.addEventListener('beforeunload', () => {
    if (window.subscriptionManager && window.subscriptionManager.subscriptions) {
        saveSubscriptions(window.subscriptionManager.subscriptions);
        console.log('💾 页面关闭前已保存数据');
    }
});

// 每30秒自动保存一次
setInterval(() => {
    if (window.subscriptionManager && window.subscriptionManager.subscriptions) {
        saveSubscriptions(window.subscriptionManager.subscriptions);
    }
}, 30000);

console.log('🚀 MarketBrew 存储保护已启动');

// 导出函数供页面使用
window.MarketBrewStorage = {
    save: saveSubscriptions,
    load: loadSubscriptions,
    key: STORAGE_KEY
};