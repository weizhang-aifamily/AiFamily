/**
 * 营养分析相关API
 */

/**
 * 计算用户营养分配比例
 */
export async function calculateUserNutritionRatios(activeMembers, allUsers) {
  try {
    const res = await fetch('/nutrition/calculate-ratios', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        active_members: activeMembers,  // 改为复数形式
        all_users: allUsers
      })
    });

    const json = await res.json();

    if (json.success) {
      return json.ratios;  // 返回整个比例对象
    }

    console.error('计算营养比例报错：', json.error || json);
    // 降级处理：为每个用户返回平均比例
    const fallbackRatio = 1 / allUsers.length;
    const fallbackRatios = {};
    activeMembers.forEach(user => {
      fallbackRatios[user.member_id] = fallbackRatio;
    });
    return fallbackRatios;
  } catch (error) {
    console.error('API调用失败：', error);
    // 降级处理
    const fallbackRatio = 1 / allUsers.length;
    const fallbackRatios = {};
    activeMembers.forEach(user => {
      fallbackRatios[user.member_id] = fallbackRatio;
    });
    return fallbackRatios;
  }
}

/**
 * 执行营养分析
 */
export async function analyzeNutrition(usersAnalysisData, days = 90) {
  try {
    const res = await fetch('/nutrition/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        users: usersAnalysisData,
        days: days
      })
    });

    const json = await res.json();

    if (json.success) {
      return json.results;
    }

    console.error('营养分析报错：', json.error || json);
    return null;
  } catch (error) {
    console.error('API调用失败：', error);
    return null;
  }
}
export async function updateMembers({
  members = []
} = {}) {
  const url = `/family/updateMembers`;

  const requestBody = {
    members: members
  };

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    });

    const json = await res.json();

    if (json.status === 'success') {
      return json.data;
    }

    console.error('updateMembers：', json.message || json);
    return [];
  } catch (error) {
    console.error('updateMembers：', error);
    return [];
  }
}