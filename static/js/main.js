// TrendZee Main JavaScript

// ─── Navbar ──────────────────────────────────────
function toggleUserMenu() {
  const dropdown = document.getElementById('userDropdown');
  if (dropdown) dropdown.classList.toggle('open');
}

function toggleMobileNav() {
  const navLinks = document.querySelector('.nav-links');
  if (navLinks) navLinks.classList.toggle('open');
}

// ─── Theme Toggle ──────────────────────────────────
function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('tz-theme', next);
  updateThemeIcon(next);
}

function updateThemeIcon(theme) {
  const icon = document.getElementById('themeIcon');
  if (icon) {
    icon.className = theme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
  }
}

// Set correct icon on page load
document.addEventListener('DOMContentLoaded', function () {
  const theme = localStorage.getItem('tz-theme') || 'dark';
  updateThemeIcon(theme);
});

// Close dropdowns when clicking outside
document.addEventListener('click', (e) => {
  if (!e.target.closest('.nav-user-menu')) {
    const dropdown = document.getElementById('userDropdown');
    if (dropdown) dropdown.classList.remove('open');
  }
  if (!e.target.closest('.nav-mobile-toggle') && !e.target.closest('.nav-links')) {
    const navLinks = document.querySelector('.nav-links');
    if (navLinks && navLinks.classList.contains('open')) {
      navLinks.classList.remove('open');
    }
  }
});

// ─── Save Trend Toggle ────────────────────────────
function initSaveButtons() {
  document.querySelectorAll('.save-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();

      const trendId = btn.dataset.trendId;
      const csrfToken = getCookie('csrftoken');

      if (!trendId) return;

      btn.disabled = true;
      try {
        const response = await fetch(`/trends/${trendId}/save/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
          },
        });

        const data = await response.json();

        if (data.saved) {
          btn.classList.add('saved');
          btn.innerHTML = '<i class="fas fa-heart"></i>';
          btn.title = 'Remove from saved';
        } else {
          btn.classList.remove('saved');
          btn.innerHTML = '<i class="far fa-heart"></i>';
          btn.title = 'Save trend';
        }

        showToast(data.message, 'success');
      } catch (err) {
        console.error('Save failed:', err);
        showToast('Failed to save trend. Please try again.', 'error');
      } finally {
        btn.disabled = false;
      }
    });
  });
}

// ─── Chatbot ──────────────────────────────────────
function initChatbot() {
  const input = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');
  const messagesDiv = document.getElementById('chatMessages');

  if (!input || !sendBtn || !messagesDiv) return;

  let history = [];

  const addMessage = (content, role) => {
    const msg = document.createElement('div');
    msg.className = `chat-message chat-message--${role} fade-in`;

    const avatarChar = role === 'user'
      ? (window.USER_INITIAL || 'U')
      : '🤖';

    // Render markdown-like formatting for AI responses
    const formattedContent = role === 'ai' ? renderMarkdown(content) : escapeHtml(content);

    msg.innerHTML = `
      <div class="message-avatar ${role === 'ai' ? 'message-avatar--ai' : ''}">${avatarChar}</div>
      <div class="message-bubble">${formattedContent}</div>
    `;
    messagesDiv.appendChild(msg);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  };

  const addTypingIndicator = () => {
    const typing = document.createElement('div');
    typing.className = 'chat-message chat-message--ai';
    typing.id = 'typingIndicator';
    typing.innerHTML = `
      <div class="message-avatar message-avatar--ai">🤖</div>
      <div class="message-bubble" style="display:flex;gap:5px;align-items:center;">
        <span class="spinner"></span> Analyzing trends...
      </div>
    `;
    messagesDiv.appendChild(typing);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  };

  const removeTypingIndicator = () => {
    const t = document.getElementById('typingIndicator');
    if (t) t.remove();
  };

  const sendMessage = async () => {
    const question = input.value.trim();
    if (!question) return;

    addMessage(question, 'user');
    history.push({ role: 'user', content: question });
    input.value = '';
    sendBtn.disabled = true;
    addTypingIndicator();

    const csrfToken = getCookie('csrftoken');

    try {
      const response = await fetch('/trends/chatbot/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question, history }),
      });

      const data = await response.json();
      removeTypingIndicator();

      if (response.status === 429) {
        addMessage('You\'re sending messages too quickly. Please wait a moment.', 'ai');
      } else if (data.response) {
        addMessage(data.response, 'ai');
        history.push({ role: 'assistant', content: data.response });
      } else if (data.error) {
        addMessage('Sorry, something went wrong. Please try again.', 'ai');
      }
    } catch (err) {
      removeTypingIndicator();
      addMessage('Connection error. Please try again.', 'ai');
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  };

  sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
}

// ─── Simple Markdown Renderer ─────────────────────
function renderMarkdown(text) {
  if (!text) return '';
  let html = escapeHtml(text);

  // Bold: **text**
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

  // Italic: *text*
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Headings: ## text
  html = html.replace(/^### (.+)$/gm, '<h4 style="margin:12px 0 6px;font-size:13px;color:var(--t-primary)">$1</h4>');
  html = html.replace(/^## (.+)$/gm, '<h3 style="margin:14px 0 6px;font-size:14px;color:var(--t-primary)">$1</h3>');

  // Bullet points: - text or * text
  html = html.replace(/^[-*] (.+)$/gm, '<div style="padding-left:12px;margin:2px 0">• $1</div>');

  // Numbered lists: 1. text
  html = html.replace(/^\d+\. (.+)$/gm, '<div style="padding-left:12px;margin:2px 0">$1</div>');

  // Line breaks
  html = html.replace(/\n/g, '<br>');

  return html;
}

// ─── Table Sorting ────────────────────────────────
function initTableSorting() {
  const table = document.getElementById('trendTable');
  if (!table) return;

  const headers = table.querySelectorAll('th.sortable');
  headers.forEach(header => {
    header.addEventListener('click', () => {
      const tbody = table.querySelector('tbody');
      const rows = Array.from(tbody.querySelectorAll('tr'));
      const sortKey = header.dataset.sort;
      const isAsc = header.classList.contains('sort-asc');

      // Reset all headers
      headers.forEach(h => {
        h.classList.remove('sort-asc', 'sort-desc');
        h.textContent = h.textContent.replace(/ [↑↓]/g, '');
      });

      rows.sort((a, b) => {
        let valA, valB;

        if (sortKey === 'score') {
          valA = parseFloat(a.querySelector('.score-cell')?.textContent || '0');
          valB = parseFloat(b.querySelector('.score-cell')?.textContent || '0');
        } else if (sortKey === 'title') {
          valA = a.querySelector('.trend-title-link')?.textContent?.toLowerCase() || '';
          valB = b.querySelector('.trend-title-link')?.textContent?.toLowerCase() || '';
          return isAsc ? valB.localeCompare(valA) : valA.localeCompare(valB);
        } else {
          valA = parseInt(a.cells[0]?.textContent || '0');
          valB = parseInt(b.cells[0]?.textContent || '0');
        }

        return isAsc ? valA - valB : valB - valA;
      });

      header.classList.add(isAsc ? 'sort-desc' : 'sort-asc');
      header.textContent += isAsc ? ' ↓' : ' ↑';

      rows.forEach(row => tbody.appendChild(row));
    });
  });
}

// ─── Toast Notifications ──────────────────────────
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  const borderColor = type === 'error' ? 'var(--rose)' : type === 'success' ? 'var(--emerald)' : 'var(--border-hover)';
  toast.style.cssText = `
    position: fixed; bottom: 24px; right: 24px;
    padding: 12px 20px;
    background: var(--bg-elevated);
    border: 1px solid ${borderColor};
    border-radius: 8px;
    font-size: 14px;
    color: var(--text-primary);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    z-index: 9999;
    animation: fadeIn 0.3s ease;
  `;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 2500);
}

// ─── Utilities ────────────────────────────────────
function getCookie(name) {
  const v = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
  return v ? v[2] : null;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// ─── Init ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initSaveButtons();
  initChatbot();
  initTableSorting();
});
