const pullOverlay = document.getElementById('pullOverlay');
const panel   = document.getElementById('hiddenPanel');
const arrow   = document.getElementById('toggleArrow');
const closePanelBtn= document.getElementById('closePanelBtn');
let startY    = 0;
/* ========== 1. 量高度 ========== */
function getPanelHeight() {
  // 1. 先让所有隐藏类失效
  document.body.classList.remove('panel-open');
  panel.style.transition = 'none';
  panel.style.transform  = 'translateY(0)';

  // 2. 强刷一次布局
  panel.offsetHeight;

  // 3. 读高度
  const h = panel.offsetHeight;
document.documentElement.style.setProperty('--panel-height', `${h}px`);
  // 4. 立刻恢复原状
  panel.style.transform  = '';
  panel.style.transition = '';
  closePanel();              // 如果你想保持初始收起状态
  return h;
}

const PANEL_HEIGHT = getPanelHeight();       // 只做一次
const THRESHOLD    = 60;
/* 手势：下拉打开 */
document.addEventListener('touchstart', e => { startY = e.touches[0].clientY; });

document.addEventListener('touchmove', e => {
  if (window.scrollY > 0) return;
  const dy = e.touches[0].clientY - startY;
  if (dy <= 0) return;
  e.preventDefault();

  const ratio = Math.min(dy / PANEL_HEIGHT, 1);   // 用真实高度
  panel.style.transform = `translateY(${(ratio - 1) * PANEL_HEIGHT}px)`;
  pullOverlay.style.opacity = ratio * 0.6;
});

document.addEventListener('touchend', e => {
  const dy = e.changedTouches[0].clientY - startY;
  dy > THRESHOLD ? openPanel() : closePanel();
});

/* 统一收口：所有“关闭”动作都走这里 */
function openPanel() {
  document.body.classList.add('panel-open');
  arrow.textContent = '↑';
  resetInlineStyle();                      // 打开时也清一次，避免残留
}

function closePanel() {
  document.body.classList.remove('panel-open');
  arrow.textContent = '↓';
  resetInlineStyle();                      // 关键：清行内样式
}

/* 把行内样式清空，让 CSS 类重新接管 */
function resetInlineStyle() {
  panel.style.transform = '';
  pullOverlay.style.opacity = '';
}

/* 点击事件 —— 统一用类切换，不再碰行内样式 */
arrow.addEventListener('click', () =>
  document.body.classList.contains('panel-open') ? closePanel() : openPanel()
);
closePanelBtn.addEventListener('click', closePanel);

/* 点遮罩也能关 */
pullOverlay.addEventListener('click', closePanel);