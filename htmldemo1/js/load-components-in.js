/**
 * 加载所有Web Components组件
 */
function loadComponents() {
    // 底部导航菜单组件定义
    class BottomNav extends HTMLElement {
        constructor() {
            super();
            this.innerHTML = `
                <nav class="bottom-nav">
                    <a href="dashboard.html" class="nav-item">
                        <span class="nav-icon">🏠</span>
                        <span class="nav-text">首页</span>
                    </a>
                    <a href="family-management.html" class="nav-item">
                        <span class="nav-icon">👨‍👩‍👧‍👦</span>
                        <span class="nav-text">家庭成员</span>
                    </a>
                    <a href="suppliers.html" class="nav-item">
                        <span class="nav-icon">🛒</span>
                        <span class="nav-text">特色食材</span>
                    </a>
                    <a href="my.html" class="nav-item">
                        <span class="nav-icon">👤</span>
                        <span class="nav-text">我的</span>
                    </a>
                </nav>
                <style>
                    .bottom-nav {
                        position: fixed;
                        bottom: 0;
                        left: 0;
                        right: 0;
                        background: white;
                        display: flex;
                        justify-content: space-around;
                        padding: 10px 0;
                        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
                        z-index: 100;
                    }
                    .nav-item {
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        text-decoration: none;
                        color: var(--text-light, #64748B);
                        font-size: 12px;
                        padding: 5px 10px;
                        transition: all 0.3s ease;
                    }
                    .nav-item.active {
                        color: var(--primary, #3B82F6);
                    }
                    .nav-icon {
                        font-size: 20px;
                        margin-bottom: 2px;
                    }
                    .nav-text {
                        font-size: 12px;
                    }
                    .nav-item:hover {
                        transform: translateY(-3px);
                    }
                </style>
            `;
            
            // 自动设置当前页面激活状态
            setTimeout(() => {
                const currentPath = window.location.pathname.split('/').pop() || 'peican.html';
                this.querySelectorAll('.nav-item').forEach(item => {
                    if (item.getAttribute('href') === currentPath) {
                        item.classList.add('active');
                    }
                });
            }, 0);
        }
    }
    
    // 注册组件
    if (!customElements.get('bottom-nav')) {
        customElements.define('bottom-nav', BottomNav);
    }
    
    // 插入到页面
    if (!document.querySelector('bottom-nav')) {
        document.body.insertAdjacentHTML('beforeend', '<bottom-nav></bottom-nav>');
    }
}

// DOM加载后初始化组件
document.addEventListener('DOMContentLoaded', loadComponents);
