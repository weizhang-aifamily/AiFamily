/* ============= 1. 常量数据定义 ============= */

const familyMembers = [
  {
    id: 1, name: '爸爸', avatar: '👨', needs: ['lowFat'], displayNeeds: ['低脂'], healthStatus: '良好',
    allergens: ['peanuts']                           // ⬅ 新增
  },
  {
    id: 2, name: '妈妈', avatar: '👩', needs: ['highIron'], displayNeeds: ['补铁'], healthStatus: '缺铁性贫血',
    allergens: []                                    // ⬅ 新增
  },
  {
    id: 3, name: '爷爷', avatar: '👴', needs: ['lowSalt', 'highCalcium'], displayNeeds: ['限盐', '高钙'], healthStatus: '高血压',
    allergens: ['shrimp']                            // ⬅ 新增
  },
  {
    id: 4, name: '小明', avatar: '👦', needs: ['highCalcium'], displayNeeds: ['高钙'], healthStatus: '生长发育期',
    allergens: ['milk', 'peanuts']                   // ⬅ 新增
  }
];
const allergyIcons = {
  peanuts: '🥜',
  shrimp:  '🦐',
  milk:    '🥛',
  egg:     '🥚'
};
const dietSolutions = {
    lowSalt: { name: '限盐', icon: '🧂', desc: '钠<1500mg/日' },
    highCalcium: { name: '高钙', icon: '🦴', desc: '钙≥800mg/日' },
    lowFat: { name: '低脂', icon: '🥑', desc: '脂肪<50g/日' },
    highIron: { name: '补铁', icon: '🧲', desc: '铁≥15mg/日' }
};

const ingredientPool = {
  highCalcium: [
    {
      emoji: '🥦',
      name: '西蓝花',
      desc: '钙含量: 47mg/100g',
      tag: '高钙',
      grams: '200g',
      servings: [1, 2, 3, 4],
      nutrients: { calcium: 47, iron: 0.7, vitaminC: 89 },
      alternatives: [
        { emoji: '🥟', name: '豆腐', desc: '植物性高钙来源' },
        { emoji: '🧀', name: '奶酪', desc: '钙含量丰富的乳制品' },
        { emoji: '🌰', name: '杏仁', desc: '坚果类中的高钙代表' }
      ]
    },
    {
      emoji: '🥛',
      name: '牛奶',
      desc: '钙含量: 120mg/100ml',
      tag: '高钙',
      grams: '250ml',
      servings: [1, 2, 3, 4],
      nutrients: { calcium: 120, iron: 0, vitaminC: 0 },
      alternatives: [
        { emoji: '🌱', name: '豆奶', desc: '植物基高钙饮品' },
        { emoji: '🌰', name: '芝麻', desc: '植物性高钙种子' },
        { emoji: '🥬', name: '羽衣甘蓝', desc: '深绿叶高钙蔬菜' }
      ]
    },
    {
      emoji: '🥟',
      name: '豆腐',
      desc: '钙含量: 138mg/100g',
      tag: '高钙',
      grams: '150g',
      servings: [1, 2, 3, 4],
      nutrients: { calcium: 138, iron: 3.4, vitaminC: 0 },
      alternatives: [
        { emoji: '🧀', name: '奶酪', desc: '钙含量丰富的乳制品' },
        { emoji: '🥛', name: '牛奶', desc: '液体钙来源' },
        { emoji: '🌰', name: '杏仁', desc: '坚果类中的高钙代表' }
      ]
    }
  ],

  lowSalt: [
    {
      emoji: '🍄',
      name: '鲜香菇',
      desc: '低钠高鲜',
      tag: '调味',
      grams: '100g',
      servings: [1, 2, 3, 4],
      nutrients: { calcium: 3, iron: 0.5, vitaminC: 0 },
      alternatives: [
        { emoji: '🍄', name: '干香菇', desc: '浓缩鲜味，低钠' },
        { emoji: '🧅', name: '洋葱', desc: '天然甜味，提升风味' },
        { emoji: '🍅', name: '番茄', desc: '酸甜平衡，减少用盐' }
      ]
    },
    {
      emoji: '🧂',
      name: '低钠酱油',
      desc: '钠含量比普通酱油低50%',
      tag: '调味',
      grams: '15ml',
      servings: [1, 2, 3, 4],
      nutrients: { calcium: 0, iron: 0, vitaminC: 0 },
      alternatives: [
        { emoji: '🍶', name: '味增', desc: '发酵鲜味，低盐版' },
        { emoji: '🍋', name: '柠檬汁', desc: '酸味提味，减少用盐' },
        { emoji: '🧄', name: '大蒜', desc: '辛香提味，天然无盐' }
      ]
    },
    {
      emoji: '🍋',
      name: '柠檬',
      desc: '天然酸味替代盐',
      tag: '调味',
      grams: '50g',
      servings: [1, 2, 3, 4],
      nutrients: { calcium: 26, iron: 0.6, vitaminC: 53 },
      alternatives: [
        { emoji: '🍈', name: '酸橙', desc: '类似柠檬的酸味替代品' },
        { emoji: '🍅', name: '醋', desc: '酸味调味，零钠' },
        { emoji: '🥭', name: '罗望子', desc: '天然果酸，风味独特' }
      ]
    }
  ],

  highIron: [
    {
      emoji: '🥬',
      name: '菠菜',
      desc: '铁含量: 2.7mg/100g',
      tag: '补铁',
      grams: '150g',
      servings: [1, 2, 3, 4],
      nutrients: { calcium: 99, iron: 2.7, vitaminC: 28 },
      alternatives: [
        { emoji: '🥬', name: '羽衣甘蓝', desc: '高铁绿叶蔬菜' },
        { emoji: '🥬', name: '瑞士甜菜', desc: '高铁高钙' },
        { emoji: '🌰', name: '芝麻', desc: '植物性高铁种子' }
      ]
    },
    {
      emoji: '🥩',
      name: '红肉',
      desc: '铁含量: 3.3mg/100g',
      tag: '补铁',
      grams: '120g',
      servings: [1, 2, 3, 4],
      nutrients: { calcium: 7, iron: 3.3, vitaminC: 0 },
      alternatives: [
        { emoji: '🐓', name: '鸡肝', desc: '动物性高铁' },
        { emoji: '🐚', name: '蛤蜊', desc: '贝类富含血红素铁' },
        { emoji: '🌱', name: '扁豆', desc: '植物性高铁豆类' }
      ]
    },
    {
      emoji: '🍓',
      name: '草莓',
      desc: '维生素C促进铁吸收',
      tag: '补铁',
      grams: '100g',
      servings: [1, 2, 3, 4],
      nutrients: { calcium: 16, iron: 0.4, vitaminC: 59 },
      alternatives: [
        { emoji: '🥝', name: '奇异果', desc: '高维生素C水果' },
        { emoji: '🍊', name: '橙子', desc: '维生素C丰富' },
        { emoji: '🌶️', name: '红椒', desc: '蔬菜中高维C' }
      ]
    }
  ],

  lowFat: [
    {
      emoji: '🍗',
      name: '鸡胸肉',
      desc: '脂肪含量: 2g/100g',
      tag: '低脂',
      grams: '150g',
      servings: [1, 2, 3, 4],
      nutrients: { calcium: 5, iron: 0.7, vitaminC: 0 },
      alternatives: [
        { emoji: '🦃', name: '火鸡胸', desc: '超低脂高蛋白' },
        { emoji: '🦐', name: '虾', desc: '低脂海鲜' },
        { emoji: '🐟', name: '鳕鱼', desc: '白肉低脂鱼' }
      ]
    },
    {
      emoji: '🫒',
      name: '橄榄油',
      desc: '富含不饱和脂肪酸',
      tag: '健康油脂',
      grams: '10ml',
      servings: [1, 2, 3, 4],
      nutrients: { calcium: 1, iron: 0.1, vitaminC: 0 },
      alternatives: [
        { emoji: '🌻', name: '亚麻籽油', desc: '富含Omega-3' },
        { emoji: '🥑', name: '牛油果', desc: '健康单不饱和脂肪' },
        { emoji: '🥜', name: '坚果', desc: '健康脂肪来源' }
      ]
    },
    {
      emoji: '🥦',
      name: '西兰花',
      desc: '膳食纤维丰富',
      tag: '低脂',
      grams: '200g',
      servings: [1, 2, 3, 4],
      nutrients: { calcium: 47, iron: 0.7, vitaminC: 89 },
      alternatives: [
        { emoji: '🥬', name: '花椰菜', desc: '低脂高纤' },
        { emoji: '🌿', name: '芦笋', desc: '低热量高纤' },
        { emoji: '🫑', name: '青椒', desc: '低碳水蔬菜' }
      ]
    }
  ]
};
const ingredientPrice = {
  '西蓝花': 3.5,
  '牛奶': 4.0,
  '豆腐': 2.8,
  '鲜香菇': 6.0,
  '低钠酱油': 0.5,
  '柠檬': 1.2,
  '菠菜': 2.0,
  '红肉': 12.0,
  '草莓': 8.0,
  '鸡胸肉': 9.0,
  '橄榄油': 1.0,
  '西兰花': 3.5
  // 如后续还有新食材，继续补充
};

const globalAlternatives = {
  // 高钙类
  西蓝花: [
    { emoji: '🥦', name: '西蓝花', desc: '钙含量: 47mg/100g', grams: '200g' },
    { emoji: '🥬', name: '菠菜', desc: '钙含量: 99mg/100g', grams: '150g' },
    { emoji: '🧀', name: '奶酪', desc: '钙含量: 720mg/100g', grams: '50g' }
  ],
  牛奶: [
    { emoji: '🥛', name: '牛奶', desc: '钙含量: 120mg/100ml', grams: '250ml' },
    { emoji: '🥛', name: '羊奶', desc: '钙含量: 140mg/100ml', grams: '250ml' },
    { emoji: '🥛', name: '豆浆', desc: '钙含量: 25mg/100ml', grams: '300ml' }
  ],
  豆腐: [
    { emoji: '🥟', name: '豆腐', desc: '钙含量: 138mg/100g', grams: '150g' },
    { emoji: '🥛', name: '牛奶', desc: '钙含量: 120mg/100ml', grams: '250ml' },
    { emoji: '🧀', name: '奶酪', desc: '钙含量: 720mg/100g', grams: '50g' }
  ],

  // 低盐调味类
  鲜香菇: [
    { emoji: '🍄', name: '鲜香菇', desc: '低钠高鲜', grams: '100g' },
    { emoji: '🍄', name: '干香菇', desc: '浓缩鲜味，低钠', grams: '30g' },
    { emoji: '🧅', name: '洋葱', desc: '天然甜味，提升风味', grams: '100g' }
  ],
  低钠酱油: [
    { emoji: '🧂', name: '低钠酱油', desc: '钠含量比普通酱油低50%', grams: '15ml' },
    { emoji: '🍋', name: '柠檬汁', desc: '酸味提味，减少用盐', grams: '15ml' },
    { emoji: '🧄', name: '大蒜', desc: '辛香提味，天然无盐', grams: '10g' }
  ],
  柠檬: [
    { emoji: '🍋', name: '柠檬', desc: '天然酸味替代盐', grams: '50g' },
    { emoji: '🍈', name: '酸橙', desc: '类似柠檬的酸味替代品', grams: '50g' },
    { emoji: '🍅', name: '醋', desc: '酸味调味，零钠', grams: '15ml' }
  ],

  // 补铁类
  菠菜: [
    { emoji: '🥬', name: '菠菜', desc: '铁含量: 2.7mg/100g', grams: '150g' },
    { emoji: '🥬', name: '羽衣甘蓝', desc: '高铁绿叶蔬菜', grams: '150g' },
    { emoji: '🌰', name: '芝麻', desc: '植物性高铁种子', grams: '20g' }
  ],
  红肉: [
    { emoji: '🥩', name: '红肉', desc: '铁含量: 3.3mg/100g', grams: '120g' },
    { emoji: '🐓', name: '鸡肝', desc: '动物性高铁', grams: '100g' },
    { emoji: '🐚', name: '蛤蜊', desc: '贝类富含血红素铁', grams: '100g' }
  ],
  草莓: [
    { emoji: '🍓', name: '草莓', desc: '维生素C促进铁吸收', grams: '100g' },
    { emoji: '🥝', name: '奇异果', desc: '高维生素C水果', grams: '100g' },
    { emoji: '🍊', name: '橙子', desc: '维生素C丰富', grams: '150g' }
  ],

  // 低脂类
  鸡胸肉: [
    { emoji: '🍗', name: '鸡胸肉', desc: '脂肪含量: 2g/100g', grams: '150g' },
    { emoji: '🦃', name: '火鸡胸', desc: '超低脂高蛋白', grams: '150g' },
    { emoji: '🦐', name: '虾', desc: '低脂海鲜', grams: '120g' }
  ],
  橄榄油: [
    { emoji: '🫒', name: '橄榄油', desc: '富含不饱和脂肪酸', grams: '10ml' },
    { emoji: '🌻', name: '亚麻籽油', desc: '富含Omega-3', grams: '10ml' },
    { emoji: '🥑', name: '牛油果', desc: '健康单不饱和脂肪', grams: '50g' }
  ],
  西兰花: [
    { emoji: '🥦', name: '西兰花', desc: '膳食纤维丰富', grams: '200g' },
    { emoji: '🥬', name: '花椰菜', desc: '低脂高纤', grams: '200g' },
    { emoji: '🌿', name: '芦笋', desc: '低热量高纤', grams: '150g' }
  ]
};
const dishPool = {
    highCalcium: [
        {emoji: '🧀', name: '奶酪焗南瓜', desc: '金黄拉丝，奶香浓郁'},
        {emoji: '🥛', name: '牛奶布丁', desc: '丝滑细腻，入口即化'},
        {emoji: '🥟', name: '豆腐羹', desc: '嫩滑鲜美，温暖入心'}
    ],
    lowSalt: [
        {emoji: '🍄', name: '香菇蒸鸡', desc: '鲜嫩多汁，原汁原味'},
        {emoji: '🍤', name: '白灼虾', desc: '清甜弹牙，蘸酱更佳'},
        {emoji: '🥗', name: '凉拌时蔬', desc: '清脆爽口，开胃解腻'}
    ],
    highIron: [
        {emoji: '🥬', name: '蒜蓉菠菜', desc: '翠绿鲜嫩，蒜香扑鼻'},
        {emoji: '🍖', name: '红烧牛肉', desc: '软烂入味，酱香浓郁'},
        {emoji: '🍳', name: '猪肝炒蛋', desc: '滑嫩可口，补铁佳品'}
    ],
    lowFat: [
        {emoji: '🍗', name: '凉拌鸡丝', desc: '低脂高蛋白，麻辣鲜香'},
        {emoji: '🐟', name: '蒸鳕鱼', desc: '雪白细腻，柠檬提鲜'},
        {emoji: '🥕', name: '胡萝卜沙拉', desc: '色彩缤纷，酸甜开胃'}
    ]
};

const ingredientTips = {
    '奶酪': '钙含量: 720mg/100g，建议每日摄入300ml奶制品',
    '牛奶': '钙含量: 120mg/100ml，早晚各一杯最佳',
    '豆腐': '钙含量: 138mg/100g，优质植物蛋白来源',
    '鲜香菇': '香菇可增强免疫力',
    '低钠酱油': '低钠酱油适合高血压人群',
    '柠檬': '柠檬可促进铁吸收',
    '菠菜': '菠菜里的草酸会阻碍铁吸收，焯水30秒即可去除60%草酸',
    '红肉': '红肉是优质铁来源',
    '草莓': '草莓富含维生素C促进铁吸收',
    '鸡胸肉': '鸡胸肉低脂高蛋白',
    '橄榄油': '橄榄油富含不饱和脂肪酸',
    '西兰花': '西兰花营养全面'
};
/* ---------- 近期吃过数据 ---------- */
const historyDishes = [
  { emoji: '🥗', name: '彩虹沙拉', desc: '5色蔬菜拼盘', count: '5' },
  { emoji: '🍤', name: '黄金虾仁', desc: '酥脆鲜嫩', count: '3' },
  { emoji: '🍄', name: '菌菇汤', desc: '浓郁暖胃', count: '2' },
  { emoji: '🥕', name: '糖醋萝卜', desc: '开胃爽口', count: '2' },
  { emoji: '🌽', name: '奶油玉米', desc: '香甜软糯', count: '1' },
  { emoji: '🍗', name: '椒盐鸡翅', desc: '外酥里嫩', count: '2' }
];
/* ========== 尝鲜功能 ========== */
const tasteDishesPool = [
  { emoji: '🥗', name: '彩虹沙拉', desc: '5色蔬菜拼盘', category: '轻食' },
  { emoji: '🍤', name: '黄金虾仁', desc: '酥脆鲜嫩', category: '海鲜' },
  { emoji: '🍄', name: '菌菇汤', desc: '浓郁暖胃', category: '汤品' },
  { emoji: '🥕', name: '糖醋萝卜', desc: '开胃爽口', category: '小菜' },
  { emoji: '🌽', name: '奶油玉米', desc: '香甜软糯', category: '主食' },
  { emoji: '🍗', name: '椒盐鸡翅', desc: '外酥里嫩', category: '肉类' },
  { emoji: '🍜', name: '凉拌面', desc: '夏日清爽', category: '主食' },
  { emoji: '🥦', name: '蒜蓉西兰花', desc: '翠绿清香', category: '蔬菜' },
  { emoji: '🍳', name: '太阳蛋', desc: '溏心嫩滑', category: '蛋类' },
  { emoji: '🍠', name: '蜜汁红薯', desc: '香甜软糯', category: '主食' }
];

/* ============= 2. 主应用逻辑 ============= */
document.addEventListener('DOMContentLoaded', function() {
    // DOM元素引用
    const memberTags = document.getElementById('memberTags');
    const solutionTags = document.getElementById('solutionTags');
    const ingredientList = document.getElementById('ingredientList');
    const dishList = document.getElementById('dishList');
    const achievementToast = document.getElementById('achievementToast');
    const progressFill = document.getElementById('progressFill');
    const achievementText = document.getElementById('achievementText');
    const mealTimeSubtitle = document.getElementById('mealTimeSubtitle');

    // 状态管理
    let activeMembers = [...familyMembers];
    let activeSolutions = new Set();
    let usageCount = 0;

    /* ============= 3. 核心功能函数 ============= */
    function setMealTime() {
        const hour = new Date().getHours();
        let mealType = '午餐';
        if (hour < 10) mealType = '早餐';
        else if (hour >= 16) mealType = '晚餐';
        mealTimeSubtitle.textContent = `益家配餐 · ${mealType}`;
    }

function renderMembers() {

// 新增：渲染 smart-guard-bar 的成员
    const guardMemberLine = document.querySelector('.smart-guard-bar .member-line');
    if (guardMemberLine) {
        guardMemberLine.innerHTML = familyMembers.map(member =>
            `<span class="member-tag active">${member.avatar}${member.name}</span>`
        ).join('');
    }

    activeMembers = [...familyMembers];
    // 动态生成过敏源和忌口详情
    updateFilterDetails();

}

function renderMembersbak() {
    memberTags.innerHTML = familyMembers.map(member => `
        <div class="member-tag active" data-id="${member.id}">
            <div class="member-main">
                <div class="member-avatar-section">
                    <div class="member-avatar">${member.avatar}</div>
                    <div class="member-name">${member.name}</div>
                </div>
                <div class="member-details">
                    <div class="needs-row">
                        ${member.displayNeeds.map(need => 
                            `<span class="need-badge">${need}</span>`
                        ).join('')}
                    </div>
                </div>
            </div>
            <a href="nutrition-report.html?memberId=${member.id}" class="report-link">
                查看报告
                <svg viewBox="0 0 24 24"><path d="M9 5l7 7-7 7"></path></svg>
            </a>
        </div>
    `).join('');
    // 动态生成过敏源和忌口详情
    updateFilterDetails();

    document.querySelectorAll('.member-tag').forEach(tag => {
        tag.addEventListener('click', function(e) {
            if (e.target.closest('.report-link')) return;
            this.classList.toggle('active');
            updateActiveMembers();
            updateFilterDetails(); // 更新详情
            syncGuardBarMembers();
        });
    });
}
// 新增：同步 smart-guard-bar 成员状态
function syncGuardBarMembers() {
    const guardMemberLine = document.querySelector('.smart-guard-bar .member-line');
    if (!guardMemberLine) return;

    guardMemberLine.innerHTML = familyMembers.map(member => {
        const isActive = activeMembers.some(m => m.id === member.id);
        return `<span class="member-tag ${isActive ? 'active' : ''}">${member.avatar}${member.name}</span>`;
    }).join('');
}

function updateFilterDetails() {
    // 获取所有选中成员的过敏源和忌口
    const activeMembers = familyMembers.filter(m =>
        document.querySelector(`.member-tag[data-id="${m.id}"]`)?.classList.contains('active')
    );

    // 合并所有过敏源
    const allAllergens = [...new Set(activeMembers.flatMap(m => m.allergens || []))];
    const allergenText = allAllergens.map(a => allergyIcons[a] || a).join('');
    document.getElementById('allergensDetail').textContent =
        allergenText ? `(${allergenText})` : '';

    // 合并所有忌口（假设在dietaryRestrictions里）
    const allTaboos = [...new Set(activeMembers.flatMap(m => m.restrictions || []))];
    const tabooText = allTaboos.join(', ');
    document.getElementById('tabooDetail').textContent =
        tabooText ? `(${tabooText})` : '';
}

    function updateActiveMembers() {
        activeMembers = [];
        document.querySelectorAll('.member-tag.active').forEach(tag => {
            const id = parseInt(tag.dataset.id);
            const member = familyMembers.find(m => m.id === id);
            if (member) activeMembers.push(member);
        });
        updateSolutions();
        syncGuardBarMembers();
    }

    function updateSolutions() {
        activeSolutions = new Set();
        activeMembers.forEach(member => {
            member.needs.forEach(need => activeSolutions.add(need));
        });
        renderSolutionTags();
        generateRecommendations();
    }

function renderSolutionTags() {
    solutionTags.innerHTML = Array.from(activeSolutions).map(solution => `
        <div class="solution-tag active" data-solution="${solution}">
            <span class="icon">${dietSolutions[solution].icon}</span>
            ${dietSolutions[solution].name}
        </div>
    `).join('');

    // 单击切换选中
    solutionTags.querySelectorAll('.solution-tag').forEach(tag => {
        tag.addEventListener('click', () => {
            tag.classList.toggle('active');
            const key = tag.dataset.solution;
            if (tag.classList.contains('active')) {
                activeSolutions.add(key);
            } else {
                activeSolutions.delete(key);
            }
            generateRecommendations();
        });
    });
}

// 初始化：默认全部选中
activeSolutions = new Set(Object.keys(dietSolutions));
renderSolutionTags();

    function generateRecommendations() {
        generateIngredients();
        generateDishes();
        usageCount++;
        updateAchievementProgress();
    }

// 替换原来的 generateIngredients 函数
function generateIngredients() {
    const ingredients = new Set();
    activeSolutions.forEach(solution => {
        const randomIngredient = ingredientPool[solution][
            Math.floor(Math.random() * ingredientPool[solution].length)
        ];
        ingredients.add(randomIngredient);
    });

ingredientList.innerHTML = Array.from(ingredients).map(ing => {
    const servingMembers = ing.servings.map(id =>
        familyMembers.find(m => m.id === id).name
    ).join('、');

    return `
        <div class="food-card" data-ingredient='${JSON.stringify(ing).replace(/'/g, "&apos;")}'>
            <div class="food-icon">${ing.emoji}</div>
            <div class="food-main">
                <div class="food-title">
                    <h4>${ing.name}</h4>
                    <span class="food-grams">${ing.grams}</span>
                </div>
                <div class="food-info">
                    <span class="food-tag">${ing.tag}</span>
                    <span class="food-desc">${ing.desc}</span>
                </div>
            </div>
            <div class="food-servings" title="适合: ${servingMembers}">${ing.servings.length}人份</div>
        </div>
    `;
}).join('');

  // ✨ 计算并显示预计花费
  let totalCost = 0;
  ingredients.forEach(ing => {
    // 根据 grams 字段提取数字，单位统一按 100g 折算
    const grams = parseFloat(ing.grams) || 100;
    const pricePer100g = ingredientPrice[ing.name] || 5; // 缺省 5 元
    totalCost += (grams / 100) * pricePer100g;
  });
  document.getElementById('budgetSpent').textContent = `预估¥${totalCost.toFixed(1)}`;

    document.querySelectorAll('.food-card').forEach(card =>
        card.addEventListener('click', () => showReplaceModal(JSON.parse(card.dataset.ingredient), card))
    );

    showIngredientTips(Array.from(ingredients));
}
    function generateDishes() {
        const dishes = [];
        activeSolutions.forEach(solution => {
            const availableDishes = dishPool[solution].filter(
                dish => !dishes.some(d => d.name === dish.name)
            );
            if (availableDishes.length > 0) {
                dishes.push(
                    availableDishes[Math.floor(Math.random() * availableDishes.length)]
                );
            }
        });

        dishList.innerHTML = dishes.map(dish => `
            <div class="dish-card">
                <div class="dish-image">${dish.emoji}</div>
                <div class="dish-label">${dish.name}</div>
            </div>
        `).join('');

    }

    function showIngredientTips(ingredients) {
        const tipElement = document.getElementById('ingredientTip');
        if (ingredients.length === 0) {
            tipElement.textContent = '暂无提示信息';
            return;
        }

        let currentIndex = 0;
        function showNextTip() {
            const currentIngredient = ingredients[currentIndex];
            tipElement.textContent = ingredientTips[currentIngredient.name] || '暂无提示信息';
            currentIndex = (currentIndex + 1) % ingredients.length;
        }
        showNextTip();
        setInterval(showNextTip, 5000);
    }

    function showAchievement(reason, name) {
        achievementToast.textContent = `${reason}: 解锁${name}`;
        achievementToast.style.display = 'block';
        setTimeout(() => {
            achievementToast.style.display = 'none';
        }, 3000);
    }

    function updateAchievementProgress() {
        const progress = Math.min(usageCount / 5 * 100, 100);
        progressFill.style.width = `${progress}%`;
        achievementText.textContent = `再完成${5 - usageCount}次规划解锁「智能厨神」成就`;
    }


    function init() {
        setMealTime();
        initBudgetRange();
        renderMembers();
        updateSolutions();
        updateFilterDetails();
        showAchievement('首次使用', '营养规划师✨');
          // 新增幻灯片初始化
  initSlideshow();
  initFirstComboSelection();
renderTasteRow();                 // 生成尝鲜菜
  document.getElementById('refreshTasteInline')
          .addEventListener('click', renderTasteRow); // 换一批
            //过敏源忌口等
    document.getElementById('excludeAllergens').addEventListener('change', generateRecommendations);
    document.getElementById('excludeTaboo').addEventListener('change', generateRecommendations);
    document.getElementById('seasonalOnly').addEventListener('change', generateRecommendations);

    // 预算选择事件监听
    document.querySelectorAll('input[name="budgetLevel"]').forEach(radio => {
        radio.addEventListener('change', generateRecommendations);
    });
    }

    // 启动应用
    init();
});


/* ============= 替换食材功能 ============= */
let currentReplacementTarget = null;

function showReplaceModal(ingredient, targetCard) {
    if (!ingredient?.name || !globalAlternatives[ingredient.name]) {
        console.error('无效的食材或缺少备选列表');
        return;
    }

    currentReplacementTarget = targetCard;

    const alternatives = globalAlternatives[ingredient.name];
    const currentData = JSON.parse(targetCard.dataset.ingredient || '{}');

    const modalHTML = `
    <div class="ingredient-modal">
        <div class="modal-content">
            <h3>替换 ${currentData.name}</h3>
            <div class="current-ingredient">
                <div class="current-icon">${currentData.emoji}</div>
                <div>
                    <h4>${currentData.name} ${currentData.grams}</h4>
                    <p>${currentData.desc}</p>
                </div>
            </div>
            <div class="alternatives-title">可选替代食材</div>
            <div class="alternatives-grid">
                ${alternatives.map(alt => `
                    <div class="alternative-item" 
                         data-ingredient='${JSON.stringify(alt).replace(/'/g, "&apos;")}'>
                        <div class="alt-icon">${alt.emoji}</div>
                        <div class="alt-name">${alt.name}</div>
                        <div class="alt-grams">${alt.grams}</div>
                        <div class="alt-desc">${alt.desc}</div>
                    </div>
                `).join('')}
            </div>
            <div class="modal-actions">
                <button class="cancel-btn">取消</button>
                <button class="confirm-btn">确认替换</button>
            </div>
        </div>
    </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);
    const modal = document.querySelector('.ingredient-modal');

    // 选择逻辑
    let selectedIngredient = null;
    modal.querySelectorAll('.alternative-item').forEach(item => {
        item.addEventListener('click', function() {
            modal.querySelectorAll('.alternative-item').forEach(i =>
                i.classList.remove('selected'));
            this.classList.add('selected');
            selectedIngredient = JSON.parse(this.dataset.ingredient.replace(/&apos;/g, "'"));
        });
    });

    // 确认替换
    modal.querySelector('.confirm-btn').addEventListener('click', () => {
        if (selectedIngredient) {
            updateIngredientCard(selectedIngredient);
            saveReplacement(currentData.name, selectedIngredient.name);
        }
        modal.remove();
    });

    // 取消/关闭
    modal.querySelector('.cancel-btn').addEventListener('click', () => modal.remove());
    modal.addEventListener('click', (e) => e.target === modal && modal.remove());
}

function updateIngredientCard(newIngredient) {
    if (!currentReplacementTarget) return;

    // 更新卡片数据
    const card = currentReplacementTarget;
    card.dataset.ingredient = JSON.stringify(newIngredient).replace(/'/g, "&apos;");

    // 更新显示
    card.querySelector('.food-icon').textContent = newIngredient.emoji;
    // 2. 名称
    const titleEl = card.querySelector('.food-title h4');
    if (titleEl) titleEl.textContent = newIngredient.name;

    // 3. 克数
    const gramsEl = card.querySelector('.food-title .food-grams');
    if (gramsEl) gramsEl.textContent = newIngredient.grams;

    // 4. 描述
    const descEl = card.querySelector('.food-info .food-desc');
    if (descEl) descEl.textContent = newIngredient.desc;
}

function saveReplacement(original, replacement) {
    // 这里可以添加保存到本地存储或API的逻辑
    console.log(`已替换: ${original} → ${replacement}`);
    // 示例: localStorage.setItem('lastReplacement', JSON.stringify({original, replacement}));
}

/* ============= 定时更新函数 ============= */
function updateAlternatives() {

}

// 每30分钟更新一次
setInterval(updateAlternatives, 30 * 60 * 1000);
updateAlternatives(); // 初始化加载

// 过滤状态对象
window.filterFlags = { seasonal: true, allergen: false, taboo: false };

const toggles = document.querySelectorAll('#filterToggles .toggle-btn');
toggles.forEach(btn => {
  btn.addEventListener('click', () => {
    const key = btn.dataset.filter;
    btn.classList.toggle('active');
    window.filterFlags[key] = !window.filterFlags[key];
  });
});

function initBudgetRange() {
  const BUDGET_RANGE = { min: 20, max: 200, step: 5, default: 80 };

}
/* ========== 今日营养仪表盘 ========== */
const nutrientTargets = { calories:2000, protein:60, calcium:800, iron:15, sodium:2000, fat:60 };
let currentIntake = { calories:0, protein:0, calcium:0, iron:0, sodium:0, fat:0 };

function renderDash(){
  Object.keys(nutrientTargets).forEach(key=>{
    const percent = Math.round(currentIntake[key]/nutrientTargets[key]*100);
    const li = document.querySelector(`.dash-bars li[data-nutrient="${key}"]`);
    const bar = li.querySelector('i');
    const val = li.querySelector('.val');
    bar.style.width = Math.min(percent,100)+'%';
    val.textContent = (percent>100?'+':'')+(percent-100)+'%';
    li.querySelector('.bar').dataset.status =
      percent>120?'danger':percent>100?'warning':'';
  });
}
document.getElementById('miniRefresh').addEventListener('click',()=>{
  // 这里后续接入真实计算
  renderDash();
});
renderDash();

/* ========== 同类替换滑杆 ========== */
// 在每个 .food-card 下方插入滑杆（示例）
document.querySelectorAll('.food-card').forEach(card=>{
  const slider = document.createElement('div');
  slider.className='replace-slider';
  slider.innerHTML=`
    <div class="slider-row">
      <span>🥦</span>
      <input type="range" min="0" max="2" value="0">
      <span>🥬</span>
      <button class="apply-replace">✓</button>
    </div>
  `;
  card.appendChild(slider);
  card.querySelector('.food-title').addEventListener('click',()=>{
    slider.classList.toggle('open');
  });
});
/* ===== 套餐勾选逻辑 ===== */
const basketCountEl  = document.getElementById('basketCount');
const openBasketBtn  = document.getElementById('openBasket');
let selectedDishes = [];

document.addEventListener('change', e=>{
  if(!e.target.matches('.dish-item input')) return;
  const dish = e.target.value;
  if(e.target.checked){
    selectedDishes.push(dish);
  }else{
    selectedDishes = selectedDishes.filter(d=>d!==dish);
  }
  updateBasket();
});

function updateBasket(){
  const count = selectedDishes.length;
  basketCountEl.textContent = `已选 ${count} 道菜`;
  openBasketBtn.disabled = count === 0;
}

/* 初始化 */
updateBasket();

/* ========== 幻灯片功能 ========== */
function initSlideshow() {
  const track = document.querySelector('.slideshow-track');
  const slides = document.querySelectorAll('.combo-slide');
  const indicators = document.querySelectorAll('.indicator');
  const prevBtn = document.getElementById('prevSlide');
  const nextBtn = document.getElementById('nextSlide');
  let currentSlide = 0;

  // 更新幻灯片位置
  function updateSlidePosition() {
    track.style.transform = `translateX(-${currentSlide * 100}%)`;

    // 更新指示点
    indicators.forEach((indicator, index) => {
      indicator.classList.toggle('active', index === currentSlide);
    });
  }

  // 切换到下一张
  function nextSlide() {
    currentSlide = (currentSlide + 1) % slides.length;
    updateSlidePosition();
  }

  // 切换到上一张
  function prevSlide() {
    currentSlide = (currentSlide - 1 + slides.length) % slides.length;
    updateSlidePosition();
  }

  // 点击指示点切换
  indicators.forEach((indicator, index) => {
    indicator.addEventListener('click', () => {
      currentSlide = index;
      updateSlidePosition();
    });
  });

  // 按钮事件绑定
  nextBtn.addEventListener('click', nextSlide);
  prevBtn.addEventListener('click', prevSlide);

  // 自动播放（可选）
  let autoplayInterval = setInterval(nextSlide, 5000);

  // 鼠标悬停时暂停自动播放
  track.addEventListener('mouseenter', () => clearInterval(autoplayInterval));
  track.addEventListener('mouseleave', () => {
    autoplayInterval = setInterval(nextSlide, 5000);
  });

  // 初始化位置
  updateSlidePosition();
}

// 初始化第一个套餐默认全选
function initFirstComboSelection() {
  const firstCombo = document.querySelector('.combo-slide[data-combo="morning"]');
  const checkboxes = firstCombo.querySelectorAll('input[type="checkbox"]');

  checkboxes.forEach(checkbox => {
    checkbox.checked = true;
    selectedDishes.push(checkbox.value);
  });

  updateBasket();
}
function renderTasteRow() {
  const container = document.getElementById('tasteRowList');
  const shuffled = [...tasteDishesPool].sort(() => Math.random() - 0.5);
  const selected = shuffled.slice(0, 3);

  container.innerHTML = selected.map(dish => `
    <div class="dish-item">
      <input type="checkbox" value="${dish.name}">
      <div class="dish-image">${dish.emoji}</div>
      <span class="dish-name">${dish.name}</span>
      <span class="nutri-tag">${dish.desc}</span>
    <span class="add-btn" data-dish="${dish.name}">+</span>
    </div>
  `).join('');
}

/* ---------- 渲染近期吃过 ---------- */
function renderHistoryRow() {
  const track = document.getElementById('historyTrack');
  track.innerHTML = historyDishes.map(dish => `
    <div class="dish-item">
      <input type="checkbox" value="${dish.name}">
      <div class="dish-image">${dish.emoji}</div>
      <span class="dish-name">${dish.name}</span>
      <span class="nutri-tag">${dish.count}</span>
    <span class="add-btn" data-dish="${dish.name}">+</span>
    </div>
  `).join('');
}
renderHistoryRow();

/* ---------- 尝鲜 + 历史 共用加菜 ---------- */
function attachAddButtons() {
  document.querySelectorAll('.add-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const dish = btn.dataset.dish;
      if (!selectedDishes.includes(dish)) {
        selectedDishes.push(dish);
        updateBasket();
      }
    });
  });
}
attachAddButtons();
// 示例随机评分生成
function getRandomRating() {
    const rating = (4 + Math.random()).toFixed(1);
    const stars = '⭐'.repeat(Math.floor(rating)) + '☆'.repeat(5 - Math.ceil(rating));
    return `${stars} ${rating}`;
}


// 初始隐藏食材清单
document.querySelector('.card').style.display = 'none';

const overlay   = document.getElementById('cartOverlay');
const drawer    = document.getElementById('cartDrawer');
const openBtn   = document.getElementById('openBasket');
const closeBtn  = document.getElementById('closeCart');

// 打开
openBtn.addEventListener('click', () => {
    overlay.classList.add('show');
});

// 关闭
closeBtn.addEventListener('click', closeCart);
overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeCart();
});
function closeCart() {
    overlay.classList.remove('show');
}
// 打开弹窗
  function openPopup(){
    document.getElementById('overlaymore').style.display='flex';
  }
  // 关闭弹窗
  function closePopup(){
    document.getElementById('overlaymore').style.display='none';
  }
  // 绑定关闭事件
  document.getElementById('closeBtnmore').addEventListener('click', closePopup);
  document.getElementById('openmore').addEventListener('click', openPopup);
