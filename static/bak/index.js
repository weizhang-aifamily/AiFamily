document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面
    initPage();
});

async function initPage() {
    try {
        // 1. 加载家庭成员数据
        const members = await loadFamilyMembers();
        renderFamilyMembers(members);

        // 2. 默认选中第一个成员并加载其数据
        if (members.length > 0) {
            await selectMember(members[0].member_id);
        }
    } catch (error) {
        console.error('初始化失败:', error);
        alert('页面初始化失败，请刷新重试');
    }
}

// 加载家庭成员数据
async function loadFamilyMembers() {
    try {
        const response = await fetch('/members');
        const data = await response.json();
        if (data.status === 'success') {
            return data.data;
        }
        throw new Error(data.message || '获取家庭成员失败');
    } catch (error) {
        console.error('加载家庭成员失败:', error);
        return [];
    }
}

// 渲染家庭成员卡片
function renderFamilyMembers(members) {
    const container = document.querySelector('.family-members');
    if (!container) return;

    container.innerHTML = members.map(member => `
        <div class="member-card" data-id="${member.member_id}">
            <div class="member-name">${member.name} (${calculateAge(member.birth_date)}岁)</div>
            <div class="health-stats">
                ${member.bmi ? `<span class="stat-item">BMI: <span class="${getBmiClass(member.bmi)}">${getBmiStatus(member.bmi)}</span></span>` : ''}
                ${member.blood_pressure ? `<span class="stat-item">血压: <span class="${getBloodPressureClass(member.blood_pressure)}">${member.blood_pressure}</span></span>` : ''}
                ${member.oxygen_level ? `<span class="stat-item">缺氧: <span class="percent">${member.oxygen_level}%</span></span>` : ''}
            </div>
        </div>
    `).join('');

    // 添加点击事件
    document.querySelectorAll('.member-card').forEach(card => {
        card.addEventListener('click', async function() {
            document.querySelectorAll('.member-card').forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            const memberId = this.dataset.id;
            await selectMember(memberId);
        });
    });
}

// 选择成员加载相关数据
async function selectMember(memberId) {
    try {
        // 1. 加载成员健康详情
        const healthData = await fetchMemberHealth(memberId);

        // 2. 加载饮食方案
        const dietPlans = await fetchDietPlans(memberId);
        renderDietPlans(dietPlans);

        // 3. 如果有方案，加载第一个方案的菜品
        if (dietPlans.length > 0) {
            await loadDishes(dietPlans[0].plan_id);
        }
    } catch (error) {
        console.error('加载成员数据失败:', error);
    }
}

// 获取成员健康数据
async function fetchMemberHealth(memberId) {
    const response = await fetch(`/members/${memberId}/health-status`);
    const data = await response.json();
    if (data.status !== 'success') throw new Error(data.message);
    return data.data;
}

// 获取饮食方案
async function fetchDietPlans(memberId) {
    const response = await fetch(`/diet/plans/${memberId}`);
    const data = await response.json();
    if (data.status !== 'success') throw new Error(data.message);
    return data.data;
}

// 渲染饮食方案
function renderDietPlans(plans) {
    const container = document.querySelector('.diet-plan-section');
    if (!container || !plans.length) return;

    // 简化显示，只展示第一个方案
    const plan = plans[0];

    // 更新膳食方案
    const nutritionResponse = fetch(`/diet/requirements/${plan.plan_id}`)
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                const supplyList = document.querySelector('.supply-list');
                if (supplyList) {
                    supplyList.innerHTML = `
                        <li><strong>供给</strong></li>
                        ${data.data.map(item => `
                            <li>${item.nutrient_type}：${item.amount}${item.unit}</li>
                        `).join('')}
                    `;
                }
            }
        });

    // 更新推荐食材
    fetch('/diet/foods/recommended')
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success' && data.data.length >= 2) {
                const food1 = data.data[0];
                const food2 = data.data[1];
                const table = document.querySelector('.food-comparison table');
                if (table) {
                    table.innerHTML = `
                        <tr>
                            <th>${food1.food_name}</th>
                            <th>${food2.food_name}</th>
                        </tr>
                        <tr>
                            <td>钙含量: ${getNutrientValue(food1, '钙')}</td>
                            <td>${getNutrientValue(food2, '钙')}</td>
                        </tr>
                        <tr>
                            <td>胡萝卜素: ${getNutrientValue(food1, '胡萝卜素')}</td>
                            <td>${getNutrientValue(food2, '胡萝卜素')}</td>
                        </tr>
                        <tr>
                            <td>维生素A: ${getNutrientValue(food1, '维生素A')}</td>
                            <td>${getNutrientValue(food2, '维生素A')}</td>
                        </tr>
                    `;
                }
            }
        });
}

// 加载菜品
async function loadDishes(planId) {
    try {
        const response = await fetch(`/diet/dishes/${planId}`);
        const data = await response.json();
        if (data.status === 'success') {
            renderDishes(data.data);
        }
    } catch (error) {
        console.error('加载菜品失败:', error);
    }
}

// 渲染菜品
function renderDishes(dishes) {
    const container = document.querySelector('.dish-list');
    if (!container) return;

    container.innerHTML = dishes.map(dish => `
        <div class="dish-item">
            <span>${dish.dish_name}: <span class="percent">${dish.rating || 10}%</span></span>
        </div>
    `).join('');
}

// 刷新菜品
async function refreshDishes() {
    const activePlan = document.querySelector('.diet-plan-section')?.dataset?.planId;
    if (!activePlan) return;

    try {
        const response = await fetch('/diet/dishes/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({plan_id: activePlan})
        });
        const data = await response.json();
        if (data.status === 'success') {
            await loadDishes(activePlan);
        }
    } catch (error) {
        console.error('刷新菜品失败:', error);
    }
}

// 工具函数
function calculateAge(birthDate) {
    const today = new Date();
    const birth = new Date(birthDate);
    let age = today.getFullYear() - birth.getFullYear();
    const m = today.getMonth() - birth.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
    return age;
}

function getBmiStatus(bmi) {
    if (bmi < 18.5) return '偏低';
    if (bmi > 24) return '偏高';
    return '正常';
}

function getBmiClass(bmi) {
    if (bmi < 18.5) return 'low';
    if (bmi > 24) return 'high';
    return 'normal';
}

function getBloodPressureClass(bp) {
    return bp === '偏高' ? 'high' : 'normal';
}

function getNutrientValue(food, nutrient) {
    const nutrition = food.nutritions?.find(n => n.nutrient_type === nutrient);
    return nutrition ? `${nutrition.amount}${nutrition.unit}` : '--';
}

// 绑定刷新按钮事件
document.querySelector('.refresh-btn')?.addEventListener('click', refreshDishes);