// === Меню пользователя ===
document.addEventListener('DOMContentLoaded', () => {
  const trigger = document.getElementById('user-menu-trigger');
  const menu = document.getElementById('user-menu');
  const avatarImg = document.getElementById('user-avatar-img');
  const profileLink = document.getElementById('profile-or-platform');

  if (trigger && menu) {
    // Показ/скрытие меню
    trigger.addEventListener('click', (e) => {
      e.stopPropagation();
      menu.classList.toggle('hidden');
    });

    // Скрытие при клике вне
    document.addEventListener('click', () => {
      menu.classList.add('hidden');
    });

    menu.addEventListener('click', (e) => {
      e.stopPropagation(); // Не скрывать при клике по меню
    });
    
    // Динамическая ссылка: "Профиль" или "Платформа"
    const path = window.location.pathname;
    if (path === '/platform') {
      profileLink.textContent = 'Профиль';
      profileLink.href = '/profile';
    } else {
      profileLink.textContent = 'Платформа';
      profileLink.href = '/platform';
    }

    // Загрузка аватара
    if (avatarImg) {
      avatarImg.src = `/user/${window.current_user_id}/avatar`;
      avatarImg.onload = () => {
        avatarImg.classList.add('loaded');
      };
    }
  }

  // === Прокрутка чата вниз ===
  const historyEl = document.getElementById('chat-history');
  if (historyEl) {
    historyEl.scrollTop = historyEl.scrollHeight;

    const input = historyEl.querySelector('input[name="message"]');
    if (input) {
      input.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
          e.preventDefault();
          const form = input.closest('form');
          if (form) form.requestSubmit();
        }
      });
    }
  }

  // === Кнопка "случайный кот" ===
  const fetchBtn = document.getElementById('fetch-cat-btn');
  const catImg = document.getElementById('random-cat-img');
  if (fetchBtn && catImg) {
    fetchBtn.addEventListener('click', async () => {
      fetchBtn.disabled = true;
      const originalText = fetchBtn.textContent;
      fetchBtn.textContent = 'Загружаю...';

      try {
        const res = await fetch('/random-cat');
        if (!res.ok) throw new Error();
        const data = await res.json();

        if (data.url) {
          catImg.src = data.url;
          catImg.alt = 'Случайный кот';
          catImg.style.display = 'block';
        } else {
          throw new Error();
        }
      } catch {
        alert('Не удалось загрузить кота. Попробуйте ещё раз.');
      } finally {
        fetchBtn.disabled = false;
        fetchBtn.textContent = originalText;
      }
    });
  }
});
