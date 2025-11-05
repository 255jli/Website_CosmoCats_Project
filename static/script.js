document.addEventListener('DOMContentLoaded', () => {
  const historyEl = document.getElementById('chat-history');
  if (historyEl) {
    // Scroll to bottom on load
    historyEl.scrollTop = historyEl.scrollHeight;

    // Submit on Ctrl/Cmd+Enter inside nearest input
    const input = historyEl.querySelector('input[name="message"]');
    if (input) {
      input.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
          const form = input.closest('form');
          if (form) form.submit();
        }
      });
    }
  }

  // Random cat button on index
  const fetchBtn = document.getElementById('fetch-cat-btn');
  const catImg = document.getElementById('random-cat-img');
  if (fetchBtn && catImg) {
    fetchBtn.addEventListener('click', async () => {
      fetchBtn.disabled = true;
      fetchBtn.textContent = 'Загружаю...';
      try {
        const res = await fetch('/random-cat');
        if (!res.ok) throw new Error('network');
        const j = await res.json();
        if (j.url) {
          catImg.src = j.url;
          catImg.style.display = 'block';
        } else {
          alert('Не удалось получить URL изображения.');
        }
      } catch (e) {
        alert('Ошибка при получении изображения кота.');
      } finally {
        fetchBtn.disabled = false;
        fetchBtn.textContent = 'Показать случайного кота';
      }
    });
  }
});

