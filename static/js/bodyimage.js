// 页面交互逻辑 - 负责UI交互
class NutritionApp {
    constructor() {
        this.analyzer = new AdvancedNutritionAnalyzer();
        this.currentResult = null;
        this.initEventListeners();
    }

    initEventListeners() {
        // 表单提交
        document.getElementById('nutritionForm').addEventListener('submit', (e) => {
            this.handleFormSubmit(e);
        });

        // 年龄输入时自动更新年龄段
        document.getElementById('age').addEventListener('change', (e) => {
            this.updateAgeGroup(e.target.value);
        });

        // 用户卡片点击事件
        const userCard = document.getElementById('bodyImage');
        if (userCard) {
            userCard.addEventListener('click', (e) => {
                this.toggleDetailSection();
            });
        }

        // 标签页切换
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // 阻止卡片内部点击事件冒泡
        document.querySelectorAll('.user-card *').forEach(element => {
            element.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        });
    }

    updateAgeGroup(age) {
        const ageNum = parseInt(age);
        const ageGroupSelect = document.getElementById('ageGroup');

        if (ageGroupSelect) {
            if (ageNum <= 12) {
                ageGroupSelect.value = 'child';
            } else if (ageNum <= 17) {
                ageGroupSelect.value = 'teen';
            } else if (ageNum <= 35) {
                ageGroupSelect.value = 'young';
            } else if (ageNum <= 59) {
                ageGroupSelect.value = 'middle';
            } else {
                ageGroupSelect.value = 'senior';
            }
        }
    }

    toggleDetailSection() {
        const userCard = document.getElementById('userCard');
        const detailSection = document.getElementById('detailSection');

        if (this.currentResult && userCard && detailSection) {
            userCard.classList.toggle('active');
            detailSection.classList.toggle('active');

            // 如果展开详情，默认显示营养分析标签
            if (detailSection.classList.contains('active')) {
                this.switchTab('nutrition');
            }
        }
    }

    switchTab(tabName) {
        // 更新标签按钮状态
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.remove('active');
        });
        const activeButton = document.querySelector(`[data-tab="${tabName}"]`);
        if (activeButton) {
            activeButton.classList.add('active');
        }

        // 更新标签内容
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        const activeContent = document.getElementById(`tab${this.capitalizeFirst(tabName)}`);
        if (activeContent) {
            activeContent.classList.add('active');
        }

        // 根据标签显示对应内容
        if (this.currentResult) {
            switch(tabName) {
                case 'nutrition':
                    this.displayNutritionContent();
                    break;
                case 'prediction':
                    this.displayPredictionContent();
                    break;
                case 'advice':
                    this.displayAdviceContent();
                    break;
            }
        }
    }

    capitalizeFirst(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }

    handleFormSubmit(e) {
        e.preventDefault();

        const loading = document.getElementById('loading');
        const error = document.getElementById('error');
        const userCard = document.getElementById('userCard');
        const detailSection = document.getElementById('detailSection');

        // 隐藏错误，显示加载
        if (error) error.style.display = 'none';
        if (loading) loading.style.display = 'block';

        // 重置显示状态
        if (userCard) userCard.classList.remove('active');
        if (detailSection) detailSection.classList.remove('active');

        // 获取所有表单数据
        const formData = {
            gender: document.getElementById('gender').value,
            age: parseInt(document.getElementById('age').value),
            ageGroup: document.getElementById('ageGroup').value,
            height_cm: parseFloat(document.getElementById('height').value),
            weight_kg: parseFloat(document.getElementById('weight').value),
            calories_intake: parseFloat(document.getElementById('calories').value),
            protein_g: parseFloat(document.getElementById('protein').value),
            fat_g: parseFloat(document.getElementById('fat').value),
            carbs_g: parseFloat(document.getElementById('carbs').value),
            exerciseFrequency: document.getElementById('exerciseFrequency').value,
            exerciseDuration: document.getElementById('exerciseDuration').value,
            exerciseIntensity: document.getElementById('exerciseIntensity').value
        };

        // 验证数据
        if (!this.validateFormData(formData)) {
            if (error) {
                error.textContent = '请检查输入数据是否合理';
                error.style.display = 'block';
            }
            if (loading) loading.style.display = 'none';
            return;
        }

        // 模拟异步处理
        setTimeout(() => {
            try {
                const result = this.analyzer.analyze(formData);
                this.currentResult = result;

                // 更新用户卡片
                this.updateUserCard(result);

                // 显示默认标签内容
                this.displayNutritionContent();

                this.showNotification('分析完成！点击卡片查看详细信息', 'success');

            } catch (err) {
                if (error) {
                    error.textContent = '分析过程中出现错误: ' + err.message;
                    error.style.display = 'block';
                }
                console.error('Analysis error:', err);
                this.showNotification('分析失败，请检查输入数据', 'error');
            } finally {
                if (loading) loading.style.display = 'none';
            }
        }, 1500);
    }

    validateFormData(formData) {
        // 基础验证
        if (formData.height_cm < 100 || formData.height_cm > 250) {
            return false;
        }
        if (formData.weight_kg < 20 || formData.weight_kg > 200) {
            return false;
        }
        if (formData.calories_intake < 500 || formData.calories_intake > 10000) {
            return false;
        }
        if (formData.age < 1 || formData.age > 120) {
            return false;
        }
        return true;
    }

    updateUserCard(result) {
        const user = result.user_input;
        const pred = result.prediction;
        const bodyImg = result.body_image;

        // 更新基本信息
        const genderText = user.gender === 'male' ? '男性' : '女性';
        const ageGroupText = this.getAgeGroupText(user.ageGroup);
        const userBasicInfo = document.getElementById('userBasicInfo');
        if (userBasicInfo) {
            userBasicInfo.textContent =
                `${genderText} | ${user.age}岁 | ${user.height_cm}cm | ${user.weight_kg}kg`;
        }

        // 更新用户头像
        const avatar = document.getElementById('userAvatar');
        if (avatar) {
            avatar.textContent = user.gender === 'male' ? '♂' : '♀';
            avatar.style.background = user.gender === 'male' ?
                'linear-gradient(135deg, #667eea, #764ba2)' :
                'linear-gradient(135deg, #ff6b6b, #ff8e8e)';
        }

        // 更新统计数据
        const statBMI = document.getElementById('statBMI');
        const statBMR = document.getElementById('statBMR');
        const statWeightChange = document.getElementById('statWeightChange');

        if (statBMI) statBMI.textContent = bodyImg.current.bmi;
        if (statBMR) statBMR.textContent = pred.advanced_bmr;
        if (statWeightChange) {
            statWeightChange.textContent =
                `${pred.weight_shift_kg > 0 ? '+' : ''}${pred.weight_shift_kg}kg`;
        }

        // 显示统计数据和图片
        const userStats = document.getElementById('userStats');
        const bodyImagePreview = document.getElementById('bodyImagePreview');
        if (userStats) userStats.style.display = 'grid';
        if (bodyImagePreview) bodyImagePreview.style.display = 'block';

        // 更新身材图片
        const bodyImage = document.getElementById('bodyImage');
        const imageInfo = document.getElementById('imageInfo');
        if (bodyImage) bodyImage.src = bodyImg.future.image_path;
        if (imageInfo) {
            imageInfo.textContent =
                `${bodyImg.future.type_name} (预测)`;
        }
    }

displayNutritionContent() {
    if (!this.currentResult) return;

    const result = this.currentResult;
    const user = result.user_input;
    const baseline = result.baseline;
    const diffs = result.differences;
    const pred = result.prediction;

    const content = document.getElementById('nutritionContent');
    if (!content) return;

    let html = `
        <div class="patent-badge">专利算法 v${result.patent_algorithm_version}</div>

        <div class="result-grid">
            <div class="result-card">
                <h4>📊 代谢分析</h4>
                <div class="result-value">基础代谢率: <strong>${pred.advanced_bmr}</strong> kcal/天</div>
                <div class="result-value">运动消耗: <strong>${pred.exercise_energy}</strong> kcal/天</div>
                <div class="result-value">总能量消耗: <strong>${pred.total_tdee}</strong> kcal/天</div>
                <div class="result-value">代谢适应性: <strong>${pred.metabolic_adaptation}%</strong></div>
            </div>
        </div>

        <div class="result-card">
            <h4>⚖️ 营养摄入分析</h4>
            <div class="nutrition-bars" id="nutritionBars">
                ${this.generateNutritionBars(result)}
            </div>
        </div>

        <div class="result-card" style="margin-top: 20px;">
            <h4>🧪 营养协同分析</h4>
            <div class="result-value">协同得分: <strong>${pred.synergy_score}/100</strong></div>
            <div class="result-value">蛋白质供能: <strong>${(diffs.actual_ratios.protein * 100).toFixed(1)}%</strong></div>
            <div class="result-value">脂肪供能: <strong>${(diffs.actual_ratios.fat * 100).toFixed(1)}%</strong></div>
            <div class="result-value">碳水供能: <strong>${(diffs.actual_ratios.carbs * 100).toFixed(1)}%</strong></div>
        </div>
    `;

    content.innerHTML = html;
}

// 新增：生成营养进度条
generateNutritionBars(result) {
    const { user_input, baseline, differences } = result;

    // 计算显示比例（以基准值为100%）
    const getPercentage = (actual, baseline) => {
        return Math.min((actual / baseline) * 100, 150); // 最大显示150%
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

    const bars = [
        {
            label: '总热量',
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

    return bars.map(bar => `
        <div class="nutrient-bar">
            <div class="nutrient-header">
                <span class="nutrient-label">${bar.label}</span>
                <div class="nutrient-values">
                    <span>${bar.actual}${bar.unit}</span>
                    <span class="nutrient-ratio">${Math.round(bar.percentage)}%</span>
                    <span class="difference-badge ${getDifferenceClass(bar.diff)}">
                        ${getDifferenceText(bar.diff, bar.unit)}
                    </span>
                </div>
            </div>
            <div class="bar-container">
                <div class="bar-fill ${bar.type}" style="width: ${bar.percentage}%"></div>
                <div class="bar-marker" style="left: 100%"></div>
            </div>
            <div class="bar-labels">
                <span>0</span>
                <span>基准: ${bar.baseline}${bar.unit}</span>
                <span>150%</span>
            </div>
        </div>
    `).join('');
}

    displayPredictionContent() {
        if (!this.currentResult) return;

        const result = this.currentResult;
        const pred = result.prediction;
        const bodyImg = result.body_image;

        const content = document.getElementById('predictionContent');
        if (!content) return;

        let html = `
            <div class="prediction-comparison">
                <div class="comparison-item">
                    <h4>当前状态</h4>
                    <div style="font-size: 2em; margin: 15px 0;">${bodyImg.current.type_name}</div>
                    <div class="result-value">BMI: <strong>${bodyImg.current.bmi}</strong></div>
                    <div class="result-value">${bodyImg.current.description}</div>
                </div>

                <div class="comparison-arrow">➡️</div>

                <div class="comparison-item">
                    <h4>30天预测</h4>
                    <div style="font-size: 2em; margin: 15px 0;">${bodyImg.future.type_name}</div>
                    <div class="result-value">BMI: <strong>${bodyImg.future.bmi}</strong></div>
                    <div class="result-value">${bodyImg.future.description}</div>
                </div>
            </div>

            <div class="result-grid">
                <div class="result-card">
                    <h4>📊 体重变化</h4>
                    <div class="result-value">当前体重: <strong>${result.user_input.weight_kg}</strong> kg</div>
                    <div class="result-value">预测体重: <strong>${pred.new_weight_kg}</strong> kg</div>
                    <div class="result-value">变化幅度: <strong style="color: ${pred.weight_shift_kg > 0 ? '#e74c3c' : '#27ae60'}">
                        ${pred.weight_shift_kg > 0 ? '+' : ''}${pred.weight_shift_kg}</strong> kg
                    </div>
                </div>

                <div class="result-card">
                    <h4>💪 体成分分析</h4>
                    <div class="result-value">脂肪变化: <strong style="color: ${pred.fat_shift_kg > 0 ? '#e74c3c' : '#27ae60'}">
                        ${pred.fat_shift_kg > 0 ? '+' : ''}${pred.fat_shift_kg}</strong> kg
                    </div>
                    <div class="result-value">肌肉变化: <strong style="color: ${pred.muscle_shift_kg > 0 ? '#27ae60' : '#e74c3c'}">
                        ${pred.muscle_shift_kg > 0 ? '+' : ''}${pred.muscle_shift_kg}</strong> kg
                    </div>
                    <div class="result-value">肌肉保留率: <strong>${(pred.muscle_ratio * 100).toFixed(1)}%</strong></div>
                    <div class="result-value">优化得分: <strong>${pred.optimization_score}/100</strong></div>
                </div>

                <div class="result-card">
                    <h4>🎯 算法评估</h4>
                    <div class="result-value">营养协同: <strong>${pred.synergy_score}/100</strong></div>
                    <div class="result-value">代谢适应: <strong>${pred.metabolic_adaptation}%</strong></div>
                    <div class="result-value">体成分优化: <strong>${pred.optimization_score}/100</strong></div>
                </div>
            </div>

            <div class="advice-section">
                <h4>💡 预测说明</h4>
                <div class="result-value">• 基于专利级多维营养分析算法</div>
                <div class="result-value">• 综合考虑年龄、性别、运动等多维度因素</div>
                <div class="result-value">• 包含代谢适应性和营养协同效应计算</div>
                <div class="result-value">• 预测结果仅供参考，实际效果因人而异</div>
            </div>
        `;

        content.innerHTML = html;
    }

    displayAdviceContent() {
        if (!this.currentResult) return;

        const result = this.currentResult;
        const content = document.getElementById('adviceContent');
        if (!content) return;

        let html = `
            <div class="result-grid">
                <div class="result-card">
                    <h4>🍎 营养建议</h4>
                    ${this.generateNutritionAdvice(result)}
                </div>

                <div class="result-card">
                    <h4>🏃 运动建议</h4>
                    ${this.generateExerciseAdvice(result)}
                </div>

                <div class="result-card">
                    <h4>🎯 目标管理</h4>
                    ${this.generateGoalAdvice(result)}
                </div>
            </div>

            <div class="advice-section" style="margin-top: 20px;">
                <h4>📋 个性化方案</h4>
                ${this.generatePersonalizedPlan(result)}
            </div>
        `;

        content.innerHTML = html;
    }

    generateNutritionAdvice(result) {
        const pred = result.prediction;
        const diffs = result.differences;
        let advice = '';

        if (pred.synergy_score < 60) {
            advice += '<div class="result-value">🔺 营养比例需要优化，建议调整三大营养素比例</div>';
        }

        if (diffs.absolute.protein_g < -10) {
            advice += '<div class="result-value">🔺 蛋白质摄入不足，建议增加优质蛋白</div>';
        } else if (diffs.absolute.protein_g > 20) {
            advice += '<div class="result-value">✅ 蛋白质摄入充足，有助于肌肉维持</div>';
        }

        if (diffs.absolute.fat_g > 15) {
            advice += '<div class="result-value">🔺 脂肪摄入偏高，建议减少油炸和高脂食物</div>';
        }

        if (diffs.absolute.carbs_g < -50) {
            advice += '<div class="result-value">🔺 碳水摄入不足，可能影响运动表现</div>';
        }

        return advice || '<div class="result-value">✅ 当前营养摄入较为均衡</div>';
    }

    generateExerciseAdvice(result) {
        const user = result.user_input;
        let advice = '';

        if (user.exerciseFrequency === 'sedentary') {
            advice += '<div class="result-value">🔺 运动量不足，建议每周至少运动3次</div>';
        } else if (user.exerciseFrequency === 'athlete') {
            advice += '<div class="result-value">✅ 运动量充足，注意恢复和营养补充</div>';
        }

        if (user.exerciseIntensity === 'low') {
            advice += '<div class="result-value">🔺 运动强度较低，建议适当增加强度</div>';
        } else if (user.exerciseIntensity === 'veryHigh') {
            advice += '<div class="result-value">✅ 高强度训练，确保充足蛋白质摄入</div>';
        }

        return advice || '<div class="result-value">✅ 当前运动计划合理</div>';
    }

    generateGoalAdvice(result) {
        const pred = result.prediction;
        let advice = '';

        if (pred.weight_shift_kg > 1.5) {
            advice += '<div class="result-value">⚠️ 增重速度偏快，建议控制热量盈余在300-500kcal</div>';
        } else if (pred.weight_shift_kg < -1.5) {
            advice += '<div class="result-value">⚠️ 减重速度偏快，建议增加蛋白质摄入保护肌肉</div>';
        } else if (Math.abs(pred.weight_shift_kg) < 0.5) {
            advice += '<div class="result-value">✅ 体重变化平稳，维持期表现良好</div>';
        }

        if (pred.muscle_ratio > 0.6) {
            advice += '<div class="result-value">💪 肌肉增长效果优秀，继续保持</div>';
        } else if (pred.muscle_ratio < 0.3) {
            advice += '<div class="result-value">🔺 肌肉流失较多，建议增加力量训练</div>';
        }

        return advice || '<div class="result-value">✅ 当前计划符合健康目标</div>';
    }

    generatePersonalizedPlan(result) {
        const user = result.user_input;
        const pred = result.prediction;

        let plan = '';

        if (pred.weight_shift_kg > 0) {
            plan += '<div class="result-value">🎯 <strong>增重期方案</strong></div>';
            plan += '<div class="result-value">• 每日热量盈余: 300-500kcal</div>';
            plan += '<div class="result-value">• 蛋白质摄入: 1.6-2.2g/kg体重</div>';
            plan += '<div class="result-value">• 结合力量训练促进肌肉增长</div>';
        } else if (pred.weight_shift_kg < 0) {
            plan += '<div class="result-value">🎯 <strong>减重期方案</strong></div>';
            plan += '<div class="result-value">• 每日热量缺口: 300-500kcal</div>';
            plan += '<div class="result-value">• 蛋白质摄入: 1.8-2.4g/kg体重</div>';
            plan += '<div class="result-value">• 保持力量训练减少肌肉流失</div>';
        } else {
            plan += '<div class="result-value">🎯 <strong>维持期方案</strong></div>';
            plan += '<div class="result-value">• 保持当前热量摄入</div>';
            plan += '<div class="result-value">• 蛋白质摄入: 1.2-1.6g/kg体重</div>';
            plan += '<div class="result-value">• 定期评估调整</div>';
        }

        // 年龄段特殊建议
        if (user.ageGroup === 'senior') {
            plan += '<div class="result-value">• 老年期特别关注: 充足蛋白质 + 维生素D + 钙质</div>';
        } else if (user.ageGroup === 'child' || user.ageGroup === 'teen') {
            plan += '<div class="result-value">• 生长发育期: 全面均衡营养 + 适量运动</div>';
        }

        return plan;
    }

    // 工具方法
    getAgeGroupText(ageGroup) {
        const texts = {
            'child': '儿童',
            'teen': '少年',
            'young': '青年',
            'middle': '中年',
            'senior': '老年'
        };
        return texts[ageGroup] || ageGroup;
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            background: ${type === 'error' ? '#f8d7da' : type === 'success' ? '#d4edda' : '#d1ecf1'};
            color: ${type === 'error' ? '#721c24' : type === 'success' ? '#155724' : '#0c5460'};
            border: 1px solid ${type === 'error' ? '#f5c6cb' : type === 'success' ? '#c3e6cb' : '#bee5eb'};
            border-radius: 10px;
            z-index: 1000;
            animation: slideIn 0.3s ease;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    // 添加CSS动画
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }

        .notification {
            font-weight: bold;
        }

        .result-value {
            margin: 8px 0;
            line-height: 1.5;
        }

        .result-value strong {
            color: #667eea;
        }
    `;
    document.head.appendChild(style);

    // 初始化应用
    new NutritionApp();
});