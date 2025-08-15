// Initialize selected solutions and members
let selectedSolutions = ['picky-eater'];
let selectedMembers = ['child', 'elder', 'adult'];

// Member selection handling
document.querySelectorAll('.status-card').forEach(card => {
    card.addEventListener('click', function() {
        this.classList.toggle('selected');
        const member = this.dataset.member;
        
        if(this.classList.contains('selected')) {
            if(!selectedMembers.includes(member)) {
                selectedMembers.push(member);
            }
        } else {
            selectedMembers = selectedMembers.filter(m => m !== member);
        }
    });
});

// Solution selection handling
document.querySelectorAll('.solution-card').forEach(card => {
    card.addEventListener('click', function() {
        // If clicking on already selected recommended solution, don't deselect
        if(this.classList.contains('recommended') && this.classList.contains('selected')) {
            return;
        }
        
        this.classList.toggle('selected');
        const solution = this.dataset.solution;
        
        if(this.classList.contains('selected')) {
            if(!selectedSolutions.includes(solution)) {
                selectedSolutions.push(solution);
            }
        } else {
            selectedSolutions = selectedSolutions.filter(s => s !== solution);
        }
    });
});

// Select/deselect all members
function toggleAllMembers() {
    const allSelected = selectedMembers.length === 3;
    
    document.querySelectorAll('.status-card').forEach(card => {
        const member = card.dataset.member;
        
        if(allSelected) {
            card.classList.remove('selected');
            selectedMembers = selectedMembers.filter(m => m !== member);
        } else {
            card.classList.add('selected');
            if(!selectedMembers.includes(member)) {
                selectedMembers.push(member);
            }
        }
    });
}

// Select/deselect all solutions
function toggleAllSolutions() {
    const allSelected = selectedSolutions.length === 4;
    
    document.querySelectorAll('.solution-card').forEach(card => {
        const solution = card.dataset.solution;
        
        if(allSelected) {
            // Keep recommended solution selected
            if(!card.classList.contains('recommended')) {
                card.classList.remove('selected');
                selectedSolutions = selectedSolutions.filter(s => s !== solution);
            }
        } else {
            card.classList.add('selected');
            if(!selectedSolutions.includes(solution)) {
                selectedSolutions.push(solution);
            }
        }
    });
}

// Update recommendations
function updateRecommendations() {
    // Generate recommendations based on selected members and solutions
    let recommendedFoods = [];
    let recommendedDishes = [];
    
    // Generate based on members
    if(selectedMembers.includes('child')) {
        recommendedFoods.push({
            name: '奶酪',
            icon: '🧀',
            desc: '钙含量: 720mg/100g',
            tag: '高钙',
            //reason: '🤖 AI推荐：孩子喜欢的乳制品，补钙效果佳'
        });
        
        recommendedDishes.push(
            {name: '奶酪焗南瓜', image: 'https://example.com/dish1.jpg'},
            {name: '牛奶布丁', image: 'https://example.com/dish2.jpg'}
        );
    }
    
    if(selectedMembers.includes('elder')) {
        recommendedFoods.push({
            name: '香菇',
            icon: '🍄',
            desc: '低钠高鲜',
            tag: '调味',
            //reason: '🤖 AI推荐：天然鲜味替代盐，适合老年人'
        });
        
        recommendedDishes.push(
            {name: '香菇蒸鸡', image: 'https://example.com/dish3.jpg'},
            {name: '素炒三鲜', image: 'https://example.com/dish4.jpg'}
        );
    }
    
    if(selectedMembers.includes('adult')) {
        recommendedFoods.push({
            name: '菠菜',
            icon: '🥬',
            desc: '铁含量: 2.7mg/100g',
            tag: '补铁',
            //reason: '🤖 AI推荐：富含铁元素，适合成年女性'
        });
        
        recommendedDishes.push(
            {name: '蒜蓉菠菜', image: 'https://example.com/dish5.jpg'},
            {name: '菠菜蛋汤', image: 'https://example.com/dish6.jpg'}
        );
    }
    
    // Generate based on solutions
    if(selectedSolutions.includes('picky-eater')) {
        recommendedFoods.push({
            name: '胡萝卜',
            icon: '🥕',
            desc: '维生素A丰富',
            tag: '隐藏食材',
            //reason: '🤖 AI推荐：可切碎隐藏在其他食物中'
        });
    }
    
    if(selectedSolutions.includes('low-salt')) {
        recommendedFoods.push({
            name: '柠檬',
            icon: '🍋',
            desc: '天然调味',
            tag: '低钠',
            reason: '🤖 AI推荐：用酸味替代咸味'
        });
        
        recommendedDishes.push(
            {name: '柠檬蒸鱼', image: 'https://example.com/dish7.jpg'}
        );
    }
    
    if(selectedSolutions.includes('high-calcium')) {
        recommendedFoods.push({
            name: '芝麻酱',
            icon: '🌰',
            desc: '钙含量: 1170mg/100g',
            tag: '高钙',
            reason: '🤖 AI推荐：钙含量是牛奶的10倍'
        });
        
        recommendedDishes.push(
            {name: '麻酱菠菜', image: 'https://example.com/dish8.jpg'}
        );
    }
    
    if(selectedSolutions.includes('low-fat')) {
        recommendedFoods.push({
            name: '鸡胸肉',
            icon: '🍗',
            desc: '低脂高蛋白',
            tag: '减脂',
            reason: '🤖 AI推荐：优质蛋白质来源，脂肪含量低'
        });
        
        recommendedDishes.push(
            {name: '凉拌鸡丝', image: 'https://example.com/dish9.jpg'}
        );
    }
    
    // Update food recommendations
    const foodList = document.getElementById('foodList');
    foodList.innerHTML = recommendedFoods.map(food => `
        <div class="food-card">
            <div class="food-icon">${food.icon}</div>
            <div class="food-info">
                <h4>${food.name}</h4>
                <p>${food.desc}</p>
            </div>
            <div class="food-tag">${food.tag}</div>
        </div>
    `).join('');
    
    // Update dish showcase
    const dishesGrid = document.getElementById('dishesGrid');
    dishesGrid.innerHTML = recommendedDishes.map(dish => `
        <div class="dish-card">
            <div class="dish-image">${dish.name}</div>
            <div class="dish-label">${dish.name}</div>
        </div>
    `).join('');
    
    // Scroll to dish showcase
    document.querySelector('.ai-dishes-showcase').scrollIntoView({
        behavior: 'smooth'
    });
}

// Habit tracker interactions
document.querySelectorAll('.btn-complete').forEach(btn => {
    btn.addEventListener('click', function() {
        const card = this.closest('.mission-card');
        card.classList.add('completed');
        
        // Update progress
        const progressBar = document.querySelector('.progress-fill');
        const currentWidth = parseInt(progressBar.style.width) || 0;
        progressBar.style.width = `${currentWidth + 5}%`;
        
        // Update streak count
        const streakCount = document.querySelector('.streak-counter strong');
        streakCount.textContent = parseInt(streakCount.textContent) + 1;
        
        // Show completion animation
        this.innerHTML = '✓ 已完成';
        setTimeout(() => {
            card.querySelector('.check-circle').innerHTML = '✓';
        }, 300);
    });
});

// Category tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', function() {
        document.querySelector('.tab.active').classList.remove('active');
        this.classList.add('active');
        
        const category = this.dataset.category;
        filterSuppliers(category);
    });
});

function filterSuppliers(category) {
    const cards = document.querySelectorAll('.supplier-card');
    
    cards.forEach(card => {
        if(category === 'all' || card.dataset.categories.includes(category)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// Initialize display
window.onload = function() {
    // Default display recommendations
    updateRecommendations();
    filterSuppliers('all');
};

window.dispatchEvent(new Event('resize'));