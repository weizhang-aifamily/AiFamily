document.addEventListener('DOMContentLoaded', async () => {
    const memberId = window.location.pathname.split('/').pop();
    await loadAllData(memberId);
});

function renderMemberBasic(data) {
    document.getElementById('memberName').textContent = data.name;
    document.getElementById('memberDetail').textContent =
        `${data.age}岁 | 身高: ${data.height || '--'}cm | 体重: ${data.weight || '--'}kg`;
    document.getElementById('memberAvatar').textContent = data.name.charAt(0);
}

function renderHealthStatus(data) {
    const tagsContainer = document.getElementById('healthTags');

    // BMI状态
    if (data.bmi) {
        const bmiValue = parseFloat(data.bmi);
        let bmiStatus = '正常', bmiClass = 'tag-normal';
        if (bmiValue < 18.5) {
            bmiStatus = '偏低';
            bmiClass = 'tag-warning';
        } else if (bmiValue > 24) {
            bmiStatus = '偏高';
            bmiClass = 'tag-danger';
        }
        tagsContainer.innerHTML += `<span class="health-tag ${bmiClass}">BMI${bmiStatus}</span>`;
    }

    // 钙状态 (假设目标800mg)
    if (data.calcium) {
        const calciumValue = parseFloat(data.calcium);
        const calciumStatus = calciumValue < 800 ? '不足' : '正常';
        const calciumClass = calciumValue < 800 ? 'tag-warning' : 'tag-normal';
        tagsContainer.innerHTML += `<span class="health-tag ${calciumClass}">钙${calciumStatus}</span>`;
    }

    // 钠状态 (假设目标1500mg)
    if (data.sodium) {
        const sodiumValue = parseFloat(data.sodium);
        const sodiumStatus = sodiumValue > 1500 ? '超标' : '正常';
        const sodiumClass = sodiumValue > 1500 ? 'tag-danger' : 'tag-normal';
        tagsContainer.innerHTML += `<span class="health-tag ${sodiumClass}">钠${sodiumStatus}</span>`;
    }
}
async function loadAllData(memberId) {
    try {
        // 1. 基本信息
        const basicInfo = await (await fetch(`/members/${memberId}/basic`)).json();

        // 2. 健康状态
        const healthStatus = await (await fetch(`/members/${memberId}/health-status`)).json();

        // 3. 营养数据
        const nutritionData = await (await fetch(`/members/${memberId}/nutrition`)).json();

        // 4. 饮食排名
        const foodRanking = await (await fetch(`/members/${memberId}/food-ranking`)).json();

        // 渲染所有数据
        renderMemberBasic(basicInfo.data);
        renderHealthStatus(healthStatus.data);
        renderNutritionData(nutritionData.data);
        renderFoodRanking(foodRanking.data);

    } catch (error) {
        console.error('数据加载失败:', error);
        alert(`数据加载失败: ${error.message}`);
    }
}
function renderMemberData(basicInfo, healthStatus) {
    document.getElementById('memberName').textContent = basicInfo.name;
    document.getElementById('memberDetail').textContent =
        `${basicInfo.age}岁 | 身高: ${basicInfo.height || '--'}cm | 体重: ${basicInfo.weight || '--'}kg`;
    document.getElementById('memberAvatar').textContent = basicInfo.name.charAt(0);

    const tagsContainer = document.getElementById('healthTags');
    tagsContainer.innerHTML = ''; // 清空原有内容

    // BMI标签
    if (healthStatus.bmi) {
        const bmiValue = parseFloat(healthStatus.bmi);
        let bmiStatus = '正常', bmiClass = 'tag-normal';
        if (bmiValue < 18.5) bmiStatus = '偏低';
        if (bmiValue > 24) bmiStatus = '偏高';
        tagsContainer.innerHTML += `<span class="health-tag ${bmiClass}">BMI${bmiStatus}</span>`;
    }

    // 钙标签
    if (healthStatus.calcium) {
        const calciumStatus = healthStatus.calcium < 800 ? '不足' : '正常';
        const calciumClass = healthStatus.calcium < 800 ? 'tag-warning' : 'tag-normal';
        tagsContainer.innerHTML += `<span class="health-tag ${calciumClass}">钙${calciumStatus}</span>`;
    }

    // 钠标签
    if (healthStatus.sodium) {
        const sodiumStatus = healthStatus.sodium > 1500 ? '超标' : '正常';
        const sodiumClass = healthStatus.sodium > 1500 ? 'tag-danger' : 'tag-normal';
        tagsContainer.innerHTML += `<span class="health-tag ${sodiumClass}">钠${sodiumStatus}</span>`;
    }
}

// 新增营养数据渲染
function renderNutritionData(nutritionData) {
    const container = document.getElementById('nutritionGrid');
    if (!container) return;

    container.innerHTML = nutritionData.map(item => `
        <div class="nutrition-item">
            <div class="nutrition-label">${item.label}</div>
            <div class="nutrition-value">${item.current}/${item.target}${item.unit}</div>
            <div class="nutrition-percent">${item.percent}</div>
        </div>
    `).join('');
}

// 新增饮食排名渲染
function renderFoodRanking(foods) {
    const container = document.getElementById('foodRanking');
    if (!container) return;

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