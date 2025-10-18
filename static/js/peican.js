import { getMembers,getDietSolutions,getCombos,getDishReco,getTagTbl  } from './familyDataLoader.js';
import { displayNutrients } from './nutritionDisplay.js';

/* ============= 1. 常量数据定义 ============= */
let memberIds;
let familyMembers = [
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
let allergyIcons = {
  peanuts: '🥜',
  shrimp:  '🦐',
  milk:    '🥛',
  egg:     '🥚'
};
let dietSolutions = {
    lowSalt: { name: '限盐', icon: '🧂', desc: '钠<1500mg/日' },
    highCalcium: { name: '高钙', icon: '🦴', desc: '钙≥800mg/日' },
    black_hair: { name: '低脂', icon: '🥑', desc: '脂肪<50g/日' },
    highIron: { name: '补铁', icon: '🧲', desc: '铁≥15mg/日' }
};
let cuisineTags = {};
let activeCuisines = new Set();
let categoryTags = {};
let activeCategories = new Set();
const cuisineSelectBox = document.getElementById('cuisineSelectBox');   // 外层容器
const cuisineToggle    = document.getElementById('cuisineToggle');      // 展开/收起按钮
const cuisineDropdown  = document.getElementById('cuisineDropdown');    // 下拉列表（ul）
let ingredientPool = {
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
let ingredientPrice = {
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

let globalAlternatives = {
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
let dishPool = {
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
    ],
    black_hair: [
        {emoji: '🍗', name: '凉拌鸡丝', desc: '低脂高蛋白，麻辣鲜香'},
        {emoji: '🐟', name: '蒸鳕鱼', desc: '雪白细腻，柠檬提鲜'},
        {emoji: '🥕', name: '胡萝卜沙拉', desc: '色彩缤纷，酸甜开胃'}
    ],
    TG: [
        {emoji: '🍗', name: '凉拌鸡丝', desc: '低脂高蛋白，麻辣鲜香'},
        {emoji: '🐟', name: '蒸鳕鱼', desc: '雪白细腻，柠檬提鲜'},
        {emoji: '🥕', name: '胡萝卜沙拉', desc: '色彩缤纷，酸甜开胃'}
    ],
    calcium: [
        {emoji: '🍗', name: '凉拌鸡丝', desc: '低脂高蛋白，麻辣鲜香'},
        {emoji: '🐟', name: '蒸鳕鱼', desc: '雪白细腻，柠檬提鲜'},
        {emoji: '🥕', name: '胡萝卜沙拉', desc: '色彩缤纷，酸甜开胃'}
    ]
};

let ingredientTips = {
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
/* ========== 1. 推荐菜数据结构 ========== */
let comboData = [
  {
    combo_id: '2234',
    combo_name: '早餐',
    meal_type: "breakfast",
    comboDesc: '10 分钟补足全天钙 80 %',
    dishes: [
      {
        dish_id: 1,
        name: '奶酪焗南瓜',
        picSeed: 'pumpkin',
        dish_tags: ['高钙 +72 %'],
        checked: false,
        rating: 4.7,
        food_list: [
            {name:'番茄',grams:'20g',tag:'',desc:''},
            {name:'鸡蛋',grams:'10g',tag:'',desc:''}
        ]
      }
    ]
  }
];

/* ---------- 近期吃过数据 ---------- */
let historyDishes = [
  { emoji: '🥗', name: '彩虹沙拉', desc: '5色蔬菜拼盘', count: '5' },
  { emoji: '🍤', name: '黄金虾仁', desc: '酥脆鲜嫩', count: '3' },
  { emoji: '🍄', name: '菌菇汤', desc: '浓郁暖胃', count: '2' },
  { emoji: '🥕', name: '糖醋萝卜', desc: '开胃爽口', count: '2' },
  { emoji: '🌽', name: '奶油玉米', desc: '香甜软糯', count: '1' },
  { emoji: '🍗', name: '椒盐鸡翅', desc: '外酥里嫩', count: '2' }
];
/* ========== 尝鲜功能 ========== */
let tasteDishesPool = [
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
let province_code = 'default';
let activeMembers = [];

/* ============= 2. 主应用逻辑 ============= */
document.addEventListener('DOMContentLoaded', function() {
    // DOM元素引用
    const memberTags = document.getElementById('memberTags');
    const solutionTags = document.getElementById('solutionTags');
    //食材清单
    const ingredientList = document.getElementById('ingredientList');
    const progressFill = document.getElementById('progressFill');
    const achievementText = document.getElementById('achievementText');

    // 状态管理
    activeMembers = [...familyMembers];
    let activeSolutions = new Set();
    let usageCount = 0;

function initMembers() {
    (async () => {
        familyMembers = await getMembers(1);
//        familyMembers = await getMembers(0);
        memberIds = familyMembers.map(m => m.member_id).join(',');
        cuisineTags = await getTagTbl('cuisine');
        categoryTags = await getTagTbl('category');

// 新增：渲染 smart-guard-bar 的成员
    const guardMemberLine = document.querySelector('.smart-guard-bar .member-line');
    if (guardMemberLine) {
        guardMemberLine.innerHTML = familyMembers.map(member =>
            `<span class="member-tag active" data-id="${member.member_id}">${member.avatar}${member.name}</span>`
        ).join('');
    }
    guardMemberLine.querySelectorAll('.member-tag').forEach(tag => {
        tag.addEventListener('click', () => {
            tag.classList.toggle('active');
            updateActiveMembers();
            updateSolutions();   // 让推荐实时刷新
            renderCategoryTags();
            generateRecommendations();
        });
    });
    activeMembers = [...familyMembers];
    window.activeMembers = activeMembers;
    // 动态生成过敏源和忌口详情
    //updateFilterDetails();
    updateSolutions();
//    renderCuisineTags();
    renderCategoryTags();
    generateRecommendations();
    })();
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
            const member = familyMembers.find(m => m.member_id === id);
            if (member) activeMembers.push(member);
        });
        window.activeMembers = activeMembers;
        //updateSolutions();
        //syncGuardBarMembers();
    }

    function updateSolutions() {
    (async () => {
    dietSolutions = await getDietSolutions(memberIds);
    if (activeMembers.length > 0) {
            // 如果有活跃成员，使用成员的 needs
            activeSolutions = new Set(
                activeMembers.flatMap(m => (m.needs || []).filter(Boolean))
            );
        } else {
            // 如果没有活跃成员，使用所有可用的饮食方案
            activeSolutions = new Set(Object.keys(dietSolutions));
        }
    // 直接用全局 dietSolutions 渲染标签
    solutionTags.innerHTML = [...activeSolutions]
        .filter(code => dietSolutions[code])      // 防止后端缺项
        .map(code => `
            <div class="solution-tag active" data-solution="${code}">
                <span class="icon">${dietSolutions[code].icon}</span>
                ${dietSolutions[code].name}
            </div>
        `).join('');

    // 绑定点击事件（只绑定一次即可）
    solutionTags.querySelectorAll('.solution-tag').forEach(tag => {
        tag.addEventListener('click', () => {
            tag.classList.toggle('active');
            const key = tag.dataset.solution;
            tag.classList.contains('active')
                ? activeSolutions.add(key)
                : activeSolutions.delete(key);
            generateRecommendations();
        });
    });


    })();
}

function renderCuisineTags() {
    if (!Array.isArray(cuisineTags)) return;

    // 按 sort 升序
    cuisineTags.sort((a, b) => a.sort - b.sort);

    // 直接用数组渲染
    cuisineDropdown.innerHTML = cuisineTags.map(
        ({ tag_code, tag_name }) => {
            const selected = activeCuisines.has(tag_code) ? 'selected' : '';
            return `<li data-code="${tag_code}" class="${selected}">${tag_name}</li>`;
        }
    ).join('');

    // 绑定点击
    cuisineDropdown.querySelectorAll('li').forEach(li => {
        li.addEventListener('click', () => {
            const code = li.dataset.code;
            li.classList.toggle('selected');
            activeCuisines.has(code) ? activeCuisines.delete(code) : activeCuisines.add(code);
            generateRecommendations();
        });
    });
}

/* ---------- 展开/收起 ---------- */
cuisineToggle?.addEventListener('click', () => {
    cuisineSelectBox.classList.toggle('open');
});
function renderCategoryTags() {
    if (!Array.isArray(categoryTags)) return;

    // 按 sort 升序
    categoryTags.sort((a, b) => a.sort - b.sort);

    // 用复选框形式渲染到 categorySelectBox
    const categorySelectBox = document.getElementById('categorySelectBox');
    categorySelectBox.innerHTML = categoryTags.map(
        ({ tag_code, tag_name }) => {
            const checked = activeCategories.has(tag_code) ? 'checked' : '';
            return `
                <div class="checkbox-item">
                    <label>
                        <input type="checkbox" value="${tag_code}" ${checked}>
                        <span>${tag_name}</span>
                    </label>
                </div>
            `;
        }
    ).join('');

    // 绑定点击事件
    categorySelectBox.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const code = checkbox.value;
            checkbox.checked ? activeCategories.add(code) : activeCategories.delete(code);
            generateRecommendations();
        });
    });
}
    function getActiveSolutions() {
        return Array.from(document.querySelectorAll('#solutionTags .solution-tag.active'))
            .map(tag => tag.getAttribute('data-solution'))
            .join(',');
    }
    function generateRecommendations() {
        generateCombos();
        usageCount++;
        updateAchievementProgress();
    }
function getSelectedMeals() {
    const checkboxes = document.querySelectorAll('input[name="mealType"]:checked');
    const selected = Array.from(checkboxes).map(cb => `${cb.value}`);
    return selected.join(',');
}

function initMealType() {
    const hour = new Date().getHours();
    let mealTypes = [];
    if (hour >= 6 && hour < 11) {
        mealTypes = ["breakfast"];
    } else if (hour >= 11 && hour < 17) {
        mealTypes = ["lunch"];
    } else {
        mealTypes = ["dinner"];
    }
    const checkboxes = document.querySelectorAll('input[name="mealType"]');
    checkboxes.forEach(cb => {
        cb.checked = mealTypes.includes(cb.value);
    });
}
/* ========== 2. 加载套餐 ========== */
function generateCombos() {
    const cuisineStr = [...activeCuisines].join(',');
    const categoryStr = [...activeCategories].join(',');
    const activeSolutions = getActiveSolutions();
    const mealType = getSelectedMeals();
    console.log(mealType);
    (async () => {
        console.log('activeMembers：', activeMembers);
        comboData = await getCombos({
            member_ids: memberIds,
            activeSolutions: activeSolutions,
            cuisine: cuisineStr,
            category: categoryStr,  // 新增的category参数
            members: activeMembers,
            province_code: province_code,
            mealType: mealType
        });
        //显示营养元素及身材图片
        console.log('comboData：', comboData);
        displayNutrients(comboData);
      const track = document.getElementById('combos');
      if (!track) return;
        const totalDishes = comboData.reduce((sum, combo) => sum + combo.dishes.length, 0);

    // 2. 写到页面
    const maxInput = document.getElementById('max_dishes');
    if (maxInput) maxInput.value = totalDishes;
  track.innerHTML = comboData.map((combo, idx) => `
    <article class="combo-row">
          <h3 class="combo-name">${combo.combo_name}</h3>
<!--          <p class="combo-desc">${combo.meal_type}</p>-->
      <div class="dish-list">
        ${combo.dishes.map(dish => `
          <label class="dish-item">
            <input type="checkbox" value="${dish.dish_id}" checked>
            <img src="://picsum.photos/seed/${dish.picSeed}/200" alt="${dish.name}">
            <span class="dish-name">${dish.name}</span>
            ${dish.exact_portion.size}份
            ${(dish.explicit_tags || []).map(tag => `<span class="nutri-tag">${tag}</span>`).join('')}
            <span class="dish-per">
                <span class="dot calories-dot">•${Math.round(dish.nutrients.EnergyKCal)}</span>
                <span class="dot protein-dot">•${Math.round(dish.nutrients.Protein)}</span>
                <span class="dot fat-dot">•${Math.round(dish.nutrients.Fat)}</span>
                <span class="dot carbs-dot">•${Math.round(dish.nutrients.Carbohydrate)}</span>
            </span>
          </label>
        `).join('')}
      </div>
    </article>
  `).join('');

  bindCheckboxSelectDishes();
  generateIngredients();
})();
}

// 生成食材清单
function generateIngredients() {
    const ingredientList = document.getElementById('ingredientList');
    if (!ingredientList) return;

    // 清空现有内容
    ingredientList.innerHTML = '';

    // 遍历所有套餐和菜品
    comboData.forEach(combo => {
        combo.dishes.forEach(dish => {
            if (dish.ingredients) {

                // 为每个菜品创建一个食材分组
                const dishSection = document.createElement('div');
                dishSection.className = 'dish-ingredient-section';
                dishSection.innerHTML = `
                    <div class="dish-header">
                        <h4>${dish.name}</h4>
                        <span class="dish-tags"></span>
                    </div>
                    <div class="dish-ingredients">
                        ${dish.ingredients.map(food => `
                            <div class="food-card">
                                <div class="food-icon"></div>
                                <div class="food-main">
                                    <div class="food-title">
                                        <h4>${food.name}</h4>
                                        <span class="food-grams">${food.grams}</span>
                                    </div>
                                    <div class="food-info">
                                        <span class="food-tag"></span>
                                        <span class="food-desc"></span>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
                ingredientList.appendChild(dishSection);
            }
        });
    });
    // 如果没有食材数据，显示提示
    if (ingredientList.children.length === 0) {
        ingredientList.innerHTML = `
            <div class="no-ingredients">
                <p>暂无食材数据</p>
            </div>
        `;
    }
}

    function updateAchievementProgress() {
        const progress = Math.min(usageCount / 5 * 100, 100);
        progressFill.style.width = `${progress}%`;
        achievementText.textContent = `再完成${5 - usageCount}次规划解锁「智能厨神」成就`;
    }


    function init() {
        initBudgetRange();
        initMealType();
        initMembers();
        renderTasteRow();                 // 生成尝鲜菜
        document.getElementById('refreshTasteInline')
          .addEventListener('click', renderTasteRow); // 换一批
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
//const basketCountEl  = document.getElementById('basketCount');
//const openBasketBtn  = document.getElementById('openBasket');
let selectedDishes = [];

function bindCheckboxSelectDishes() {
  // 绑定新的事件
  document.querySelectorAll('.dish-item input').forEach(checkbox => {
    if(checkbox.checked && !selectedDishes.includes(checkbox.value)) {
      selectedDishes.push(checkbox.value);
    }
    checkbox.addEventListener('change', function() {
      if(this.checked){
        if(!selectedDishes.includes(dish)) {
          selectedDishes.push(dish);
        }
      }else{
        selectedDishes = selectedDishes.filter(d => d !== dish);
      }
    });
  });
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
    document.querySelector('.card').style.display = '';
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
