export async function getMembers(userId = 1) {
  const res  = await fetch(`/family/getMembers/${userId}`);
  const json = await res.json();

  if (json.status === 'success') {
    console.log('解析后的成员列表：', json.data);
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
export async function getCombos(member_ids = "1,2", activeSolutions = 'highCalcium,lowFat', cuisine = 'sichuan') {
const mealType = new Date().getHours() < 10 ? 'breakfast' :
                 new Date().getHours() < 16 ? 'lunch' : 'dinner';
  const url = `/family/getCombos/${member_ids}?meal_type=${mealType}&cuisine=${cuisine}&activeSolutions=${activeSolutions}`;
  const res  = await fetch(url);
  const json = await res.json();

  if (json.status === 'success') {
    return json.data;
  }

  console.error('getCombos：', json.message || json);
  return [];
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
