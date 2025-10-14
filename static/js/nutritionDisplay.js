import { AdvancedNutritionAnalyzer } from './nutritionAnalyzer.js';
import { CONFIG } from './config.js';
/* ========== 显示营养元素及身材图片 ========== */
export function displayNutrients(comboData) {
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

    // 定义多用户数据（包含用户id）
    const formData = [
        {
            id: 'user1',
            gender: 'male',
            age: 35,
            ageGroup: 'middle',
            height_cm: 175,
            weight_kg: 70,
            exerciseFrequency: 'moderate',
            exerciseDuration: 'medium',
            exerciseIntensity: 'medium'
        },
        {
            id: 'user2',
            gender: 'female',
            age: 28,
            ageGroup: 'young',
            height_cm: 165,
            weight_kg: 55,
            exerciseFrequency: 'light',
            exerciseDuration: 'medium',
            exerciseIntensity: 'low'
        }
        // 可以继续添加更多用户...
    ];
    console.log(formData)
    const activeMembers = window.activeMembers || [];
    console.log('activeMembers:', window.activeMembers);
    // 创建营养分析器实例
    const analyzer = new AdvancedNutritionAnalyzer();
    const daysInput = document.getElementById('predictionDays');
    const days = daysInput ? parseInt(daysInput.value) : 90;
    try {
        // 为每个用户分配营养数据
        const usersAnalysisData = activeMembers.map(user => {
            const userRatio = calculateUserNutritionRatio(user, activeMembers, analyzer);
            console.log(`用户 ${user.member_id} 分配比例: ${userRatio}`);
            console.log(`总营养数据:`, totalNutrients);

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

            console.log(`用户 ${user.member_id} 分析数据:`, userData);
            return userData;
        });
        // 执行营养分析（自动适配n个人）
        const results = analyzer.analyze(usersAnalysisData, days);
        console.log("results",results)
        updateUserCard(results);
        generateNutritionMini(results);

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
/* ========== 生成缩略版营养展示（一行显示） ========== */
function generateNutritionMiniOne(result) {
    if (!result) return;

    const { user_input, baseline, differences } = result;
    const content = document.getElementById('nutritionMiniContent'); // 需要在前端添加这个容器
    if (!content) return;

    // 计算百分比（限制在0-150%）
    const getPercentage = (actual, baseline) => {
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

    // 营养数据配置
    const nutrients = [
        {
            label: '热量',
            type: 'calories',
            actual: user_input.calories_intake,
            baseline: baseline.calories,
            diff: differences.absolute.calories,
            unit: 'kcal',
            percentage: getPercentage(user_input.calories_intake, baseline.calories)
        },
        {
            label: '蛋白质',
            type: 'protein',
            actual: user_input.protein_g,
            baseline: baseline.protein_g,
            diff: differences.absolute.protein_g,
            unit: 'g',
            percentage: getPercentage(user_input.protein_g, baseline.protein_g)
        },
        {
            label: '脂肪',
            type: 'fat',
            actual: user_input.fat_g,
            baseline: baseline.fat_g,
            diff: differences.absolute.fat_g,
            unit: 'g',
            percentage: getPercentage(user_input.fat_g, baseline.fat_g)
        },
        {
            label: '碳水',
            type: 'carbs',
            actual: user_input.carbs_g,
            baseline: baseline.carbs_g,
            diff: differences.absolute.carbs_g,
            unit: 'g',
            percentage: getPercentage(user_input.carbs_g, baseline.carbs_g)
        }
    ];

    // 生成HTML - 一行布局
    const html = `
        <div class="nutrition-mini-bar">
            ${nutrients.map(nutrient => `
                <div class="nutrient-mini-item">
                    <div class="nutrient-mini-header">
                        <span class="nutrient-mini-label">${nutrient.label}</span>
                        <span class="nutrient-mini-value">${nutrient.actual}${nutrient.unit}</span>
                    </div>
                    <div class="mini-bar-container">
                        <div class="mini-bar-fill ${nutrient.type}"
                             style="width: ${nutrient.percentage}%"
                             title="${nutrient.label}: ${nutrient.actual}${nutrient.unit} (${Math.round(nutrient.percentage)}%)">
                        </div>
                    </div>
                    <div class="nutrient-mini-diff ${getDifferenceClass(nutrient.diff)}">
                        ${getDifferenceText(nutrient.diff, nutrient.unit)}
                    </div>
                </div>
            `).join('')}
        </div>
    `;

    content.innerHTML = html;
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
/* ========== 计算用户营养分配比例 ========== */
function calculateUserNutritionRatio(user, allUsers, analyzer) {
    // 方案1: 按体重比例分配（更合理）
    const userWeight = parseFloat(user.weight_kg) || 65;
    const totalWeight = allUsers.reduce((sum, u) => sum + (parseFloat(u.weight_kg) || 65), 0);

    return totalWeight > 0 ? userWeight / totalWeight : 1 / allUsers.length;
}