    // 默认已拥有设备（可持久化到 localStorage）
let ownedEquipment = JSON.parse(localStorage.getItem('ownedEquipment') || '[]');

document.addEventListener('DOMContentLoaded', function() {
    // DOM元素
    const addMemberBtn = document.getElementById('addMemberBtn');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const addMemberModal = document.getElementById('addMemberModal');
    const dietPlanModal = document.getElementById('dietPlanModal');
    const memberForm = document.getElementById('memberForm');
    const uploadArea = document.getElementById('uploadArea');
    const reportUpload = document.getElementById('reportUpload');
    const membersGrid = document.getElementById('membersGrid');

    // 示例成员数据
    let members = [
        {
            id: 1,
            name: '小明',
            age: 8,
            gender: 'male',
            indicators: ['anemia'],
            avatar: '👦'
        },
        {
            id: 2,
            name: '爷爷',
            age: 65,
            gender: 'male',
            indicators: ['hypertension', 'hyperlipidemia'],
            avatar: '👴'
        }
    ];
// ===== 厨房设备数据 =====
const kitchenEquipment = [
  { id: 'stove',   name: '燃气灶', icon: '🔥' },
  { id: 'oven',    name: '烤箱',   icon: '🔥' },
  { id: 'steamer', name: '蒸锅',   icon: '🥘' },
  { id: 'blender', name: '破壁机', icon: '🧃' },
  { id: 'airfry',  name: '空气炸锅', icon: '🍟' },
  { id: 'rice',    name: '电饭煲', icon: '🍚' }
];
    // 饮食方案数据库
    const dietPlans = {
        hypertension: {
            title: '限盐饮食方案',
            desc: '针对高血压人群的饮食建议',
            content: `
                <h4>核心原则</h4>
                <p>• 每日盐摄入 ≤ 5g</p>
                <p>• 增加钾摄入（香蕉/菠菜）</p>
                <h4>推荐食材</h4>
                <p>• 低钠酱油</p>
                <p>• 香菇（天然鲜味替代盐）</p>
            `
        },
        hyperlipidemia: {
            title: '低脂饮食方案',
            desc: '针对高血脂人群的饮食建议',
            content: `
                <h4>核心原则</h4>
                <p>• 减少饱和脂肪摄入</p>
                <p>• 增加膳食纤维</p>
                <h4>推荐食材</h4>
                <p>• 燕麦</p>
                <p>• 深海鱼类</p>
            `
        },
        anemia: {
            title: '补铁饮食方案',
            desc: '针对贫血人群的饮食建议',
            content: `
                <h4>核心原则</h4>
                <p>• 增加血红素铁摄入</p>
                <p>• 搭配维生素C促进吸收</p>
                <h4>推荐食材</h4>
                <p>• 红肉</p>
                <p>• 菠菜（焯水后食用）</p>
            `
        }
    };

    // 初始化页面
    renderMembers();
renderKitchenEquipment();
    // 事件监听
    addMemberBtn.addEventListener('click', () => addMemberModal.style.display = 'flex');
    closeModalBtn.addEventListener('click', () => addMemberModal.style.display = 'none');

    // 点击空白处关闭弹窗
    window.addEventListener('click', (e) => {
        if (e.target === addMemberModal) addMemberModal.style.display = 'none';
        if (e.target === dietPlanModal) dietPlanModal.style.display = 'none';
    });

    // 上传区域点击事件
    uploadArea.addEventListener('click', () => reportUpload.click());
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = getComputedStyle(document.documentElement)
    .getPropertyValue('--primary-color').trim();
    });
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = getComputedStyle(document.documentElement)
        .getPropertyValue('--border-color').trim();
    });
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = getComputedStyle(document.documentElement)
        .getPropertyValue('--border-color').trim();
        if (e.dataTransfer.files.length) {
            reportUpload.files = e.dataTransfer.files;
            simulateReportAnalysis(); // 模拟报告分析
        }
    });

    // 表单提交
    memberForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const newMember = {
            id: Date.now(),
            name: document.getElementById('memberName').value,
            age: document.getElementById('memberAge').value,
            gender: document.getElementById('memberGender').value,
            indicators: Array.from(document.querySelectorAll('input[name="healthIndicator"]:checked')).map(el => el.value),
            avatar: document.getElementById('memberGender').value === 'male' ? '👨' : '👩'
        };

        members.push(newMember);
        renderMembers();
        addMemberModal.style.display = 'none';
        memberForm.reset();

    });

    // 渲染成员列表
    // 修改 renderMembers 函数
    function renderMembers() {
      membersGrid.innerHTML = members.map(member => `
        <div class="member-card" data-id="${member.id}">
          <div class="member-header">
            <div class="member-avatar">${member.avatar}</div>
            <div class="member-info">
              <h4>${member.name}</h4>
              <p>${member.age}岁 · ${member.gender === 'male' ? '男' : '女'}</p>
              ${member.indicators.length ? `
                <div class="member-tags">
                  ${member.indicators.map(ind => `<span class="health-tag">${getIndicatorName(ind)}</span>`).join('')}
                </div>
              ` : ''}
            </div>
          </div>
          
          <!-- 饮食方案直接内嵌 -->
          <div class="diet-plan">
            <h5>饮食建议</h5>
            <div class="diet-plan-content">
              ${generatePlanHTML(member)}
            </div>
          </div>
        </div>
      `).join('');
    }

    // 新增独立的方案生成函数
    function generatePlanHTML(member) {
      if (!member.indicators.length) return '<p>暂无特殊建议，保持均衡饮食即可</p>';

      return member.indicators.map(indicator => {
        if (!dietPlans[indicator]) return '';
        return `
          <p><strong>${dietPlans[indicator].title}:</strong> 
          ${dietPlans[indicator].content.replace(/<[^>]+>/g, '')}</p>
        `;
      }).join('');
    }


    // 模拟体检报告分析
    function simulateReportAnalysis() {
        // 这里是模拟分析过程，实际项目中需要对接后端API
        setTimeout(() => {
            // 模拟从报告中识别出的指标
            const detectedIndicators = ['hypertension', 'hyperlipidemia'];

            // 自动勾选对应的复选框
            document.querySelectorAll('input[name="healthIndicator"]').forEach(checkbox => {
                checkbox.checked = detectedIndicators.includes(checkbox.value);
            });

            alert('体检报告分析完成！已自动识别健康指标');
        }, 1500);
    }

    // 辅助函数：获取指标显示名称
    function getIndicatorName(key) {
        const names = {
            hypertension: '高血压',
            hyperlipidemia: '高血脂',
            diabetes: '高血糖',
            anemia: '贫血',
            osteoporosis: '骨质疏松'
        };
        return names[key] || key;
    }


// ===== 渲染厨房设备 =====
function renderKitchenEquipment() {
  const grid = document.getElementById('equipmentGrid');
  if (!grid) return; // 容错
  grid.innerHTML = kitchenEquipment.map(eq => `
    <div class="equipment-item">
      <input type="checkbox" id="${eq.id}" ${ownedEquipment.includes(eq.id) ? 'checked' : ''}>
      <label for="${eq.id}">${eq.icon} ${eq.name}</label>
    </div>
  `).join('');

  // 监听勾选变化并持久化
  grid.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    cb.addEventListener('change', () => {
      if (cb.checked) {
        if (!ownedEquipment.includes(cb.id)) ownedEquipment.push(cb.id);
      } else {
        ownedEquipment = ownedEquipment.filter(id => id !== cb.id);
      }
      localStorage.setItem('ownedEquipment', JSON.stringify(ownedEquipment));
    });
  });
}





});
document.querySelectorAll('.member-header').forEach(header => {
  header.addEventListener('click', () => {
    header.parentElement.classList.toggle('collapsed');
  });
});
