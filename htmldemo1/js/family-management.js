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

// 在文件顶部添加数据
const allergiesData = [
    { id: 'peanuts', name: '花生', icon: '🥜' },
    { id: 'shellfish', name: '贝类', icon: '🦐' },
    { id: 'dairy', name: '乳制品', icon: '🥛' },
    { id: 'eggs', name: '鸡蛋', icon: '🥚' },
    { id: 'gluten', name: '麸质', icon: '🌾' },
    { id: 'soy', name: '大豆', icon: '🫘' }
];

const dietaryRestrictionsData = [
    { id: 'vegetarian', name: '素食', icon: '🥗' },
    { id: 'halal', name: '清真', icon: '🕌' },
    { id: 'low_sodium', name: '低盐', icon: '🧂' },
    { id: 'low_sugar', name: '低糖', icon: '🍯' },
    { id: 'spicy', name: '忌辣', icon: '🌶️' },
    { id: 'pork', name: '忌猪肉', icon: '🐷' }
];
const healthIndicatorsData = [
    { id: 'hypertension', name: '高血压', icon: '💓', category: '心血管' },
    { id: 'hyperlipidemia', name: '高血脂', icon: '🩸', category: '心血管' },
    { id: 'diabetes', name: '高血糖', icon: '🍯', category: '代谢' },
    { id: 'anemia', name: '贫血', icon: '🩹', category: '血液' },
    { id: 'osteoporosis', name: '骨质疏松', icon: '🦴', category: '骨骼' },
    { id: 'gout', name: '痛风', icon: '🦶', category: '代谢' },
    { id: 'fatty_liver', name: '脂肪肝', icon: '🫘', category: '肝脏' },
    { id: 'gastritis', name: '胃炎', icon: '🫄', category: '消化' }
];
// 修改示例成员数据，添加过敏源和忌口
let members = [
    {
        id: 1,
        name: '小明',
        age: 8,
        gender: 'male',
        indicators: ['anemia'],
        allergies: ['peanuts', 'dairy'],
        restrictions: ['spicy'],
        avatar: '👦'
    },
    {
        id: 2,
        name: '爷爷',
        age: 65,
        gender: 'male',
        indicators: ['hypertension', 'hyperlipidemia'],
        allergies: [],
        restrictions: ['low_sodium', 'low_sugar'],
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
renderFormData();
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
// 修改memberForm的submit事件监听
memberForm.addEventListener('submit', (e) => {
    e.preventDefault();

    const newMember = {
        id: Date.now(),
        name: document.getElementById('memberName').value,
        age: document.getElementById('memberAge').value,
        gender: document.getElementById('memberGender').value,
        indicators: Array.from(document.querySelectorAll('input[name="healthIndicator"]:checked')).map(el => el.value),
        allergies: Array.from(document.querySelectorAll('input[name="allergies"]:checked')).map(el => el.value),
        restrictions: Array.from(document.querySelectorAll('input[name="dietaryRestrictions"]:checked')).map(el => el.value),
        avatar: document.getElementById('memberGender').value === 'male' ? '👨' : '👩'
    };

    members.push(newMember);
    renderMembers();
    addMemberModal.style.display = 'none';
    memberForm.reset();
});

    // 替换原有的renderMembers函数
function renderMembers() {
    membersGrid.innerHTML = members.map(member => `
        <div class="member-card" data-id="${member.id}">
            <div class="member-header">
                <div class="member-avatar">${member.avatar}</div>
                <div class="member-info">
                    <h4>${member.name}</h4>
                    <p>${member.age}岁 · ${member.gender === 'male' ? '男' : '女'}</p>
                </div>
            </div>
            
            <!-- 健康指标 -->
            ${member.indicators.length ? `
                <div class="member-section">
                    <h5>健康关注</h5>
                    <div class="tags-container">
                        ${member.indicators.map(ind => {
                            const indicatorInfo = healthIndicatorsData.find(i => i.id === ind);
                            return `<span class="tag health-tag">
                                ${indicatorInfo?.icon || '💊'} 
                                ${indicatorInfo?.name || getIndicatorName(ind)}
                            </span>`;
                        }).join('')}
                    </div>
                </div>
            ` : ''}
            
            <!-- 过敏源 -->
            ${member.allergies?.length ? `
                <div class="member-section">
                    <h5>过敏源</h5>
                    <div class="tags-container allergies">
                        ${member.allergies.map(allergy => {
                            const allergyInfo = allergiesData.find(a => a.id === allergy);
                            return `<span class="tag allergy-tag">${allergyInfo?.icon || '⚠️'} ${allergyInfo?.name || allergy}</span>`;
                        }).join('')}
                    </div>
                </div>
            ` : ''}
            
            <!-- 忌口 -->
            ${member.restrictions?.length ? `
                <div class="member-section">
                    <h5>饮食忌口</h5>
                    <div class="tags-container restrictions">
                        ${member.restrictions.map(restriction => {
                            const restrictionInfo = dietaryRestrictionsData.find(r => r.id === restriction);
                            return `<span class="tag restriction-tag">${restrictionInfo?.icon || '🚫'} ${restrictionInfo?.name || restriction}</span>`;
                        }).join('')}
                    </div>
                </div>
            ` : ''}
            
            <!-- 饮食方案 -->
            <div class="member-section">
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
// 改名为renderFormData更合适
// 修改renderFormData函数中的复选框渲染方式
function renderFormData() {
    // 渲染体检指标
    const healthIndicatorsGroup = document.querySelector('.checkbox-group');
    if (healthIndicatorsGroup) {
        healthIndicatorsGroup.innerHTML = healthIndicatorsData.map(indicator => `
            <label class="checkbox-item">
                <input type="checkbox" name="healthIndicator" value="${indicator.id}">
                <span class="checkbox-custom"></span>
                <span class="emoji-icon">${indicator.icon}</span>
                ${indicator.name}
                <span class="category-tag">${indicator.category}</span>
            </label>
        `).join('');
    }

    // 渲染过敏源（同样的方式）
    const allergiesGroup = document.getElementById('allergiesGroup');
    if (allergiesGroup) {
        allergiesGroup.innerHTML = allergiesData.map(allergy => `
            <label class="checkbox-item">
                <input type="checkbox" name="allergies" value="${allergy.id}">
                <span class="checkbox-custom"></span>
                <span class="emoji-icon">${allergy.icon}</span>
                ${allergy.name}
            </label>
        `).join('');
    }

    // 渲染忌口（同样的方式）
    const restrictionsGroup = document.getElementById('dietaryRestrictionsGroup');
    if (restrictionsGroup) {
        restrictionsGroup.innerHTML = dietaryRestrictionsData.map(restriction => `
            <label class="checkbox-item">
                <input type="checkbox" name="dietaryRestrictions" value="${restriction.id}">
                <span class="checkbox-custom"></span>
                <span class="emoji-icon">${restriction.icon}</span>
                ${restriction.name}
            </label>
        `).join('');
    }
}




});
document.querySelectorAll('.member-header').forEach(header => {
  header.addEventListener('click', () => {
    header.parentElement.classList.toggle('collapsed');
  });
});
