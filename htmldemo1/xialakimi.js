const overlay = document.getElementById('pullOverlay');
const panel   = document.getElementById('hiddenPanel');
const arrow   = document.getElementById('toggleArrow');
const closeBtn= document.getElementById('closePanelBtn');
let startY    = 0;

/* 手势：下拉打开 */
document.addEventListener('touchstart', e => { startY = e.touches[0].clientY; });

document.addEventListener('touchmove', e => {
  if (window.scrollY > 0) return;          // 页面已滚动时不触发
  const dy = e.touches[0].clientY - startY;
  if (dy <= 0) return;                     // 只处理下拉
  e.preventDefault();
  const ratio = Math.min(dy / 150, 1);     // 0~1 的进度
  panel.style.transform = `translateY(-${(1 - ratio) * 100}%)`;
  overlay.style.opacity = ratio * 0.6;
});

document.addEventListener('touchend', e => {
  const dy = e.changedTouches[0].clientY - startY;
  // 手势距离够长 → 打开，否则复位
  if (dy > 60) {
    openPanel();
  } else {
    resetInlineStyle();                    // 关键：立即复位
  }
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
  overlay.style.opacity = '';
}

/* 点击事件 —— 统一用类切换，不再碰行内样式 */
arrow.addEventListener('click', () =>
  document.body.classList.contains('panel-open') ? closePanel() : openPanel()
);
closeBtn.addEventListener('click', closePanel);

/* 点遮罩也能关 */
overlay.addEventListener('click', closePanel);