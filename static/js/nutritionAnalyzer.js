// 专利级多维营养分析与身材预测算法
export class AdvancedNutritionAnalyzer {
    constructor() {
        this.patentedConfig = {
            // 专利核心参数
            'METABOLIC_ADAPTATION_FACTOR': 0.15,
            'NUTRIENT_SYNERGY_MULTIPLIER': 1.25,
            'AGE_RELATED_DECLINE_CURVE': 0.002,
            'EXERCISE_EFFICIENCY_INDEX': 0.85,
            'BODY_COMPOSITION_OPTIMIZER': 0.72,
            'kcal_per_kg_fat': 7700
        };

        // 添加缺失的BMI标准定义
// 在 constructor 中更新 bmiStandards
this.bmiStandards = {
    male: {
        1: {  // 偏偏瘦
            'name': '偏偏瘦',
            'bmi_range': [0, 18.4],  // 修改边界值
            'description': '体重过轻，需要增加营养',
            'image_path': 'images/mbody/very_thin.png'
        },
        2: {  // 偏瘦
            'name': '偏瘦',
            'bmi_range': [18.5, 19.9],  // 明确边界
            'description': '体重偏轻，建议适当增重',
            'image_path': 'images/mbody/thin.png'
        },
        3: {  // 标准
            'name': '标准',
            'bmi_range': [20.0, 23.9],  // 缩小标准范围
            'description': '健康体重，继续保持',
            'image_path': 'images/mbody/normal.png'
        },
        4: {  // 偏胖
            'name': '偏胖',
            'bmi_range': [24.0, 27.9],  // 调整范围
            'description': '体重偏重，建议适当减重',
            'image_path': 'images/mbody/overweight.png'
        },
        5: {  // 偏偏胖
            'name': '偏偏胖',
            'bmi_range': [28.0, 100.0],  // 降低肥胖阈值
            'description': '体重过重，需要减重',
            'image_path': 'images/mbody/very_overweight.png'
        }
    },
    female: {
        1: {  // 偏偏瘦
            'name': '偏偏瘦',
            'bmi_range': [0, 17.4],  // 修改边界值
            'description': '体重过轻，需要增加营养',
            'image_path': 'images/fbody/very_thin.png'
        },
        2: {  // 偏瘦
            'name': '偏瘦',
            'bmi_range': [17.5, 18.9],  // 明确边界
            'description': '体重偏轻，建议适当增重',
            'image_path': 'images/fbody/thin.png'
        },
        3: {  // 标准
            'name': '标准',
            'bmi_range': [19.0, 23.9],  // 缩小标准范围
            'description': '健康体重，继续保持',
            'image_path': 'images/fbody/normal.png'
        },
        4: {  // 偏胖
            'name': '偏胖',
            'bmi_range': [24.0, 27.9],  // 调整范围
            'description': '体重偏重，建议适当减重',
            'image_path': 'images/fbody/overweight.png'
        },
        5: {  // 偏偏胖
            'name': '偏偏胖',
            'bmi_range': [28.0, 100.0],  // 降低肥胖阈值
            'description': '体重过重，需要减重',
            'image_path': 'images/fbody/very_overweight.png'
        }
    }
};

        // 专利算法映射表
        this.patentedAlgorithms = this.initializePatentedAlgorithms();
    }

    // 专利核心方法1: 多维代谢率计算
    calculateAdvancedBMR(height, weight, age, gender, ageGroup) {
        // 基础BMR计算
        let baseBMR;
        if (gender === 'male') {
            baseBMR = 10 * weight + 6.25 * height - 5 * age + 5;
        } else {
            baseBMR = 10 * weight + 6.25 * height - 5 * age - 161;
        }

        // 年龄段修正因子（专利核心）
        const ageGroupFactors = {
            'child': 1.15,   // 儿童新陈代谢旺盛
            'teen': 1.25,    // 青少年生长激素影响
            'young': 1.10,   // 青年代谢活跃
            'middle': 1.00,  // 中年基准
            'senior': 0.85   // 老年代谢减缓
        };

        // 性别特异性修正
        const genderSpecificFactors = {
            'male': 1.05,
            'female': 0.95
        };

        return baseBMR * ageGroupFactors[ageGroup] * genderSpecificFactors[gender];
    }

    // 专利核心方法2: 运动能量消耗智能计算
    calculateExerciseEnergyExpenditure(BMR, exerciseParams) {
        const { frequency, duration, intensity } = exerciseParams;

        // 运动频率系数（专利算法）
        const frequencyFactors = {
            'sedentary': 1.0,
            'light': 1.1,
            'moderate': 1.25,
            'active': 1.45,
            'athlete': 1.7
        };

        // 运动时长系数
        const durationFactors = {
            'short': 0.8,
            'medium': 1.0,
            'long': 1.25,
            'extended': 1.5
        };

        // 运动强度系数（基于MET值）
        const intensityFactors = {
            'low': 1.2,      // MET 3-4
            'medium': 1.5,   // MET 5-6
            'high': 2.0,     // MET 7-8
            'veryHigh': 2.8  // MET 9+
        };

        // 专利核心公式：EE = BMR × 频率系数 × 时长系数 × 强度系数 × 效率指数
        return BMR * frequencyFactors[frequency] *
               durationFactors[duration] *
               intensityFactors[intensity] *
               this.patentedConfig.EXERCISE_EFFICIENCY_INDEX;
    }

    // 专利核心方法3: 营养协同效应计算
    calculateNutrientSynergy(proteinRatio, fatRatio, carbsRatio, ageGroup) {
        // 不同年龄段的理想营养比例（专利研究得出）
        const optimalRatios = {
            'child': { protein: 0.15, fat: 0.30, carbs: 0.55 },
            'teen': { protein: 0.20, fat: 0.25, carbs: 0.55 },
            'young': { protein: 0.25, fat: 0.25, carbs: 0.50 },
            'middle': { protein: 0.25, fat: 0.25, carbs: 0.50 },
            'senior': { protein: 0.30, fat: 0.25, carbs: 0.45 }
        };

        const optimal = optimalRatios[ageGroup];

        // 专利算法：营养偏离度计算
        const proteinDeviation = Math.abs(proteinRatio - optimal.protein);
        const fatDeviation = Math.abs(fatRatio - optimal.fat);
        const carbsDeviation = Math.abs(carbsRatio - optimal.carbs);

        // 协同效应得分（0-1，越高越好）
        const synergyScore = 1 - (proteinDeviation + fatDeviation + carbsDeviation) * 2;

        return Math.max(0.1, Math.min(1, synergyScore));
    }

    // 专利核心方法4: 体成分变化预测算法
    predictBodyCompositionAdvanced(ratioDiffs, totalShift, weight, gender, ageGroup, exerciseParams) {
        let baseMuscleRatio;

        // 基于年龄和性别的基准肌肉比例
        const baseRatios = {
            'male': {
                'child': 0.25, 'teen': 0.35, 'young': 0.40, 'middle': 0.35, 'senior': 0.25
            },
            'female': {
                'child': 0.20, 'teen': 0.25, 'young': 0.30, 'middle': 0.25, 'senior': 0.20
            }
        };

        if (totalShift > 0) {
            // 增重模式
            baseMuscleRatio = baseRatios[gender][ageGroup];

            // 蛋白质效应增强
            if (ratioDiffs.protein > 0.03) {
                baseMuscleRatio += 0.20;
            } else if (ratioDiffs.protein < -0.03) {
                baseMuscleRatio -= 0.15;
            }

            // 运动强度对肌肉增长的促进
            const intensityBonus = {
                'low': 0.05, 'medium': 0.10, 'high': 0.15, 'veryHigh': 0.20
            };
            baseMuscleRatio += intensityBonus[exerciseParams.intensity];

        } else {
            // 减重模式
            baseMuscleRatio = baseRatios[gender][ageGroup] * 0.7;

            // 高蛋白保护肌肉
            if (ratioDiffs.protein > 0.03) {
                baseMuscleRatio += 0.15;
            } else if (ratioDiffs.protein < -0.03) {
                baseMuscleRatio -= 0.10;
            }

            // 力量训练保护肌肉
            if (exerciseParams.intensity === 'high' || exerciseParams.intensity === 'veryHigh') {
                baseMuscleRatio += 0.10;
            }
        }

        // 专利优化器调整
        const optimizedRatio = baseMuscleRatio * this.patentedConfig.BODY_COMPOSITION_OPTIMIZER;
        const muscleRatio = Math.max(0.1, Math.min(0.8, optimizedRatio));

        const muscleShift = totalShift * muscleRatio;
        const fatShift = totalShift * (1 - muscleRatio);

        return {
            'fat_shift': fatShift,
            'muscle_shift': muscleShift,
            'muscle_ratio': muscleRatio,
            'optimization_score': this.calculateOptimizationScore(muscleRatio, ageGroup, gender)
        };
    }

    // 专利核心方法5: 代谢适应性预测
// 专利核心方法5: 代谢适应性预测 - 更科学的长期预测
predictMetabolicAdaptation(currentWeight, predictedShift, timeframe, ageGroup) {
    // 代谢适应性系数
    const adaptationFactors = {
        'child': 0.6,   // 儿童代谢适应性强
        'teen': 0.7,    // 青少年适应性强
        'young': 0.8,   // 青年基准
        'middle': 0.9,  // 中年代谢适应性下降
        'senior': 1.0   // 老年代谢适应性显著下降
    };

    const baseAdaptation = this.patentedConfig.METABOLIC_ADAPTATION_FACTOR;
    const ageAdaptation = adaptationFactors[ageGroup];

    // 更科学的长期代谢适应公式
    // 适应性与时间平方根成正比，与体重变化幅度成正比
    const timeFactor = Math.sqrt(timeframe / 30); // 以30天为基准
    const weightChangeFactor = Math.min(1, Math.abs(predictedShift) / currentWeight * 10);

    return baseAdaptation * ageAdaptation * timeFactor * weightChangeFactor;
}

    // 专利核心方法6: 综合体重预测
// 专利核心方法6: 综合体重预测 - 科学版本
predictWeightShiftAdvanced(differences, userProfile, days = 90) { // 默认改为90天
    const { weight_kg, height_cm, age, gender, ageGroup, exerciseFrequency, exerciseDuration, exerciseIntensity } = userProfile;

    // 计算高级BMR - 保持科学计算
    const advancedBMR = this.calculateAdvancedBMR(height_cm, weight_kg, age, gender, ageGroup);

    // 计算运动消耗 - 保持科学计算
    const exerciseEE = this.calculateExerciseEnergyExpenditure(advancedBMR, {
        frequency: exerciseFrequency,
        duration: exerciseDuration,
        intensity: exerciseIntensity
    });

    // 计算总能量消耗
    const TDEE = advancedBMR + exerciseEE;

    // 科学的热量差值计算
    const dailyCalorieDiff = differences.absolute.calories - TDEE;
    const totalCalorieSurplus = dailyCalorieDiff * days;

    // 科学的体重变化计算 (7700 kcal = 1kg 脂肪)
    let baseWeightShift = totalCalorieSurplus / this.patentedConfig.kcal_per_kg_fat;

    // 营养协同效应调整
    const synergyScore = this.calculateNutrientSynergy(
        differences.actual_ratios.protein,
        differences.actual_ratios.fat,
        differences.actual_ratios.carbs,
        ageGroup
    );

    // 代谢适应性调整 - 随时间增强
    const metabolicAdaptation = this.predictMetabolicAdaptation(
        weight_kg, baseWeightShift, days, ageGroup
    );

    // 科学的最终体重变化公式
    const adjustedWeightShift = baseWeightShift *
                              synergyScore *
                              this.patentedConfig.NUTRIENT_SYNERGY_MULTIPLIER *
                              (1 - metabolicAdaptation);

    console.log(`科学预测: ${days}天, 每日热量差: ${dailyCalorieDiff}kcal, 预计变化: ${adjustedWeightShift}kg`);

    // 体成分预测
    const bodyComp = this.predictBodyCompositionAdvanced(
        differences.ratios, adjustedWeightShift, weight_kg, gender, ageGroup,
        { frequency: exerciseFrequency, duration: exerciseDuration, intensity: exerciseIntensity }
    );

    const newWeight = weight_kg + adjustedWeightShift;

    return {
        'weight_shift_kg': Math.round(adjustedWeightShift * 100) / 100,
        'new_weight_kg': Math.round(newWeight * 10) / 10,
        'fat_shift_kg': Math.round(bodyComp.fat_shift * 100) / 100,
        'muscle_shift_kg': Math.round(bodyComp.muscle_shift * 100) / 100,
        'muscle_ratio': Math.round(bodyComp.muscle_ratio * 1000) / 1000,
        'optimization_score': Math.round(bodyComp.optimization_score * 100),
        'synergy_score': Math.round(synergyScore * 100),
        'metabolic_adaptation': Math.round(metabolicAdaptation * 100),
        'advanced_bmr': Math.round(advancedBMR),
        'exercise_energy': Math.round(exerciseEE),
        'total_tdee': Math.round(TDEE),
        'timeframe_days': days
    };
}

    // 辅助方法
    calculateOptimizationScore(muscleRatio, ageGroup, gender) {
        // 计算体成分优化得分
        const optimalRatios = {
            'male': { 'child': 0.3, 'teen': 0.4, 'young': 0.45, 'middle': 0.4, 'senior': 0.35 },
            'female': { 'child': 0.25, 'teen': 0.3, 'young': 0.35, 'middle': 0.3, 'senior': 0.25 }
        };

        const optimal = optimalRatios[gender][ageGroup];
        return Math.max(0, 1 - Math.abs(muscleRatio - optimal) / optimal);
    }
    /* ========== 计算用户营养分配比例 ========== */
    /* 计算用户营养分配比例 - 基于 TDEE + 年龄修正 */
    calculateUserNutritionRatio(user, allUsers, analyzer) {
      // 1. 基础信息
      const weight = parseFloat(user.weight_kg) || 65;
      const height = parseFloat(user.height_cm) || 170;
      const age  = parseInt(user.age) || 30;
      const gender = user.gender || 'male';
      const ageGroup = user.ageGroup || 'middle';

      // 2. 计算 BMR（复用 analyzer 里的专利公式，可替换为 Mifflin 简化版）
      const bmr = analyzer.calculateAdvancedBMR(height, weight, age, gender, ageGroup);

      // 3. PAL（活动系数）映射
      const palMap = {
        sedentary: 1.2,
        light: 1.375,
        moderate: 1.55,
        active: 1.725,
        athlete: 1.9
      };
      const pal = palMap[user.exerciseFrequency] || 1.55;

      // 4. 运动额外消耗（简单折算）
      const durationMap = { short: 15, medium: 30, long: 45, extended: 60 };
      const intensityMap = { low: 3, medium: 5, high: 7, veryHigh: 9 }; // METs
      const mins = durationMap[user.exerciseDuration] || 30;
      const mets = intensityMap[user.exerciseIntensity] || 5;
      const exerciseKcal = (mets * weight * (mins / 60)) || 0;

      // 5. TDEE
      let tdee = bmr * pal + exerciseKcal;

      // 6. 年龄修正
      if (age < 6) tdee *= 1.2;        // 生长高峰
      if (age >= 65) tdee *= 0.9;      // 食欲下降

      // 7. 全家总 TDEE
      const totalTDEE = allUsers.reduce((sum, u) => {
        const uWeight = parseFloat(u.weight_kg) || 65;
        const uHeight = parseFloat(u.height_cm) || 170;
        const uAge  = parseInt(u.age) || 30;
        const uGender = u.gender || 'male';
        const uAgeGroup = u.ageGroup || 'middle';
        const uBMR = analyzer.calculateAdvancedBMR(uHeight, uWeight, uAge, uGender, uAgeGroup);
        const uPAL = palMap[u.exerciseFrequency] || 1.55;
        const uMins = durationMap[u.exerciseDuration] || 30;
        const uMets = intensityMap[u.exerciseIntensity] || 5;
        const uExercise = (uMets * uWeight * (uMins / 60)) || 0;
        let uTDEE = uBMR * uPAL + uExercise;
        if (uAge < 6) uTDEE *= 1.2;
        if (uAge >= 65) uTDEE *= 0.9;
        return sum + uTDEE;
      }, 0);

      // 8. 比例
      return totalTDEE > 0 ? tdee / totalTDEE : 1 / allUsers.length;
    }

    initializePatentedAlgorithms() {
        return {
            // 这里可以注册更多的专利算法
            'bodyCompositionV1': this.predictBodyCompositionAdvanced,
            'metabolicAdaptationV1': this.predictMetabolicAdaptation,
            'nutrientSynergyV1': this.calculateNutrientSynergy
        };
    }

// 主分析方法 - 支持多用户和自定义时间
analyze(usersInput, days = null) {
    // 如果没有指定天数，使用表单选择或默认90天
    if (!days) {
        const daysInput = document.getElementById('predictionDays');
        days = daysInput ? parseInt(daysInput.value) : 90;
    }

    // 处理多用户情况
    const isMultiUser = Array.isArray(usersInput);
    const inputs = isMultiUser ? usersInput : [usersInput];

    const results = [];

    inputs.forEach((userInput, index) => {
        const baseline = this.calculateBaseline(userInput);
        const differences = this.calculateDifferences(userInput, baseline);
        const prediction = this.predictWeightShiftAdvanced(differences, userInput, days);
        const bodyImagePrediction = this.predictFutureBodyImage(userInput, prediction.weight_shift_kg);

        results.push({
            'user_input': userInput,
            'baseline': baseline,
            'differences': differences,
            'prediction': prediction,
            'body_image': bodyImagePrediction,
            'patent_algorithm_version': '1.0'
        });
    });

    return isMultiUser ? results : results[0];
}

    // 保持原有方法的兼容性
    calculateBaseline(userInput) {
        const { height_cm, weight_kg, gender, age, ageGroup } = userInput;
        const advancedBMR = this.calculateAdvancedBMR(height_cm, weight_kg, age, gender, ageGroup);

        return {
            'calories': Math.round(advancedBMR),
            'protein_g': Math.round(weight_kg * 1.2 * 10) / 10,
            'fat_g': Math.round((advancedBMR * 0.25) / 9 * 10) / 10,
            'carbs_g': Math.round((advancedBMR * 0.55) / 4 * 10) / 10,
            'bmr': Math.round(advancedBMR),
            'tdee': Math.round(advancedBMR)
        };
    }

    calculateDifferences(intake, baseline) {
    console.log('差异计算 - 摄入:', intake);
    console.log('差异计算 - 基准:', baseline);
        const toOneDecimal = (num) => parseFloat(num.toFixed(1));

        const absoluteDiffs = {
            'calories': toOneDecimal(intake.calories_intake - baseline.calories),
            'protein_g': toOneDecimal(intake.protein_g - baseline.protein_g),
            'fat_g': toOneDecimal(intake.fat_g - baseline.fat_g),
            'carbs_g': toOneDecimal(intake.carbs_g - baseline.carbs_g)
        };
console.log('绝对差异:', absoluteDiffs);
        const calculateRatio = (nutrientG, calories, nutrientType) => {
            const kcalPerG = nutrientType === 'fat' ? 9 : 4;
            return calories > 0 ? (nutrientG * kcalPerG) / calories : 0;
        };

        const actualRatios = {
            'protein': calculateRatio(intake.protein_g, intake.calories_intake, 'protein'),
            'fat': calculateRatio(intake.fat_g, intake.calories_intake, 'fat'),
            'carbs': calculateRatio(intake.carbs_g, intake.calories_intake, 'carbs')
        };
console.log('实际比例:', actualRatios);
        const baselineRatios = {
            'protein': calculateRatio(baseline.protein_g, baseline.calories, 'protein'),
            'fat': calculateRatio(baseline.fat_g, baseline.calories, 'fat'),
            'carbs': calculateRatio(baseline.carbs_g, baseline.calories, 'carbs')
        };

        const ratioDiffs = {};
        for (const nutrient of ['protein', 'fat', 'carbs']) {
            ratioDiffs[nutrient] = actualRatios[nutrient] - baselineRatios[nutrient];
        }

        return {
            'absolute': absoluteDiffs,
            'ratios': ratioDiffs,
            'actual_ratios': actualRatios,
            'baseline_ratios': baselineRatios
        };
    }

getBodyImageType(height, weight, gender) {
    const bmi = this.calculateBMI(height, weight);
    const bodyImageMapping = this.bmiStandards[gender];

    console.log(`BMI计算: 身高${height}cm, 体重${weight}kg, BMI=${bmi}`); // 调试信息

    for (const [typeCode, config] of Object.entries(bodyImageMapping)) {
        const [minBMI, maxBMI] = config.bmi_range;
        // 修复边界判断逻辑
        if (bmi >= minBMI && bmi < maxBMI) {
            console.log(`匹配到体型: ${config.name}, 范围: [${minBMI}, ${maxBMI})`); // 调试信息
            return {
                type_code: parseInt(typeCode),
                type_name: config.name,
                bmi: Math.round(bmi * 10) / 10,
                image_path: config.image_path,
                description: config.description
            };
        }
    }

    // 如果所有范围都不匹配，返回最接近的
    console.log('未匹配到具体范围，使用默认标准体型'); // 调试信息
    return bodyImageMapping[3]; // 默认返回标准体型
}

    predictFutureBodyImage(userInput, predictedWeightShift) {
        const { height_cm, weight_kg, gender } = userInput;
        const futureWeight = weight_kg + predictedWeightShift;
        const currentBody = this.getBodyImageType(height_cm, weight_kg, gender);
        const futureBody = this.getBodyImageType(height_cm, futureWeight, gender);

        return {
            current: currentBody,
            future: futureBody,
            weight_change: predictedWeightShift
        };
    }

    calculateBMI(height, weight) {
        const heightM = height / 100;
        return weight / (heightM * heightM);
    }
}