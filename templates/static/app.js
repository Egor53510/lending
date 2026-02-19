// ========================================
// SUNO AI MUSIC - INTERACTIVE JAVASCRIPT
// Version: 1.1
// Modern interactive features and animations
// ========================================

// Particles Animation
function createParticles() {
    const container = document.getElementById('particles');
    if (!container) return;
    
    const particleCount = 25;
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.cssText = `
            position: absolute;
            width: ${Math.random() * 4 + 2}px;
            height: ${Math.random() * 4 + 2}px;
            background: rgba(99, 102, 241, ${Math.random() * 0.5 + 0.2});
            border-radius: 50%;
            left: ${Math.random() * 100}%;
            top: ${Math.random() * 100}%;
            animation: float ${Math.random() * 10 + 10}s ease-in-out infinite;
            animation-delay: ${Math.random() * 5}s;
            pointer-events: none;
        `;
        container.appendChild(particle);
    }
}

// Smooth scroll for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Scroll to form function
function scrollToForm() {
    document.getElementById('contact').scrollIntoView({
        behavior: 'smooth',
        block: 'center'
    });
}

// Interactive Music Cards
function initMusicCards() {
    const musicCards = document.querySelectorAll('.music-card');
    const styleHint = document.getElementById('styleHint');
    const audioPlayer = document.getElementById('styleAudio');
    
    const styleMessages = {
        'rock': '🎸 Создай мощный рок-хит с гитарными риффами',
        'jazz': '🎹 Импровизируй в стиле джаза с саксофоном',
        'edm': '🎧 Сделай танцевальный EDM трек',
        'hip-hop': '🎤 Создай хип-хоп бит с крутым flow',
        'pop': '🎺 Напиши поп-хит, который зайдёт в чарты',
        'ambient': '🌙 Расслабься с эмбиент-саундтреком',
        'classical': '🎻 Напиши классическую композицию',
        'cinematic': '🎬 Создай эпичный саундтрек для фильма'
    };
    
    // Mapping style names to form values
    const styleMapping = {
        'rock': 'rock',
        'jazz': 'jazz', 
        'edm': 'electronic',
        'hip-hop': 'hip-hop',
        'pop': 'pop',
        'ambient': 'ambient',
        'classical': 'classical',
        'cinematic': 'cinematic'
    };
    
    musicCards.forEach(card => {
        card.addEventListener('click', function() {
            // Remove active class from all cards
            musicCards.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked card
            this.classList.add('active');
            
            // Get style name
            const styleName = this.querySelector('.card-name').textContent.toLowerCase();
            
            // Update hint text
            if (styleMessages[styleName]) {
                styleHint.textContent = styleMessages[styleName];
                styleHint.style.animation = 'none';
                setTimeout(() => {
                    styleHint.style.animation = 'hintPulse 2s ease-in-out infinite';
                }, 10);
            }
            
            // Update form field
            const styleSelect = document.getElementById('style');
            if (styleSelect && styleMapping[styleName]) {
                styleSelect.value = styleMapping[styleName];
                
                // Add visual feedback to form using CSS class
                styleSelect.classList.add('highlighted');
                setTimeout(() => {
                    styleSelect.classList.remove('highlighted');
                }, 2000);
            }
            
            // Visual feedback - pulse vinyl
            const vinyl = document.querySelector('.vinyl-record');
            vinyl.style.animation = 'none';
            setTimeout(() => {
                vinyl.style.animation = 'vinylSpin 2s linear infinite';
            }, 10);
            
            // Play a subtle click sound effect (using Web Audio API)
            playClickSound();
        });
        
        // Add hover sound effect
        card.addEventListener('mouseenter', function() {
            playHoverSound();
        });
    });
}

// Simple sound effects using Web Audio API
function playClickSound() {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.1);
    } catch (e) {
        // Silent fail if audio is not supported
    }
}

function playHoverSound() {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 600;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.05);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.05);
    } catch (e) {
        // Silent fail if audio is not supported
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initMusicCards();
    createParticles();
});

// Drag and Drop for Music Styles
function initDraggableStyles() {
    const draggables = document.querySelectorAll('.draggable-style');
    let draggedElement = null;
    let initialX = 0;
    let initialY = 0;
    let currentX = 0;
    let currentY = 0;

    draggables.forEach(el => {
        el.addEventListener('mousedown', startDrag);
        el.addEventListener('touchstart', startDrag, { passive: false });
    });

    function startDrag(e) {
        e.preventDefault();
        draggedElement = this;
        draggedElement.classList.add('dragging');
        
        const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
        const clientY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY;
        
        const rect = draggedElement.getBoundingClientRect();
        const parentRect = draggedElement.parentElement.getBoundingClientRect();
        
        initialX = clientX - rect.left;
        initialY = clientY - rect.top;

        document.addEventListener('mousemove', drag);
        document.addEventListener('mouseup', endDrag);
        document.addEventListener('touchmove', drag, { passive: false });
        document.addEventListener('touchend', endDrag);
    }

    function drag(e) {
        if (!draggedElement) return;
        e.preventDefault();
        
        const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
        const clientY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY;
        
        const parentRect = draggedElement.parentElement.getBoundingClientRect();
        
        let newX = clientX - parentRect.left - initialX;
        let newY = clientY - parentRect.top - initialY;
        
        // Bounds checking
        newX = Math.max(0, Math.min(newX, parentRect.width - draggedElement.offsetWidth));
        newY = Math.max(0, Math.min(newY, parentRect.height - draggedElement.offsetHeight));
        
        draggedElement.style.left = newX + 'px';
        draggedElement.style.top = newY + 'px';
        draggedElement.style.right = 'auto';
        draggedElement.style.bottom = 'auto';
    }

    function endDrag() {
        if (draggedElement) {
            draggedElement.classList.remove('dragging');
            draggedElement = null;
        }
        
        document.removeEventListener('mousemove', drag);
        document.removeEventListener('mouseup', endDrag);
        document.removeEventListener('touchmove', drag);
        document.removeEventListener('touchend', endDrag);
    }
}

// Form validation and submission
document.getElementById('leadForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const submitBtn = this.querySelector('button[type="submit"]');
    const submitText = document.getElementById('submitText');
    const submitLoader = document.getElementById('submitLoader');
    const formStatus = document.getElementById('formStatus');
    
    // Clear previous errors
    document.querySelectorAll('.error-message').forEach(el => {
        if (el.id !== 'phoneError') el.textContent = '';
    });
    
    // Get form values
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const phone = document.getElementById('phone').value.trim();
    const style = document.getElementById('style').value;
    const hasText = document.querySelector('input[name="has_text"]:checked').value;
    const textDescription = document.getElementById('text_description').value.trim();
    const message = document.getElementById('message').value.trim();
    
    // Validation
    let hasErrors = false;
    
    if (name.length < 2) {
        document.getElementById('nameError').textContent = 'Имя должно содержать минимум 2 символа';
        hasErrors = true;
    }
    
    const phoneRegex = /^\+7[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$/;
    if (!phoneRegex.test(phone)) {
        document.getElementById('phoneError').textContent = 'Введите телефон в формате +7 (999) 999-99-99';
        hasErrors = true;
    }
    
    if (!style) {
        document.getElementById('styleError').textContent = 'Выберите музыкальный стиль';
        hasErrors = true;
    }
    
    if (hasErrors) {
        formStatus.className = 'form-status error';
        formStatus.textContent = '✗ Пожалуйста, исправьте ошибки в форме';
        return;
    }
    
    // Show loading state
    submitBtn.disabled = true;
    submitText.classList.add('hidden');
    submitLoader.classList.remove('hidden');
    formStatus.className = 'form-status';
    formStatus.textContent = '';
    
    const formData = {
        name: name,
        email: email,
        phone: phone,
        style: style,
        has_text: hasText === 'yes',
        text_description: hasText === 'yes' ? textDescription : null,
        message: message || null,
        source: 'landing'
    };
    
    try {
        const response = await fetch('/api/leads', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            formStatus.className = 'form-status success';
            formStatus.textContent = '✓ Заявка успешно отправлена! Мы свяжемся с вами в ближайшее время.';
            this.reset();
            document.getElementById('textDescriptionGroup').classList.add('hidden');
            document.getElementById('phoneError').textContent = 'Формат: +7 (999) 999-99-99';
            
            setTimeout(() => {
                submitBtn.disabled = false;
                submitText.classList.remove('hidden');
                submitLoader.classList.add('hidden');
            }, 3000);
        } else {
            throw new Error(data.detail || 'Ошибка при отправке заявки');
        }
    } catch (error) {
        formStatus.className = 'form-status error';
        formStatus.textContent = '✗ ' + (error.message || 'Ошибка соединения. Попробуйте позже.');
        
        submitBtn.disabled = false;
        submitText.classList.remove('hidden');
        submitLoader.classList.add('hidden');
    }
});

// Toggle text description field
document.querySelectorAll('input[name="has_text"]').forEach(radio => {
    radio.addEventListener('change', function() {
        const textGroup = document.getElementById('textDescriptionGroup');
        if (this.value === 'yes') {
            textGroup.classList.remove('hidden');
            document.getElementById('text_description').setAttribute('required', 'required');
        } else {
            textGroup.classList.add('hidden');
            document.getElementById('text_description').removeAttribute('required');
        }
    });
});

// Fetch and display stats
async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        if (response.ok) {
            const data = await response.json();
            const totalTracksEl = document.getElementById('total-tracks');
            if (totalTracksEl && data.total_tracks) {
                totalTracksEl.textContent = data.total_tracks.toLocaleString() + '+';
            }
        }
    } catch (error) {
        console.log('Stats fetch failed:', error);
    }
}

// Navbar scroll effect
let lastScroll = 0;
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    const currentScroll = window.pageYOffset;
    
    if (currentScroll > 50) {
        navbar.style.background = 'rgba(15, 15, 26, 0.95)';
    } else {
        navbar.style.background = 'rgba(15, 15, 26, 0.8)';
    }
    
    lastScroll = currentScroll;
});

// Intersection Observer for animations
const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate-in');
        }
    });
}, observerOptions);

// Observe elements for animation
document.querySelectorAll('.benefit-card, .step, .testimonial-card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
});

// Add animate-in class styles
const style = document.createElement('style');
style.textContent = `
    .animate-in {
        opacity: 1 !important;
        transform: translateY(0) !important;
    }
`;
document.head.appendChild(style);

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    createParticles();
    initDraggableStyles();
    fetchStats();
});
