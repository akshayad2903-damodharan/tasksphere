// Auto-refresh current time
function updateTime() {
    const now = new Date();
    const timeString = now.toLocaleString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });
    
    const timeElements = document.querySelectorAll('.current-time');
    timeElements.forEach(el => {
        el.textContent = timeString;
    });
}

// Update time every second
setInterval(updateTime, 1000);
updateTime();

// Smooth animations for cards
document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.stat-card, .profile-card, .activity-section, .tasks-section');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        setTimeout(() => {
            card.style.transition = 'all 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
});

// Confirm delete with better UX
document.querySelectorAll('.btn-danger').forEach(btn => {
    btn.addEventListener('click', function(e) {
        e.preventDefault();
        if (confirm('Are you sure you want to delete this task? This action cannot be undone.')) {
            window.location.href = this.href;
        }
    });
});

// Form validation enhancements
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.style.borderColor = '#ef4444';
                isValid = false;
            } else {
                field.style.borderColor = '#e5e7eb';
            }
        });
        
        if (!isValid) {
            e.preventDefault();
            alert('Please fill in all required fields.');
        }
    });
});
