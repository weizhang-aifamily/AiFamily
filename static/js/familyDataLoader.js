export async function loadFamilyMembers(userId = 1) {
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
