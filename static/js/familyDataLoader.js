export async function getMembers(userId = 1) {
  const res  = await fetch(`/family/getMembers/${userId}`);
  const json = await res.json();

  console.log('原始返回：', json);   // ← 关键打印

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
export async function getCombos(member_ids = "1,2") {
  const res  = await fetch(`/family/getCombos/${member_ids}`);
  const json = await res.json();

  if (json.status === 'success') {
    return json.data;
  }

  console.error('getCombos：', json.message || json);
  return [];
}
