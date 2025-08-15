/**
 * 加载所有Web Components组件
 */
function loadComponents() {
    // 底部导航菜单
    if (!customElements.get('bottom-nav')) {
        fetch('components/bottom-nav.html')
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const template = doc.getElementById('bottom-nav-template');

                // 注册Web Component
                class BottomNav extends HTMLElement {
                    constructor() {
                        super();
                        const content = template.content.cloneNode(true);
                        this.appendChild(content);
                    }
                }

                customElements.define('bottom-nav', BottomNav);

                // 插入到页面
                if (!document.querySelector('bottom-nav')) {
                    document.body.insertAdjacentHTML('beforeend', '<bottom-nav></bottom-nav>');
                }
            })
            .catch(err => console.error('加载底部菜单失败:', err));
    }
}

// DOM加载后初始化组件
document.addEventListener('DOMContentLoaded', loadComponents);
