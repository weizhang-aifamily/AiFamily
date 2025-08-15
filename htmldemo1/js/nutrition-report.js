// 成员数据
const membersData = {
  "1": { // 小明
    type: "child",
    calories: { value: 1850, avg: 1650, unit: "大卡" },
    fiber: { value: 23, avg: 18, unit: "g" },
    sodium: { value: 2300, avg: 2000, unit: "mg" }
  },
  "2": { // 妈妈
    type: "adult",
    calories: { value: 1650, avg: 1800, unit: "大卡" },
    fiber: { value: 25, avg: 22, unit: "g" },
    sodium: { value: 2100, avg: 2000, unit: "mg" }
  },
  "3": { // 爸爸
    type: "adult",
    calories: { value: 2100, avg: 2200, unit: "大卡" },
    fiber: { value: 20, avg: 22, unit: "g" },
    sodium: { value: 2500, avg: 2000, unit: "mg" }
  }
};

const benefitTips = {
  child: {
    calories: "保持合理热量有助于儿童正常生长发育",
    fiber: "充足膳食纤维促进儿童肠道健康发育",
    sodium: "控制钠摄入预防儿童期高血压风险"
  },
  adult: {
    calories: "控制热量摄入有助于维持健康体重",
    fiber: "高纤维饮食降低成人慢性病风险",
    sodium: "低钠饮食降低心血管疾病风险"
  }
};

// 食物排名数据
const foodRankingData = {
  dishes: [
    { name: "炸鸡", icon: "🍗", meta: "高钠(1200mg/份) | 高热量(450kcal)", frequency: "本周3次" },
    { name: "薯条", icon: "🍟", meta: "高钠(800mg/份) | 高脂肪", frequency: "本周2次" },
    { name: "白米饭", icon: "🍚", meta: "碳水化合物 | 低纤维", frequency: "本周7次" }
  ],
  ingredients: [
    { name: "鸡肉", icon: "🍗", meta: "蛋白质 | 低脂肪", frequency: "本周5次" },
    { name: "土豆", icon: "🥔", meta: "碳水化合物 | 钾", frequency: "本周4次" },
    { name: "大米", icon: "🍚", meta: "碳水化合物 | 低纤维", frequency: "本周7次" }
  ]
};

// 初始化成员切换功能
function initMemberSwitcher() {
  const memberTabs = document.querySelectorAll('.member-tab');
  const memberAddBtn = document.querySelector('.member-add-btn');

  memberTabs.forEach(tab => {
    tab.addEventListener('click', function() {
      // 更新UI状态
      memberTabs.forEach(t => t.classList.remove('active'));
      this.classList.add('active');

      // 加载对应成员数据
      const memberId = this.dataset.memberId;
      loadMemberData(memberId);
    });
  });

  // 添加成员按钮事件
  memberAddBtn.addEventListener('click', function() {
    alert('跳转到添加家庭成员页面');
  });

  // 默认加载第一个成员
  memberTabs[0].click();
}

// 加载成员数据
function loadMemberData(memberId) {
  const member = membersData[memberId];
  if (!member) return;

  // 更新所有指标卡片
  updateMetricCard('calories', member);
  updateMetricCard('fiber', member);
  updateMetricCard('sodium', member);
}

// 更新单个指标卡片
function updateMetricCard(type, memberData) {
  const card = document.querySelector(`.metric-card[data-type="${type}"]`);
  if (!card) return;

  const data = memberData[type];
  const memberType = memberData.type;

  // 计算百分比 (钠是越低越好，其他是越高越好)
  let percentage, comparisonText, ringOffset;
  if (type === 'sodium') {
    percentage = Math.round((data.avg / data.value) * 100);
    comparisonText = percentage >= 100 ? '低于' : '高于';
    ringOffset = 157 - (157 * Math.min(percentage, 100)) / 100;
  } else {
    percentage = Math.round((data.value / data.avg) * 100);
    comparisonText = percentage >= 100 ? '高于' : '低于';
    ringOffset = 157 - (157 * Math.min(percentage, 150)) / 150;
  }

  // 更新主数值
  card.querySelector('.main-value .value').textContent = data.value.toLocaleString();
  card.querySelector('.main-value .unit').textContent = data.unit;

  // 更新环形进度条
  const ringFill = card.querySelector('.ring-fill');
  ringFill.style.strokeDasharray = '157 157';
  ringFill.style.strokeDashoffset = ringOffset;

  // 更新百分比
  card.querySelector('.percentage').textContent = `${percentage}%`;

  // 更新排名信息
  const rank = calculateRank(percentage, type);
  card.querySelector('.rank-badge').innerHTML = `
    ${rank.icon} 优于${rank.percent}%同龄人
  `;

  // 更新基准值
  card.querySelector('.benchmark').innerHTML = `
    <span class="label">同龄平均:</span>
    <span class="value">${data.avg.toLocaleString()}${data.unit}</span>
  `;

  // 更新健康提示
  card.querySelector('.benefit-tip').innerHTML = `
    <span class="icon">💡</span>
    ${benefitTips[memberType][type]}
  `;

  // 根据表现添加特殊类名
  card.classList.remove('excellent', 'good', 'warning');
  if (percentage >= 120) {
    card.classList.add('excellent');
  } else if (percentage >= 90) {
    card.classList.add('good');
  } else if (percentage < 80) {
    card.classList.add('warning');
  }
}

// 计算排名百分比
function calculateRank(percentage, type) {
  // 钠是越低越好，其他是越高越好
  const score = type === 'sodium' ? 100/Math.max(percentage, 1) : percentage;

  if (score >= 120) return { percent: 95, icon: '👑' };
  if (score >= 110) return { percent: 85, icon: '👍' };
  if (score >= 100) return { percent: 70, icon: '👌' };
  if (score >= 90) return { percent: 55, icon: '✋' };
  return { percent: 30, icon: '⚠️' };
}

// 初始化食物排名功能
function initFoodRanking() {
  const tabs = document.querySelectorAll('.tab-container .tab');
  const foodRankingContainer = document.getElementById('foodRankingContainer');
  const quickRecordBtn = document.getElementById('quickRecordBtn');

  // 加载食物排名数据
  function loadFoodRanking(type) {
    const data = foodRankingData[type] || [];
    let html = '';

    data.forEach(item => {
      html += `
        <div class="food-item">
          <div class="food-icon">${item.icon}</div>
          <div class="food-info">
            <div class="food-name">${item.name}</div>
            <div class="food-meta">${item.meta}</div>
          </div>
          <div class="food-frequency">${item.frequency}</div>
        </div>
      `;
    });

    foodRankingContainer.innerHTML = html || '<div class="no-data">暂无数据</div>';
  }

  // Tab切换事件
  tabs.forEach(tab => {
    tab.addEventListener('click', function() {
      tabs.forEach(t => t.classList.remove('active'));
      this.classList.add('active');
      const type = this.dataset.type;
      loadFoodRanking(type);
    });
  });

  // 快速记录按钮事件
  quickRecordBtn.addEventListener('click', function() {
    alert('跳转到快速记录页面');
  });

  // 默认加载菜品排名
  loadFoodRanking('dishes');
}

// 图表功能
function initChartButtons() {
  const chartBtns = document.querySelectorAll('.chart-btn');

  chartBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      chartBtns.forEach(b => b.classList.remove('active'));
      this.classList.add('active');

      const chartType = this.dataset.type;
      updateChart(chartType);
    });
  });
}

function updateChart(chartType) {
  const chartPlaceholder = document.getElementById('mainChart');
  chartPlaceholder.innerHTML = `[${getChartTitle(chartType)}趋势图表]`;
}

function getChartTitle(type) {
  const titles = {
    calories: '热量',
    protein: '蛋白质',
    sodium: '钠'
  };
  return titles[type] || type;
}

// 导出报告
function exportReport() {
  alert('模拟导出PDF报告功能\n实际项目中应调用PDF生成API');
}

// 获取改善方案
function showImprovePlan() {
  alert('跳转到改善方案页面\n可链接到家庭管理页面的饮食方案');
}

// 分享报告
function shareReport() {
  if (navigator.share) {
    navigator.share({
      title: '我的营养报告',
      text: '来自益家AiFamily的营养分析报告',
      url: window.location.href
    }).catch(err => {
      console.log('分享失败:', err);
      fallbackShare();
    });
  } else {
    fallbackShare();
  }
}

function fallbackShare() {
  alert('链接已复制到剪贴板\n可通过粘贴分享');
}

// 在DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
  initMemberSwitcher();
  initFoodRanking();
  initChartButtons();

  // 事件监听
  document.getElementById('periodSelect').addEventListener('change', function() {
    const activeTab = document.querySelector('.member-tab.active');
    if (activeTab) {
      loadMemberData(activeTab.dataset.memberId);
    }
  });

  document.getElementById('exportBtn').addEventListener('click', exportReport);
  document.getElementById('improvePlanBtn').addEventListener('click', showImprovePlan);
  document.getElementById('shareBtn').addEventListener('click', shareReport);
});