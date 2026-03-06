/**
 * CHATIKKSS PILOT — Main Engine
 * Onboarding, Chat history, Settings, Web Speech API
 */

const socket = io();

// ─── DOM ────────────────────────────────────────────────────────

const $ = (s) => document.getElementById(s);

const onboarding = $('onboarding');
const obPage1 = $('obPage1');
const obPage2 = $('obPage2');
const obNext = $('obNext');
const obNameInput = $('obNameInput');
const obStart = $('obStart');
const appEl = $('app');
const chat = $('chat');
const msgInput = $('msgInput');
const sendBtn = $('sendBtn');
const micBtn = $('micBtn');
const themeBtn = $('themeBtn');
const settingsBtn = $('settingsBtn');
const closeSettingsBtn = $('closeSettingsBtn');
const settingsPanel = $('settingsPanel');
const clearAllBtn = $('clearAllBtn');
const ttsToggle = $('ttsToggle');
const autoPlayToggle = $('autoPlayToggle');
const confirmAllToggle = $('confirmAllToggle');
const nameInput = $('nameInput');
const voiceSelect = $('voiceSelect');
const historyToggle = $('historyToggle');
const sidebar = $('sidebar');
const sidebarOverlay = $('sidebarOverlay');
const historyList = $('historyList');
const newChatBtn = $('newChatBtn');
const welcome = $('welcome');
const welcomeName = $('welcomeName');
const ttsPlayer = $('ttsPlayer');
const toasts = $('toasts');

let recognition = null;
let isListening = false;
let thinkingEl = null;

// ─── Settings / State ───────────────────────────────────────────

let state = {
    name: '',
    theme: 'dark',
    fontSize: 'medium',
    ttsEnabled: true,
    autoPlay: true,
    confirmAll: false,
    onboarded: false,
    voice: 'ru-RU-DmitryNeural',
    msgCount: 0,
    msgDate: new Date().toLocaleDateString('ru-RU'),
    chats: [],          // { id, title, messages: [{role, text, time}] }
    currentChatId: null,
};

function loadState() {
    try {
        const s = localStorage.getItem('cp_state');
        if (s) state = { ...state, ...JSON.parse(s) };
    } catch (e) { }
}

function saveState() {
    localStorage.setItem('cp_state', JSON.stringify(state));
}

loadState();

// ─── Init ───────────────────────────────────────────────────────

function init() {
    applyTheme(state.theme);
    applyFontSize(state.fontSize);

    ttsToggle.checked = state.ttsEnabled;
    autoPlayToggle.checked = state.autoPlay;
    confirmAllToggle.checked = state.confirmAll;
    nameInput.value = state.name;
    if (voiceSelect) voiceSelect.value = state.voice || 'ru-RU-DmitryNeural';

    if (!state.onboarded) {
        onboarding.style.display = 'flex';
        appEl.classList.add('hidden');
    } else {
        onboarding.style.display = 'none';
        appEl.classList.remove('hidden');
        welcomeName.textContent = state.name || 'друг';

        // Send name to server
        socket.emit('set_name', { name: state.name });

        // Load current chat or create new
        if (!state.currentChatId || !state.chats.find(c => c.id === state.currentChatId)) {
            newChat(false);
        } else {
            loadChat(state.currentChatId);
        }

        renderHistory();
    }
}

// ─── Onboarding ─────────────────────────────────────────────────

obNext.addEventListener('click', () => {
    obPage1.classList.remove('active');
    obPage2.classList.add('active');
    setTimeout(() => obNameInput.focus(), 300);
});

obNameInput.addEventListener('input', () => {
    obStart.disabled = !obNameInput.value.trim();
});

obStart.addEventListener('click', () => {
    let name = obNameInput.value.trim();
    if (!name) return;

    // Сразу с большой буквы
    name = name.charAt(0).toUpperCase() + name.slice(1);

    state.name = name;
    state.onboarded = true;
    saveState();

    onboarding.style.display = 'none';
    appEl.classList.remove('hidden');
    welcomeName.textContent = name;
    nameInput.value = name;

    socket.emit('set_name', { name });
    newChat(false);
    renderHistory();
});

// Enter in name input
obNameInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && obNameInput.value.trim()) {
        obStart.click();
    }
});

// ─── Theme ──────────────────────────────────────────────────────

function applyTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    document.querySelectorAll('.pill[data-theme]').forEach(p => {
        p.classList.toggle('active', p.dataset.theme === t);
    });
    state.theme = t;
}

themeBtn.addEventListener('click', () => {
    const next = state.theme === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    saveState();
});

document.querySelectorAll('.pill[data-theme]').forEach(p => {
    p.addEventListener('click', () => {
        applyTheme(p.dataset.theme);
        saveState();
    });
});

// ─── Font Size ──────────────────────────────────────────────────

function applyFontSize(size) {
    document.documentElement.setAttribute('data-size', size);
    document.querySelectorAll('.pill-sm[data-size]').forEach(p => {
        p.classList.toggle('active', p.dataset.size === size);
    });
    state.fontSize = size;
}

document.querySelectorAll('.pill-sm[data-size]').forEach(p => {
    p.addEventListener('click', () => {
        applyFontSize(p.dataset.size);
        saveState();
    });
});

// ─── Settings Panel ─────────────────────────────────────────────

settingsBtn.addEventListener('click', () => {
    settingsPanel.classList.toggle('open');
});

if (closeSettingsBtn) {
    closeSettingsBtn.addEventListener('click', () => {
        settingsPanel.classList.remove('open');
    });
}

// Close settings on click outside (back button area)
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        settingsPanel.classList.remove('open');
        closeSidebar();
    }
});

ttsToggle.addEventListener('change', () => {
    state.ttsEnabled = ttsToggle.checked;
    saveState();
});

autoPlayToggle.addEventListener('change', () => {
    state.autoPlay = autoPlayToggle.checked;
    saveState();
});

confirmAllToggle.addEventListener('change', () => {
    state.confirmAll = confirmAllToggle.checked;
    saveState();
    socket.emit('update_settings', { confirm_all: state.confirmAll, voice: state.voice });
});

if (voiceSelect) {
    voiceSelect.addEventListener('change', () => {
        state.voice = voiceSelect.value;
        saveState();
        socket.emit('update_settings', { voice: state.voice });
        toast('Голос изменён', 'success');
    });
}

nameInput.addEventListener('change', () => {
    let newName = nameInput.value.trim();
    if (newName) {
        newName = newName.charAt(0).toUpperCase() + newName.slice(1);
    }
    state.name = newName;
    welcomeName.textContent = state.name || 'друг';
    saveState();
    socket.emit('set_name', { name: state.name });
    toast('Имя обновлено', 'success');
});

clearAllBtn.addEventListener('click', () => {
    if (confirm('Удалить все данные? Это действие нельзя отменить.')) {
        localStorage.removeItem('cp_state');
        location.reload();
    }
});

// ─── Sidebar (History) ──────────────────────────────────────────

historyToggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    sidebarOverlay.classList.toggle('open');
});

sidebarOverlay.addEventListener('click', closeSidebar);

function closeSidebar() {
    sidebar.classList.remove('open');
    sidebarOverlay.classList.remove('open');
}

function renderHistory() {
    historyList.innerHTML = '';
    // Отображаем только чаты с сообщениями
    const sorted = [...state.chats].filter(c => c.messages.length > 0).reverse();

    if (sorted.length === 0) {
        historyList.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);font-size:12px;">Пока нет чатов</div>';
        return;
    }

    sorted.forEach(c => {
        const item = document.createElement('div');
        item.className = `chat-item${c.id === state.currentChatId ? ' active' : ''}`;
        item.innerHTML = `
            <span class="chat-item-title">${c.title || 'Новый чат'}</span>
            <button class="chat-item-del" data-id="${c.id}" title="Удалить">✕</button>
        `;
        item.addEventListener('click', (e) => {
            if (e.target.classList.contains('chat-item-del')) return;
            loadChat(c.id);
            closeSidebar();
        });
        historyList.appendChild(item);
    });

    // Delete buttons
    document.querySelectorAll('.chat-item-del').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteChat(btn.dataset.id);
        });
    });
}

// ─── Chat Management ────────────────────────────────────────────

function newChat(closeSb = true) {
    const id = 'chat_' + Date.now();
    state.chats.push({ id, title: '', messages: [] });
    state.currentChatId = id;
    saveState();

    // Clear server history
    socket.emit('clear_history');
    socket.emit('set_name', { name: state.name });

    // Reset UI
    clearChatUI();
    renderHistory();
    if (closeSb) closeSidebar();
}

function loadChat(id) {
    const chatData = state.chats.find(c => c.id === id);
    if (!chatData) return;

    state.currentChatId = id;
    saveState();

    // Clear and rebuild UI
    clearChatUI();

    if (chatData.messages.length === 0) {
        if (welcome) welcome.style.display = '';
    } else {
        if (welcome) welcome.style.display = 'none';
        chatData.messages.forEach(m => {
            addMsgUI(m.role, m.text, null, m.time, false);
        });
    }

    // Reload server context
    socket.emit('clear_history');
    socket.emit('set_name', { name: state.name });

    // Replay messages to rebuild Mistral context
    chatData.messages.forEach(m => {
        socket.emit('replay_message', { role: m.role, content: m.text });
    });

    renderHistory();
}

function deleteChat(id) {
    state.chats = state.chats.filter(c => c.id !== id);

    if (state.currentChatId === id) {
        if (state.chats.length > 0) {
            loadChat(state.chats[state.chats.length - 1].id);
        } else {
            newChat(false);
        }
    }

    saveState();
    renderHistory();
}

function clearChatUI() {
    chat.innerHTML = '';
    if (welcome) {
        chat.appendChild(welcome);
        welcome.style.display = '';
    }
}

function saveMsgToChat(role, text) {
    const chatData = state.chats.find(c => c.id === state.currentChatId);
    if (!chatData) return;

    const time = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    chatData.messages.push({ role, text, time });

    // Set title from first user message
    if (!chatData.title && role === 'user') {
        chatData.title = text.length > 40 ? text.slice(0, 40) + '...' : text;
        renderHistory();
    }

    saveState();
}

newChatBtn.addEventListener('click', () => newChat());

// ─── Web Speech API ─────────────────────────────────────────────

// ─── Voice Recording (Backend PyAudio) ──────────────────────────────

function startListening() {
    if (isListening) return;
    isListening = true;
    micBtn.classList.add('active');
    socket.emit('start_voice');
}

function stopListening() {
    isListening = false;
    micBtn.classList.remove('active');
}

socket.on('voice_recognized', (data) => {
    stopListening();
    if (data.text) {
        // Эффект плавного набора текста в поле ввода
        msgInput.value = '';
        let i = 0;
        toast('Распознано!', 'success');
        function typeWriter() {
            if (i < data.text.length) {
                msgInput.value += data.text.charAt(i);
                i++;
                setTimeout(typeWriter, 15); // Скорость печати
            } else {
                // Отправляем спустя 0.4 сек после допечатки
                setTimeout(() => sendMessage(), 400);
            }
        }
        typeWriter();
    }
});

socket.on('voice_stop', () => stopListening());

micBtn.addEventListener('click', () => isListening ? stopListening() : startListening());

// ─── Socket Events ──────────────────────────────────────────────

socket.on('connect', () => {
    // Re-send state on reconnect
    if (state.name) socket.emit('set_name', { name: state.name });
    socket.emit('update_settings', { confirm_all: state.confirmAll, voice: state.voice });
});

socket.on('disconnect', () => {
    // disconnected
});

socket.on('thinking', (data) => {
    data.status ? showThinking() : hideThinking();
});

socket.on('response', (data) => {
    hideThinking();
    if (welcome) welcome.style.display = 'none';

    const text = data.text || '';
    addMsgUI('assistant', text, data.actions);
    saveMsgToChat('assistant', text);

    if (state.ttsEnabled && state.autoPlay && data.audio_url) {
        ttsPlayer.src = data.audio_url;
        ttsPlayer.play().catch(() => { });
    }
});

socket.on('action_result', (data) => {
    const card = document.querySelector(`[data-aid="${data.action_id}"]`);
    if (!card) return;
    const btns = card.querySelector('.ac-btns');
    if (!btns) return;

    if (data.denied) {
        btns.innerHTML = '<span class="ac-result denied">⛔ Отклонено</span>';
        toast('Отклонено', 'warning');
    } else if (data.success) {
        btns.innerHTML = `<span class="ac-result ok">✅ ${data.message}</span>`;
        toast(data.message, 'success');
    } else {
        btns.innerHTML = `<span class="ac-result fail">❌ ${data.message}</span>`;
        toast(data.message, 'error');
    }
});

socket.on('status', (data) => toast(data.message, data.type || 'info'));

// ─── Send ───────────────────────────────────────────────────────

function sendMessage(text) {
    text = text || msgInput.value.trim();
    if (!text) return;

    const today = new Date().toLocaleDateString('ru-RU');
    if (state.msgDate !== today) {
        state.msgDate = today;
        state.msgCount = 0;
    }

    if (state.msgCount >= 100) {
        toast('Лимит сообщений на сегодня исчерпан! Приходите завтра 🚀', 'error');
        return;
    }

    state.msgCount++;
    saveState();

    if (welcome) welcome.style.display = 'none';

    addMsgUI('user', text);
    saveMsgToChat('user', text);
    socket.emit('send_message', { message: text });
    msgInput.value = '';
}

sendBtn.addEventListener('click', () => sendMessage());
msgInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); sendMessage(); }
});

// ─── Message UI ─────────────────────────────────────────────────

function addMsgUI(role, text, actions, timeStr, animate = true) {
    const div = document.createElement('div');
    div.className = `msg ${role}`;
    if (!animate) div.style.animation = 'none';

    const time = timeStr || new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });

    let actionsHTML = '';
    if (actions) {
        actionsHTML = actions.filter(a => a.type !== 'none').map(actionCard).join('');
    }

    div.innerHTML = `
        <div class="msg-bubble">${fmt(text)}</div>
        ${actionsHTML}
        <span class="msg-time">${time}</span>
    `;

    chat.appendChild(div);
    scrollDown();
}

function actionCard(a) {
    const id = a.action_id || '';
    const desc = a.description || a.type;
    let btns = '';

    if (a.status === 'pending') {
        btns = `<div class="ac-btns">
            <button class="ac-btn yes" onclick="window._confirm('${id}')">✓ Да</button>
            <button class="ac-btn no" onclick="window._deny('${id}')">✕ Нет</button>
        </div>`;
    } else if (a.status === 'executed') {
        btns = `<span class="ac-result ok">✅ ${a.result?.message || 'Выполнено'}</span>`;
    } else if (a.status === 'blocked') {
        btns = `<span class="ac-result fail">🚫 ${a.reason}</span>`;
    }

    return `<div class="action-card" data-aid="${id}">
        <div class="ac-type">⚡ ${a.type}</div>
        <div class="ac-desc">${desc}</div>
        ${btns}
    </div>`;
}

// ─── Thinking ───────────────────────────────────────────────────

function showThinking() {
    if (thinkingEl) return;
    thinkingEl = document.createElement('div');
    thinkingEl.className = 'thinking';
    thinkingEl.innerHTML = '<span></span><span></span><span></span>';
    chat.appendChild(thinkingEl);
    scrollDown();
}

function hideThinking() {
    if (thinkingEl) { thinkingEl.remove(); thinkingEl = null; }
}

// ─── Utils ──────────────────────────────────────────────────────

function fmt(text) {
    if (!text) return '';
    text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    text = text.replace(/`(.*?)`/g, '<code style="background:var(--bg-hover);padding:1px 5px;border-radius:4px;font-size:12px;">$1</code>');
    text = text.replace(/\n/g, '<br>');
    return text;
}

function scrollDown() {
    requestAnimationFrame(() => { chat.scrollTop = chat.scrollHeight; });
}

function toast(msg, type) {
    const t = document.createElement('div');
    t.className = `toast ${type || 'info'}`;
    t.textContent = msg;
    toasts.appendChild(t);
    setTimeout(() => {
        t.style.animation = 'toastOut 0.3s ease forwards';
        setTimeout(() => t.remove(), 300);
    }, 2500);
}

// ─── Hotkeys ────────────────────────────────────────────────────

document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'm') {
        e.preventDefault();
        isListening ? stopListening() : startListening();
    }
});

// ─── Global ─────────────────────────────────────────────────────

window._send = sendMessage;
window._confirm = (id) => { socket.emit('confirm_action', { action_id: id }); toast('Выполняю...', 'info'); };
window._deny = (id) => { socket.emit('deny_action', { action_id: id }); };

// ─── Start ──────────────────────────────────────────────────────

init();
