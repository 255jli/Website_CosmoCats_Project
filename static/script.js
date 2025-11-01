// Карусель слов с улучшенной анимацией
const words = [
    "исследуют", "вдохновляют", "инновационируют", "революционизируют",
    "трансформируют", "оптимизируют", "катализируют", "синхронизируют",
    "мотивируют", "заряжают", "ускоряют", "продвигают", "создают",
    "разрабатывают", "открывают", "покоряют", "изменяют", "улучшают"
];

let currentIndex = 0;
const carouselElement = document.getElementById('word-carousel');

function animateTextChange() {
    const currentWord = words[currentIndex];
    const nextIndex = (currentIndex + 1) % words.length;
    const nextWord = words[nextIndex];
    
    // Эффект исчезновения
    carouselElement.style.opacity = '0';
    carouselElement.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        // Смена текста
        carouselElement.textContent = nextWord;
        
        // Эффект появления
        carouselElement.style.opacity = '1';
        carouselElement.style.transform = 'translateY(0)';
        
        currentIndex = nextIndex;
    }, 500);
}

// Запуск карусели
setInterval(animateTextChange, 3000);

// Анимация чисел статистики
function animateStats() {
    const statNumbers = document.querySelectorAll('.stat-number');
    
    statNumbers.forEach(stat => {
        const target = parseInt(stat.getAttribute('data-target'));
        const duration = 2000;
        const step = target / (duration / 16);
        let current = 0;
        
        const timer = setInterval(() => {
            current += step;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            stat.textContent = Math.floor(current);
        }, 16);
    });
}

// Запуск анимации статистики при скролле
const observerOptions = {
    threshold: 0.5,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            animateStats();
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

// Наблюдаем за секцией статистики
const statsSection = document.querySelector('.stats-section');
if (statsSection) {
    observer.observe(statsSection);
}

// Параллакс эффект для звезд
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const stars = document.querySelector('.stars');
    const stars2 = document.querySelector('.stars2');
    const stars3 = document.querySelector('.stars3');
    
    stars.style.transform = `translateY(${scrolled * 0.3}px)`;
    stars2.style.transform = `translateY(${scrolled * 0.6}px)`;
    stars3.style.transform = `translateY(${scrolled * 0.9}px)`;
});

// Интерактивность для карточек
document.querySelectorAll('.feature-card, .testimonial-card').forEach(card => {
    card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const angleY = (x - centerX) / 25;
        const angleX = (centerY - y) / 25;
        
        card.style.transform = `perspective(1000px) rotateX(${angleX}deg) rotateY(${angleY}deg)`;
    });
    
    card.addEventListener('mouseleave', () => {
        card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0)';
    });
});

// Плавная прокрутка для якорей
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
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

// Эффект печатной машинки для подзаголовка
function typeWriter(element, text, speed = 50) {
    let i = 0;
    element.innerHTML = '';
    
    function type() {
        if (i < text.length) {
            element.innerHTML += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    }
    type();
}

// Запуск эффекта печатной машинки при загрузке
document.addEventListener('DOMContentLoaded', () => {
    const subtitle = document.querySelector('.hero-subtitle');
    if (subtitle) {
        const originalText = subtitle.textContent;
        typeWriter(subtitle, originalText);
    }
});

// Случайные вспышки звезд
function createRandomStarFlashes() {
    setInterval(() => {
        const flash = document.createElement('div');
        flash.style.position = 'fixed';
        flash.style.width = '3px';
        flash.style.height = '3px';
        flash.style.background = 'white';
        flash.style.borderRadius = '50%';
        flash.style.left = Math.random() * 100 + 'vw';
        flash.style.top = Math.random() * 100 + 'vh';
        flash.style.boxShadow = '0 0 10px 2px white';
        flash.style.animation = 'starFlash 1s ease-out forwards';
        
        document.body.appendChild(flash);
        
        setTimeout(() => {
            flash.remove();
        }, 1000);
    }, 500);
}

// Добавляем CSS для анимации вспышек
const style = document.createElement('style');
style.textContent = `
    @keyframes starFlash {
        0% { opacity: 0; transform: scale(0); }
        50% { opacity: 1; transform: scale(2); }
        100% { opacity: 0; transform: scale(1); }
    }
`;
document.head.appendChild(style);

createRandomStarFlashes();

// Консольное приветствие
console.log(`
🚀🐱 Добро пожаловать в CosmoCats! 🐱🚀

Межгалактическая организация кошачьего превосходства

"Мы не просто коты - мы будущее вселенной!"

⚡ Особенности:
• Исследование дальних галактик
• Квантовые технологии сна
• Телескопическое зрение
• Одновременное нахождение в нескольких местах

Присоединяйся к нашей миссии! 🎯
`);