import { CONFIG } from './config.js';
import { calculateUserNutritionRatios, analyzeNutrition, updateMembers } from './nutritionDataLoader.js';
/* ========== 显示营养元素及身材图片 ========== */
export async function displayNutrients(comboData) {
    if (!comboData || comboData.length === 0) return;

    // 汇总所有套餐的营养数据
    const totalNutrients = {
        calories_intake: 0,
        protein_g: 0,
        fat_g: 0,
        carbs_g: 0
    };

    // 遍历所有套餐，累加营养数据
    comboData.forEach(combo => {
        if (combo.nutrients) {
            totalNutrients.calories_intake += combo.nutrients.EnergyKCal || 0;
            totalNutrients.protein_g += combo.nutrients.Protein || 0;
            totalNutrients.fat_g += combo.nutrients.Fat || 0;
            totalNutrients.carbs_g += combo.nutrients.Carbohydrate || 0;
        }
    });
    totalNutrients.calories_intake = parseFloat(totalNutrients.calories_intake.toFixed(1));
    totalNutrients.protein_g = parseFloat(totalNutrients.protein_g.toFixed(1));
    totalNutrients.fat_g = parseFloat(totalNutrients.fat_g.toFixed(1));
    totalNutrients.carbs_g = parseFloat(totalNutrients.carbs_g.toFixed(1));

    const activeMembers = window.activeMembers || [];
    console.log('activeMembers:', window.activeMembers);

    const daysInput = document.getElementById('predictionDays');
    const days = daysInput ? parseInt(daysInput.value) : 90;
    try {
        const ratios = await calculateUserNutritionRatios(activeMembers, activeMembers);
        // 为每个用户分配营养数据
        const usersAnalysisData = activeMembers.map(user => {
//            const userRatio = analyzer.calculateUserNutritionRatio(user, activeMembers, analyzer);
            const userRatio = ratios[user.member_id];

            const userData = {
                id: user.member_id,
                name: user.name,
                gender: user.gender || 'male',
                age: parseFloat(user.age) || 30,
                ageGroup: user.ageGroup || 'middle',
                height_cm: parseFloat(user.height_cm) || 170,
                weight_kg: parseFloat(user.weight_kg) || 65,
                calories_intake: totalNutrients.calories_intake * userRatio,
                protein_g: totalNutrients.protein_g * userRatio,
                fat_g: totalNutrients.fat_g * userRatio,
                carbs_g: totalNutrients.carbs_g * userRatio,
                exerciseFrequency: user.exerciseFrequency || 'moderate',
                exerciseDuration: user.exerciseDuration || 'medium',
                exerciseIntensity: user.exerciseIntensity || 'medium'
            };

            return userData;
        });
        // 执行营养分析（自动适配n个人）
//        const results = analyzer.analyze(usersAnalysisData, days);
        const results = await analyzeNutrition(usersAnalysisData, days);
        console.log("results",results)
        updateUserCard(results);
        generateNutritionMini(results);
        displayUserInfoForm(results);
    } catch (error) {
        console.error('营养分析失败:', error);
    }
}
/* ========== 生成缩略版营养展示（一行显示） ========== */
function generateNutritionMini(results) {
    if (!results) return;

    // 处理单用户和多用户情况
    const resultsArray = Array.isArray(results) ? results : [results];

    const content = document.getElementById('nutritionMiniContent');
    if (!content) return;

    // 汇总所有用户的营养数据
    const totalUserInput = {
        calories_intake: 0,
        protein_g: 0,
        fat_g: 0,
        carbs_g: 0
    };

    const totalBaseline = {
        calories: 0,
        protein_g: 0,
        fat_g: 0,
        carbs_g: 0
    };

    const totalDifferences = {
        absolute: {
            calories: 0,
            protein_g: 0,
            fat_g: 0,
            carbs_g: 0
        }
    };

    // 累加所有用户的营养数据
    resultsArray.forEach(result => {
        const { user_input, baseline, differences } = result;

        totalUserInput.calories_intake += user_input.calories_intake || 0;
        totalUserInput.protein_g += user_input.protein_g || 0;
        totalUserInput.fat_g += user_input.fat_g || 0;
        totalUserInput.carbs_g += user_input.carbs_g || 0;

        totalBaseline.calories += baseline.calories || 0;
        totalBaseline.protein_g += baseline.protein_g || 0;
        totalBaseline.fat_g += baseline.fat_g || 0;
        totalBaseline.carbs_g += baseline.carbs_g || 0;

        totalDifferences.absolute.calories += differences.absolute.calories || 0;
        totalDifferences.absolute.protein_g += differences.absolute.protein_g || 0;
        totalDifferences.absolute.fat_g += differences.absolute.fat_g || 0;
        totalDifferences.absolute.carbs_g += differences.absolute.carbs_g || 0;
    });

    // 计算百分比（限制在0-150%）
    const getPercentage = (actual, baseline) => {
        if (baseline === 0) return 0;
        return Math.min((actual / baseline) * 100, 150);
    };

    // 获取差值样式
    const getDifferenceClass = (diff) => {
        if (diff > 0) return 'difference-positive';
        if (diff < 0) return 'difference-negative';
        return 'difference-neutral';
    };

    // 获取差值文本
    const getDifferenceText = (diff, unit = '') => {
        if (diff > 0) return `+${diff}${unit}`;
        if (diff < 0) return `${diff}${unit}`;
        return `±0${unit}`;
    };

    // 营养数据配置（使用汇总数据）
    const nutrients = [
        {
            label: '热量',
            type: 'calories',
            actual: totalUserInput.calories_intake,
            baseline: totalBaseline.calories,
            diff: totalDifferences.absolute.calories,
            unit: 'kcal',
            percentage: getPercentage(totalUserInput.calories_intake, totalBaseline.calories)
        },
        {
            label: '蛋白质',
            type: 'protein',
            actual: totalUserInput.protein_g,
            baseline: totalBaseline.protein_g,
            diff: totalDifferences.absolute.protein_g,
            unit: 'g',
            percentage: getPercentage(totalUserInput.protein_g, totalBaseline.protein_g)
        },
        {
            label: '脂肪',
            type: 'fat',
            actual: totalUserInput.fat_g,
            baseline: totalBaseline.fat_g,
            diff: totalDifferences.absolute.fat_g,
            unit: 'g',
            percentage: getPercentage(totalUserInput.fat_g, totalBaseline.fat_g)
        },
        {
            label: '碳水',
            type: 'carbs',
            actual: totalUserInput.carbs_g,
            baseline: totalBaseline.carbs_g,
            diff: totalDifferences.absolute.carbs_g,
            unit: 'g',
            percentage: getPercentage(totalUserInput.carbs_g, totalBaseline.carbs_g)
        }
    ];

    // 生成HTML - 一行布局
    const html = `
        <div class="nutrition-mini-bar">
            ${nutrients.map(nutrient => `
                <div class="nutrient-mini-item">
                    <div class="nutrient-mini-header">
                        <span class="nutrient-mini-label">${nutrient.label}</span>
                        <span class="nutrient-mini-value">${Math.round(nutrient.actual)}${nutrient.unit}</span>
                    </div>
                    <div class="mini-bar-container">
                        <div class="mini-bar-fill ${nutrient.type}"
                             style="width: ${nutrient.percentage}%"
                             title="${nutrient.label}: ${Math.round(nutrient.actual)}${nutrient.unit} (${Math.round(nutrient.percentage)}%)">
                        </div>
                    </div>
                    <div class="nutrient-mini-diff ${getDifferenceClass(nutrient.diff)}">
                        ${getDifferenceText(Math.round(nutrient.diff), nutrient.unit)}
                    </div>
                </div>
            `).join('')}
        </div>
    `;

    content.innerHTML = html;
}
/* ========== 显示可编辑的用户信息表单（移动端优化） ========== */
function displayUserInfoForm(results) {
    if (!results) return;

    // 处理单用户和多用户情况
    const resultsArray = Array.isArray(results) ? results : [results];

    const container = document.getElementById('userInfoFormContainer');

    const formsHTML = resultsArray.map((userResult, index) => {
        const user = userResult.user_input;
        let actionButtons = '';
        if (index === 0) {
            actionButtons = `
                <button type="button" class="btn-save" onclick="saveUserInfo('${user.id}')">保存</button>
                <button type="button" class="btn-cancel" onclick="resetUserInfo('${user.id}')">重置</button>
            `;
        }
        return `
            <div class="user-info-form" data-user-id="${user.id}">
                <div class="form-header">
                    <h3></h3>
                    <div class="form-actions">
                        ${actionButtons}
                    </div>
                </div>

                <div class="form-grid">
                    <div class="form-group">
                        <label for="name-${user.id}">姓名</label>
                        <input type="text" id="name-${user.id}" value="${user.name}" class="form-input">
                    </div>

                    <div class="form-group">
                        <label for="gender-${user.id}">性别</label>
                        <select id="gender-${user.id}" class="form-select">
                            <option value="male" ${user.gender === 'male' ? 'selected' : ''}>男</option>
                            <option value="female" ${user.gender === 'female' ? 'selected' : ''}>女</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="age-${user.id}">年龄</label>
                        <input type="number" id="age-${user.id}" value="${user.age}" min="1" max="120" class="form-input">
                    </div>

                    <div class="form-group">
                        <label for="ageGroup-${user.id}">年龄段</label>
                        <select id="ageGroup-${user.id}" class="form-select">
                            <option value="young" ${user.ageGroup === 'young' ? 'selected' : ''}>青年</option>
                            <option value="middle" ${user.ageGroup === 'middle' ? 'selected' : ''}>中年</option>
                            <option value="old" ${user.ageGroup === 'old' ? 'selected' : ''}>老年</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="height-${user.id}">身高 (cm)</label>
                        <input type="number" id="height-${user.id}" value="${user.height_cm}" min="50" max="250" class="form-input">
                    </div>

                    <div class="form-group">
                        <label for="weight-${user.id}">体重 (kg)</label>
                        <input type="number" id="weight-${user.id}" value="${user.weight_kg}" min="20" max="200" step="0.1" class="form-input">
                    </div>

                    <div class="form-group full-width">
                        <label class="section-label">运动习惯</label>
                    </div>

                    <div class="form-group">
                        <label for="exerciseFrequency-${user.id}">频率</label>
                        <select id="exerciseFrequency-${user.id}" class="form-select">
                            <option value="low" ${user.exerciseFrequency === 'low' ? 'selected' : ''}>低</option>
                            <option value="moderate" ${user.exerciseFrequency === 'moderate' ? 'selected' : ''}>中</option>
                            <option value="high" ${user.exerciseFrequency === 'high' ? 'selected' : ''}>高</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="exerciseDuration-${user.id}">时长</label>
                        <select id="exerciseDuration-${user.id}" class="form-select">
                            <option value="short" ${user.exerciseDuration === 'short' ? 'selected' : ''}>短</option>
                            <option value="medium" ${user.exerciseDuration === 'medium' ? 'selected' : ''}>中</option>
                            <option value="long" ${user.exerciseDuration === 'long' ? 'selected' : ''}>长</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="exerciseIntensity-${user.id}">强度</label>
                        <select id="exerciseIntensity-${user.id}" class="form-select">
                            <option value="low" ${user.exerciseIntensity === 'low' ? 'selected' : ''}>低</option>
                            <option value="medium" ${user.exerciseIntensity === 'medium' ? 'selected' : ''}>中</option>
                            <option value="high" ${user.exerciseIntensity === 'high' ? 'selected' : ''}>高</option>
                        </select>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = formsHTML;

}

/* ========== 保存用户信息 ========== */
function saveUserInfo(userId) {
    const form = document.querySelector(`.user-info-form[data-user-id="${userId}"]`);
    if (!form) return;

    const updatedUser = [{
        member_id: userId,
        name: document.getElementById(`name-${userId}`).value,
        gender: document.getElementById(`gender-${userId}`).value,
        age: parseFloat(document.getElementById(`age-${userId}`).value),
        ageGroup: document.getElementById(`ageGroup-${userId}`).value,
        height_cm: parseFloat(document.getElementById(`height-${userId}`).value),
        weight_kg: parseFloat(document.getElementById(`weight-${userId}`).value),
        exerciseFrequency: document.getElementById(`exerciseFrequency-${userId}`).value,
        exerciseDuration: document.getElementById(`exerciseDuration-${userId}`).value,
        exerciseIntensity: document.getElementById(`exerciseIntensity-${userId}`).value
    }];
    (async () => {
        console.log('activeMembers：', activeMembers);
        result = await updateMembers({
            members: updatedUser
        });

    })();

    // 显示保存成功提示
    showNotification('信息已更新', 'success');
}

/* ========== 重置用户信息 ========== */
function resetUserInfo(userId) {
    if (window.activeMembers) {
        const originalUser = window.activeMembers.find(user => user.member_id === userId);
        if (originalUser) {
            document.getElementById(`name-${userId}`).value = originalUser.name;
            document.getElementById(`gender-${userId}`).value = originalUser.gender || 'male';
            document.getElementById(`age-${userId}`).value = parseFloat(originalUser.age) || 30;
            document.getElementById(`ageGroup-${userId}`).value = originalUser.ageGroup || 'middle';
            document.getElementById(`height-${userId}`).value = parseFloat(originalUser.height_cm) || 170;
            document.getElementById(`weight-${userId}`).value = parseFloat(originalUser.weight_kg) || 65;
            document.getElementById(`exerciseFrequency-${userId}`).value = originalUser.exerciseFrequency || 'moderate';
            document.getElementById(`exerciseDuration-${userId}`).value = originalUser.exerciseDuration || 'medium';
            document.getElementById(`exerciseIntensity-${userId}`).value = originalUser.exerciseIntensity || 'medium';
        }
    }
}
window.saveUserInfo = saveUserInfo;
window.resetUserInfo = resetUserInfo;
/* ========== 显示通知 ========== */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 2000);
}
function updateUserCard(results) {
    // 处理单用户和多用户情况
    const resultsArray = Array.isArray(results) ? results : [results];

    const bodyImagePreview = document.getElementById('bodyImagePreview');
    if (bodyImagePreview) bodyImagePreview.style.display = 'flex';

    // 清空现有内容并重新生成所有用户图片
    bodyImagePreview.innerHTML = '';

    // 为每个用户生成图片元素
    resultsArray.forEach((result) => {
        const userId = result.user_input.id;
        const weight_shift_kg = result.prediction.weight_shift_kg;
        const name = result.user_input.name;
        const html = `<div class="image-group">
        <img id="${userId}" class="bodyImage" src="${CONFIG.STATIC_BASE_URL}${result.body_image.future.image_path}" alt="身材预览">
        <div class="image-info" id="imageInfo">${name}${weight_shift_kg}kg</div></div>`;
        bodyImagePreview.insertAdjacentHTML('beforeend', html);
    });

}