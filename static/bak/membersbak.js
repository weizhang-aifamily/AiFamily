// members.js
document.addEventListener('DOMContentLoaded', async () => {
    const memberId = window.location.pathname.split('/').pop();
    await loadMemberDetails(memberId);
    await loadHealthMetrics(memberId);
    await loadNutritionData(memberId);
    await loadFoodRanking(memberId);
});

async function loadMemberDetails(memberId) {
    try {
        const response = await fetch(`/api/members/${memberId}`);
        const data = await response.json();
        renderMemberDetails(data.data);
    } catch (error) {
        console.error('加载成员详情失败:', error);
    }
}

function renderMemberDetails(member) {
    document.getElementById('memberName').textContent = member.name;

    // 计算年龄
    const birthDate = new Date(member.birth_date);
    const ageDiff = Date.now() - birthDate.getTime();
    const ageDate = new Date(ageDiff);
    const age = Math.abs(ageDate.getUTCFullYear() - 1970);

    document.getElementById('memberInfo').textContent =
        `${age}岁 | 身高: ${member.height || '--'}cm | 体重: ${member.weight || '--'}kg`;
}

async function loadHealthMetrics(memberId) {
    try {
        const response = await fetch(`/api/members/${memberId}/metrics/latest`);
        const data = await response.json();
        renderHealthStatus(data.data);
    } catch (error) {
        console.error('加载健康指标失败:', error);
    }
}

function renderHealthStatus(metrics) {
    const container = document.getElementById('metricsGrid');

    // 创建状态标签
    const statusTags = document.createElement('div');
    statusTags.className = 'status-tags';

    // BMI状态
    if (metrics.BMI) {
        const bmiValue = parseFloat(metrics.BMI.metric_value);
        let bmiStatus = '正常';
        let bmiClass = 'status-normal';

        if (bmiValue < 18.5) {
            bmiStatus = '偏低';
            bmiClass = 'status-warning';
        } else if (bmiValue > 24) {
            bmiStatus = '偏高';
            bmiClass = 'status-danger';
        }

        statusTags.innerHTML += `
            <span class="status-tag ${bmiClass}">BMI${bmiStatus}</span>
        `;
    }

    // 钙状态
    if (metrics.CALCIUM) {
        const calciumValue = parseFloat(metrics.CALCIUM.metric_value);
        const calciumStatus = calciumValue < 800 ? '不足' : '正常';
        const calciumClass = calciumValue < 800 ? 'status-warning' : 'status-normal';

        statusTags.innerHTML += `
            <span class="status-tag ${calciumClass}">钙${calciumStatus}</span>
        `;
    }

    // 钠状态
    if (metrics.SODIUM) {
        const sodiumValue = parseFloat(metrics.SODIUM.metric_value);
        const sodiumStatus = sodiumValue > 1500 ? '超标' : '正常';
        const sodiumClass = sodiumValue > 1500 ? 'status-danger' : 'status-normal';

        statusTags.innerHTML += `
            <span class="status-tag ${sodiumClass}">钠${sodiumStatus}</span>
        `;
    }

    container.appendChild(statusTags);
}

async function loadNutritionData(memberId) {
    try {
        const response = await fetch(`/api/members/${memberId}/nutrition`);
        const data = await response.json();
        renderNutritionOverview(data.data);
    } catch (error) {
        console.error('加载营养数据失败:', error);
    }
}

function renderNutritionOverview(nutrition) {
    const container = document.createElement('div');
    container.className = 'nutrition-overview';

    container.innerHTML = `
        <h3 class="section-title">营养摄入概览</h3>
        <div class="nutrition-item">
            <span class="nutrition-label">能量</span>
            <div>
                <span class="nutrition-value">${nutrition.energy.value}/${nutrition.energy.target}kcal</span>
                <span class="nutrition-percent">(${Math.round(nutrition.energy.value/nutrition.energy.target*100)}%)</span>
            </div>
        </div>
        <div class="nutrition-item">
            <span class="nutrition-label">蛋白质</span>
            <div>
                <span class="nutrition-value">${nutrition.protein.value}/${nutrition.protein.target}g</span>
                <span class="nutrition-percent">(${Math.round(nutrition.protein.value/nutrition.protein.target*100)}%)</span>
            </div>
        </div>
        <div class="nutrition-item">
            <span class="nutrition-label">钙</span>
            <div>
                <span class="nutrition-value">${nutrition.calcium.value}/${nutrition.calcium.target}mg</span>
                <span class="nutrition-percent">(${Math.round(nutrition.calcium.value/nutrition.calcium.target*100)}%)</span>
            </div>
        </div>
        <div class="nutrition-item">
            <span class="nutrition-label">铁</span>
            <div>
                <span class="nutrition-value">${nutrition.iron.value}/${nutrition.iron.target}mg</span>
                <span class="nutrition-percent">(${Math.round(nutrition.iron.value/nutrition.iron.target*100)}%)</span>
            </div>
        </div>
        <div class="nutrition-item">
            <span class="nutrition-label">锌</span>
            <div>
                <span class="nutrition-value">${nutrition.zinc.value}/${nutrition.zinc.target}mg</span>
                <span class="nutrition-percent">(${Math.round(nutrition.zinc.value/nutrition.zinc.target*100)}%)</span>
            </div>
        </div>
        <div class="nutrition-item">
            <span class="nutrition-label">钠</span>
            <div>
                <span class="nutrition-value">${nutrition.sodium.value}/${nutrition.sodium.target}mg</span>
                <span class="nutrition-percent">(${Math.round(nutrition.sodium.value/nutrition.sodium.target*100)}%)</span>
            </div>
        </div>
    `;

    document.querySelector('.container').appendChild(container);
}

async function loadFoodRanking(memberId) {
    try {
        const response = await fetch(`/api/members/${memberId}/food-ranking`);
        const data = await response.json();
        renderFoodRanking(data.data);
    } catch (error) {
        console.error('加载食物排名失败:', error);
    }
}

function renderFoodRanking(foods) {
    const container = document.createElement('div');
    container.className = 'food-ranking';

    container.innerHTML = `
        <h3 class="section-title">饮食分析与排名</h3>
        <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
            <span style="font-weight: 500;">菜品排名</span>
            <span style="font-weight: 500;">食材排名</span>
        </div>
    `;

    foods.forEach(food => {
        const foodItem = document.createElement('div');
        foodItem.className = 'food-item';

        foodItem.innerHTML = `
            <span class="food-name">${food.name}</span>
            <div class="food-tags">
                ${food.tags.map(tag => `<span class="food-tag">${tag}</span>`).join('')}
            </div>
        `;

        container.appendChild(foodItem);
    });

    // 添加快速记录
    const quickRecord = document.createElement('div');
    quickRecord.className = 'quick-record';
    quickRecord.innerHTML = `
        <span class="quick-record-item">本周${foods[0].count}次</span>
        <span class="quick-record-item">本周${foods[1].count}次</span>
        <span class="quick-record-item">本周${foods[2].count}次</span>
    `;

    container.appendChild(quickRecord);

    document.querySelector('.container').appendChild(container);
}
// members.js - 精确数据加载
document.addEventListener('DOMContentLoaded', async () => {
    const memberId = window.location.pathname.split('/').pop();
    await loadMemberData(memberId);
    await loadNutritionData(memberId);
});

async function loadMemberData(memberId) {
    try {
        // 模拟API响应 - 实际应从后端获取
        const memberData = {
            name: "小明",
            age: 8,
            height: 130,
            weight: 28,
            bmi: 16.6, // 正常范围
            calcium: 650, // 不足(低于800)
            sodium: 2200 // 超标(高于1500)
        };

        renderMemberData(memberData);
    } catch (error) {
        console.error('加载成员数据失败:', error);
    }
}

function renderMemberData(data) {
    // 更新基本信息
    document.getElementById('memberName').textContent = data.name;
    document.getElementById('memberDetail').textContent =
        `${data.age}岁 | 身高: ${data.height}cm | 体重: ${data.weight}kg`;

    // 更新健康标签
    const tagsContainer = document.getElementById('healthTags');

    // BMI标签
    let bmiStatus = '正常';
    let bmiClass = 'tag-normal';
    if (data.bmi < 18.5) bmiStatus = '偏低';
    if (data.bmi > 24) bmiStatus = '偏高';

    // 钙标签
    const calciumStatus = data.calcium < 800 ? '不足' : '正常';
    const calciumClass = data.calcium < 800 ? 'tag-warning' : 'tag-normal';

    // 钠标签
    const sodiumStatus = data.sodium > 1500 ? '超标' : '正常';
    const sodiumClass = data.sodium > 1500 ? 'tag-danger' : 'tag-normal';

    tagsContainer.innerHTML = `
        <span class="health-tag ${bmiClass}">BMI${bmiStatus}</span>
        <span class="health-tag ${calciumClass}">钙${calciumStatus}</span>
        <span class="health-tag ${sodiumClass}">钠${sodiumStatus}</span>
    `;
}

async function loadNutritionData(memberId) {
    try {
        // 模拟API响应 - 实际应从后端获取
        const nutritionData = [
            { label: "能量", value: "1450/1800", percent: "81%", unit: "kcal" },
            { label: "蛋白质", value: "48/60", percent: "80%", unit: "g" },
            { label: "钙", value: "650/800", percent: "81%", unit: "mg" },
            { label: "铁", value: "8/10", percent: "80%", unit: "mg" },
            { label: "锌", value: "6/8", percent: "75%", unit: "mg" },
            { label: "钠", value: "2200/1500", percent: "147%", unit: "mg" }
        ];

        renderNutritionData(nutritionData);
    } catch (error) {
        console.error('加载营养数据失败:', error);
    }
}

function renderNutritionData(data) {
    const container = document.getElementById('nutritionGrid');

    container.innerHTML = data.map(item => `
        <div class="nutrition-item">
            <div class="nutrition-label">${item.label}</div>
            <div class="nutrition-value">${item.value}${item.unit}</div>
            <div class="nutrition-percent">${item.percent}</div>
        </div>
    `).join('');
}
document.addEventListener('DOMContentLoaded', async () => {
    const memberId = window.location.pathname.split('/').pop();
    await loadMemberData(memberId);
    await loadNutritionData(memberId);
    await loadFoodRanking(memberId);

    // 初始化幻灯片
    initSlider();
});

let currentSlide = 0;
let slideInterval;

function initSlider() {
    const slides = document.querySelectorAll('.slide');
    const indicators = document.querySelectorAll('.indicator');

    // 设置自动轮播
    slideInterval = setInterval(() => {
        goToSlide((currentSlide + 1) % slides.length);
    }, 2000);

    // 指示器点击事件
    indicators.forEach((indicator, index) => {
        indicator.addEventListener('click', () => {
            clearInterval(slideInterval);
            goToSlide(index);
            // 重新启动自动轮播
            slideInterval = setInterval(() => {
                goToSlide((currentSlide + 1) % slides.length);
            }, 2000);
        });
    });
}

function goToSlide(slideIndex) {
    const slides = document.querySelectorAll('.slide');
    const indicators = document.querySelectorAll('.indicator');
    const slider = document.querySelector('.slider');

    // 更新当前幻灯片索引
    currentSlide = slideIndex;

    // 移动幻灯片
    slider.style.transform = `translateX(-${currentSlide * 100}%)`;

    // 更新活动状态
    slides.forEach((slide, index) => {
        slide.classList.toggle('active', index === currentSlide);
    });

    indicators.forEach((indicator, index) => {
        indicator.classList.toggle('active', index === currentSlide);
    });
}

async function loadMemberData(memberId) {
    try {
        const response = await fetch(`/api/members/${memberId}/full-health`);
        const data = await response.json();

        renderMemberData(data.data.basic_info, data.data.health_status);
    } catch (error) {
        console.error('加载成员数据失败:', error);
    }
}

function renderMemberData(basicInfo, healthStatus) {
    document.getElementById('memberName').textContent = basicInfo.name;
    document.getElementById('memberDetail').textContent =
        `${basicInfo.age}岁 | 身高: ${basicInfo.height}cm | 体重: ${basicInfo.weight}kg`;

    document.getElementById('memberAvatar').textContent = basicInfo.name.charAt(0);

    const tagsContainer = document.getElementById('healthTags');

    // BMI标签
    let bmiStatus = '正常';
    let bmiClass = 'tag-normal';
    if (healthStatus.bmi < 18.5) bmiStatus = '偏低';
    if (healthStatus.bmi > 24) bmiStatus = '偏高';

    // 钙标签
    const calciumStatus = healthStatus.calcium < 800 ? '不足' : '正常';
    const calciumClass = healthStatus.calcium < 800 ? 'tag-warning' : 'tag-normal';

    // 钠标签
    const sodiumStatus = healthStatus.sodium > 1500 ? '超标' : '正常';
    const sodiumClass = healthStatus.sodium > 1500 ? 'tag-danger' : 'tag-normal';

    tagsContainer.innerHTML = `
        <span class="health-tag ${bmiClass}">BMI${bmiStatus}</span>
        <span class="health-tag ${calciumClass}">钙${calciumStatus}</span>
        <span class="health-tag ${sodiumClass}">钠${sodiumStatus}</span>
    `;
}

async function loadNutritionData(memberId) {
    try {
        const response = await fetch(`/api/members/${memberId}/full-health`);
        const data = await response.json();

        renderNutritionData(data.data.nutrition);
    } catch (error) {
        console.error('加载营养数据失败:', error);
    }
}

function renderNutritionData(nutritionData) {
    const container = document.getElementById('nutritionGrid');

    container.innerHTML = nutritionData.map(item => `
        <div class="nutrition-item">
            <div class="nutrition-label">${item.label}</div>
            <div class="nutrition-value">${item.value}${item.unit}</div>
            <div class="nutrition-percent">${item.percent}</div>
        </div>
    `).join('');
}

async function loadFoodRanking(memberId) {
    try {
        const response = await fetch(`/api/members/${memberId}/full-health`);
        const data = await response.json();

        renderFoodRanking(data.data.food_ranking);
    } catch (error) {
        console.error('加载食物排名失败:', error);
    }
}

function renderFoodRanking(foods) {
    const container = document.getElementById('foodRanking');

    container.innerHTML = foods.map((food, index) => `
        <div class="food-item">
            <span class="rank">${index + 1}</span>
            <div class="food-info">
                <span class="food-name">${food.name}</span>
                <div class="food-tags">
                    ${food.tags.map(tag => `<span class="tag ${getTagClass(tag)}">${tag}</span>`).join('')}
                </div>
            </div>
            <span class="count">本周${food.count}次</span>
        </div>
    `).join('');
}

function getTagClass(tag) {
    if (tag.includes('高钠')) return 'high-sodium';
    if (tag.includes('高热量')) return 'high-calorie';
    if (tag.includes('高脂肪')) return 'high-fat';
    if (tag.includes('碳水化合物')) return 'carb';
    if (tag.includes('低纤维')) return 'low-fiber';
    return '';
}
// members.js - 精确数据加载
document.addEventListener('DOMContentLoaded', async () => {
    const memberId = window.location.pathname.split('/').pop();
    await loadMemberData(memberId);
    await loadNutritionData(memberId);
});

async function loadMemberData(memberId) {
    try {
        // 模拟API响应 - 实际应从后端获取
        const memberData = {
            name: "小明",
            age: 8,
            height: 130,
            weight: 28,
            bmi: 16.6, // 正常范围
            calcium: 650, // 不足(低于800)
            sodium: 2200 // 超标(高于1500)
        };

        renderMemberData(memberData);
    } catch (error) {
        console.error('加载成员数据失败:', error);
    }
}

function renderMemberData(data) {
    // 更新基本信息
    document.getElementById('memberName').textContent = data.name;
    document.getElementById('memberDetail').textContent =
        `${data.age}岁 | 身高: ${data.height}cm | 体重: ${data.weight}kg`;

    // 更新健康标签
    const tagsContainer = document.getElementById('healthTags');

    // BMI标签
    let bmiStatus = '正常';
    let bmiClass = 'tag-normal';
    if (data.bmi < 18.5) bmiStatus = '偏低';
    if (data.bmi > 24) bmiStatus = '偏高';

    // 钙标签
    const calciumStatus = data.calcium < 800 ? '不足' : '正常';
    const calciumClass = data.calcium < 800 ? 'tag-warning' : 'tag-normal';

    // 钠标签
    const sodiumStatus = data.sodium > 1500 ? '超标' : '正常';
    const sodiumClass = data.sodium > 1500 ? 'tag-danger' : 'tag-normal';

    tagsContainer.innerHTML = `
        <span class="health-tag ${bmiClass}">BMI${bmiStatus}</span>
        <span class="health-tag ${calciumClass}">钙${calciumStatus}</span>
        <span class="health-tag ${sodiumClass}">钠${sodiumStatus}</span>
    `;
}

async function loadNutritionData(memberId) {
    try {
        // 模拟API响应 - 实际应从后端获取
        const nutritionData = [
            { label: "能量", value: "1450/1800", percent: "81%", unit: "kcal" },
            { label: "蛋白质", value: "48/60", percent: "80%", unit: "g" },
            { label: "钙", value: "650/800", percent: "81%", unit: "mg" },
            { label: "铁", value: "8/10", percent: "80%", unit: "mg" },
            { label: "锌", value: "6/8", percent: "75%", unit: "mg" },
            { label: "钠", value: "2200/1500", percent: "147%", unit: "mg" }
        ];

        renderNutritionData(nutritionData);
    } catch (error) {
        console.error('加载营养数据失败:', error);
    }
}

function renderNutritionData(data) {
    const container = document.getElementById('nutritionGrid');

    container.innerHTML = data.map(item => `
        <div class="nutrition-item">
            <div class="nutrition-label">${item.label}</div>
            <div class="nutrition-value">${item.value}${item.unit}</div>
            <div class="nutrition-percent">${item.percent}</div>
        </div>
    `).join('');
}