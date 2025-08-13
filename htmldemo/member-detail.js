document.addEventListener('DOMContentLoaded', function() {
    // Slider functionality
    const sliderWrapper = document.getElementById('nutritionSlider');
    const dots = document.querySelectorAll('.slider-dot');
    let currentSlide = 0;
    const slideCount = document.querySelectorAll('.slider-slide').length;
    
    // Update slider position
    function updateSlider() {
        sliderWrapper.style.transform = `translateX(-${currentSlide * 100}%)`;
        
        // Update dot states
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === currentSlide);
        });
    }
    
    // Dot click events
    dots.forEach(dot => {
        dot.addEventListener('click', function() {
            currentSlide = parseInt(this.getAttribute('data-index'));
            updateSlider();
        });
    });
    
    // Touch swipe support
    let touchStartX = 0;
    let touchEndX = 0;
    
    sliderWrapper.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
    }, false);
    
    sliderWrapper.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }, false);
    
    function handleSwipe() {
        const diff = touchStartX - touchEndX;
        
        // Swipe left - next slide
        if (diff > 50 && currentSlide < slideCount - 1) {
            currentSlide++;
            updateSlider();
        }
        
        // Swipe right - previous slide
        if (diff < -50 && currentSlide > 0) {
            currentSlide--;
            updateSlider();
        }
    }
    
    // Tab switching
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            tabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            // Add content switching logic here if needed
        });
    });
});