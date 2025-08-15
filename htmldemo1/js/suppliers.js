// Supplier data
const suppliers = [
    {
        name: "五常大米",
        image: "https://via.placeholder.com/300x200?text=五常大米",
        categories: ["growth", "vegetarian"],
        tags: ["儿童营养", "低GI"],
        description: "蛋白质含量高出普通大米30%，适合儿童生长发育期食用",
        price: "¥39.9/5kg",
        badge: "基地直供"
    },
    {
        name: "有机藜麦",
        image: "https://via.placeholder.com/300x200?text=有机藜麦",
        categories: ["weight-loss", "chronic"],
        tags: ["高蛋白", "低GI"],
        description: "蛋白质含量高达14%，富含9种必需氨基酸，适合减脂控糖人群",
        price: "¥59.9/500g",
        badge: "有机认证"
    },
    {
        name: "高钙牛奶",
        image: "https://via.placeholder.com/300x200?text=高钙牛奶",
        categories: ["growth"],
        tags: ["儿童", "钙+30%"],
        description: "每100ml含钙150mg，特别添加维生素D促进钙吸收",
        price: "¥69.9/12盒",
        badge: "钙强化"
    },
    {
        name: "低钠酱油",
        image: "https://via.placeholder.com/300x200?text=低钠酱油",
        categories: ["chronic", "vegetarian"],
        tags: ["钠-50%", "三高友好"],
        description: "钠含量比普通酱油低50%，鲜味不减，适合高血压人群",
        price: "¥29.9/500ml",
        badge: "低钠"
    },
    {
        name: "有机鸡蛋",
        image: "https://via.placeholder.com/300x200?text=有机鸡蛋",
        categories: ["growth", "weight-loss"],
        tags: ["DHA", "无抗生素"],
        description: "富含DHA和卵磷脂，促进儿童大脑发育",
        price: "¥39.9/15枚",
        badge: "有机认证"
    },
    {
        name: "亚麻籽油",
        image: "https://via.placeholder.com/300x200?text=亚麻籽油",
        categories: ["chronic", "vegetarian"],
        tags: ["Omega-3", "低温冷榨"],
        description: "富含Omega-3脂肪酸，有助于心血管健康",
        price: "¥89.9/500ml",
        badge: "冷榨工艺"
    }
];

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    // Render all suppliers initially
    renderSuppliers('all');

    // Set up tab click events
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', function() {
            // Update active tab
            document.querySelector('.tab.active').classList.remove('active');
            this.classList.add('active');

            // Filter suppliers
            const category = this.dataset.category;
            renderSuppliers(category);
        });
    });
});

// Render suppliers based on category
function renderSuppliers(category) {
    const supplierGrid = document.getElementById('supplierGrid');
    supplierGrid.innerHTML = '';

    const filteredSuppliers = category === 'all'
        ? suppliers
        : suppliers.filter(supplier => supplier.categories.includes(category));

    filteredSuppliers.forEach(supplier => {
        const supplierCard = document.createElement('div');
        supplierCard.className = 'supplier-card';
        supplierCard.dataset.categories = supplier.categories.join(' ');

        supplierCard.innerHTML = `
            <div class="supplier-badge">${supplier.badge}</div>
            <img src="${supplier.image}" class="supplier-image">
            <div class="supplier-info">
                <h4>${supplier.name}</h4>
                <div class="supplier-tags">
                    ${supplier.tags.map(tag => `<span>${tag}</span>`).join('')}
                </div>
                <p class="supplier-desc">${supplier.description}</p>
                <div class="supplier-footer">
                    <span class="price">${supplier.price}</span>
                    <button class="supplier-btn">查看详情</button>
                </div>
            </div>
        `;

        supplierGrid.appendChild(supplierCard);
    });
}