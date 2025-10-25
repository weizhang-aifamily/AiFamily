export async function getMembers(userId = 1) {
  const res  = await fetch(`/family/getMembers/${userId}`);
  const json = await res.json();

  if (json.status === 'success') {
    return json.data;
  }

  console.error('接口报错：', json.message || json);
  return [];
}
export async function getDietSolutions(member_ids = "1,2") {
  const res  = await fetch(`/family/getDietSolutions/${member_ids}`);
  const json = await res.json();

  if (json.status === 'success') {
    return json.data;
  }

  console.error('getDietSolutions：', json.message || json);
  return [];
}
export async function getCombos({
  member_ids = "1,2",
  need_tags = 'highCalcium,lowFat',
  cuisine = 'sichuan',
  category = '',
  members = [],
  province_code = 'default',
  mealType = 'all',
  want_eat = ''
} = {}) {
  const url = `/family/getCombos/${member_ids}`;

  const requestBody = {
    meal_type: mealType,
    need_tags: need_tags,
    cuisine: cuisine,
    category: category,
    members: members,
    province_code: province_code,
    want_eat: want_eat
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

    console.error('getCombos：', json.message || json);
    return [];
  } catch (error) {
    console.error('getCombos请求失败：', error);
    return [];
  }
}
export async function getTagTbl(group_code = "cuisine") {
  const url = `/family/getTagTbl/${group_code}`;
  const res  = await fetch(url);
  const json = await res.json();

  if (json.status === 'success') {
    return json.data;
  }

  console.error('getTagTbl：', json.message || json);
  return [];
}
export async function getDishReco(member_ids = "1,2", mealType = 'lunch', maxResults = 3) {
  const url = `/family/getDishReco/${member_ids}?meal_type=${mealType}&max_results=${maxResults}`;
  const res  = await fetch(url);
  const json = await res.json();

  if (json.status === 'success') {
    return json.data;
  }

  console.error('getDishReco：', json.message || json);
  return [];
}
export async function saveMemberDishLog(combo, members) {
  try {
    const response = await fetch('/family/saveMemberDishLog', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        combo: combo,
        members: members
      })
    });

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('saveMemberDishLog请求失败：', error);
    return { success: false, error: error.message };
  }
}
export async function searchDishReq(keyword) {
  try {
    const response = await fetch('/search/keyword', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        keyword: keyword
      })
    });

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('searchDish请求失败：', error);
    return { success: false, error: error.message };
  }
}