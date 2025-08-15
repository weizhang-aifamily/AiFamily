document.addEventListener('DOMContentLoaded', function() {
    // DOM元素
    const prevDayBtn = document.getElementById('prevDay');
    const nextDayBtn = document.getElementById('nextDay');
    const currentDateEl = document.getElementById('currentDate');
    const cameraBtn = document.getElementById('cameraBtn');
    const scanBtn = document.getElementById('scanBtn');
    const manualBtn = document.getElementById('manualBtn');
    const cameraModal = document.getElementById('cameraModal');
    const closeCameraBtn = document.getElementById('closeCameraBtn');
    const captureBtn = document.getElementById('captureBtn');
    const mealTabs = document.querySelectorAll('.tab');

    // 当前日期
    let currentDate = new Date();

    // 初始化页面
    updateDateDisplay();

    // 事件监听
    prevDayBtn.addEventListener('click', goToPreviousDay);
    nextDayBtn.addEventListener('click', goToNextDay);
    cameraBtn.addEventListener('click', openCameraModal);
    closeCameraBtn.addEventListener('click', closeCameraModal);
    captureBtn.addEventListener('click', capturePhoto);

    mealTabs.forEach(tab => {
        tab.addEventListener('click', () => switchMealTab(tab));
    });

    // 点击空白处关闭弹窗
    window.addEventListener('click', (e) => {
        if (e.target === cameraModal) closeCameraModal();
    });

    // 日期导航函数
    function goToPreviousDay() {
        currentDate.setDate(currentDate.getDate() - 1);
        updateDateDisplay();
        // 这里可以添加加载当天数据的逻辑
    }

    function goToNextDay() {
        // 不允许选择未来日期
        const today = new Date();
        if (currentDate >= today) return;

        currentDate.setDate(currentDate.getDate() + 1);
        updateDateDisplay();
        // 这里可以添加加载当天数据的逻辑
    }

    function updateDateDisplay() {
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        currentDateEl.textContent = currentDate.toLocaleDateString('zh-CN', options);

        // 禁用"明天"按钮如果是今天
        const today = new Date();
        nextDayBtn.disabled = currentDate.toDateString() === today.toDateString();
    }

    // 相机功能函数
    function openCameraModal() {
        cameraModal.style.display = 'flex';
        // 实际项目中这里应该初始化摄像头
    }

    function closeCameraModal() {
        cameraModal.style.display = 'none';
        // 实际项目中这里应该关闭摄像头
    }

    function capturePhoto() {
        // 模拟拍照
        alert('拍照成功！模拟识别中...');
        setTimeout(() => {
            closeCameraModal();
            // 这里可以添加识别后的处理逻辑
        }, 1500);
    }

    // 切换餐别标签
    function switchMealTab(selectedTab) {
        // 移除所有active类
        mealTabs.forEach(tab => tab.classList.remove('active'));
        // 添加active类到选中标签
        selectedTab.classList.add('active');
        // 这里可以添加加载对应餐别数据的逻辑
    }

    // 扫描条形码功能（模拟）
    scanBtn.addEventListener('click', () => {
        alert('模拟扫描条形码功能\n实际项目中应调用摄像头扫描API');
    });

    // 手动输入功能（模拟）
    manualBtn.addEventListener('click', () => {
        alert('模拟手动输入弹窗\n实际项目中应显示表单');
    });
});