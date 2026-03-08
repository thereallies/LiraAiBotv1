const boot = window.LIRA_WEB_BOOT || {};

const byId = (id) => document.getElementById(id);
const views = {
  dashboard: byId("view-dashboard"),
  chat: byId("view-chat"),
  image: byId("view-image"),
  vision: byId("view-vision"),
  voice: byId("view-voice"),
  admin: byId("view-admin"),
};

const state = {
  currentSessionId: null,
  sessions: [],
  sessionsSupported: true,
  fallbackMessages: [],
  currentMessages: [],
};

function showToast(message, tone = "info", title = "") {
  const root = byId("toast-stack");
  if (!root || !message) return;

  const toast = document.createElement("div");
  toast.className = `toast ${tone}`.trim();
  toast.innerHTML = `
    ${title ? `<strong>${escapeHtml(title)}</strong>` : ""}
    <div>${escapeHtml(message)}</div>
  `;
  root.appendChild(toast);

  window.setTimeout(() => toast.classList.add("visible"), 10);
  window.setTimeout(() => {
    toast.classList.remove("visible");
    window.setTimeout(() => toast.remove(), 220);
  }, 4200);
}

const sidebar = document.querySelector(".sidebar");
const sidebarToggle = byId("sidebar-toggle");
const chatInput = byId("chat-input");
const chatFeed = byId("chat-feed");
const chatCanvas = byId("chat-canvas");
const chatMainPanel = byId("chat-main-panel");
const chatLayout = byId("chat-layout");
const chatHistoryPanel = byId("chat-history-panel");
const chatStatus = byId("chat-status");
const topTitle = byId("view-title");
const chatModel = byId("chat-model");
const assistantMode = byId("assistant-mode");
const newChatBtn = byId("new-chat-btn");
const chatSubmitBtn = byId("chat-submit-btn");
const historyToggleBtn = byId("history-toggle-btn");

function escapeForAttribute(value) {
  return escapeHtml(value).replaceAll("\n", "&#10;");
}

function setView(name) {
  Object.entries(views).forEach(([key, node]) => {
    if (!node) return;
    node.classList.toggle("active", key === name);
  });

  document.querySelectorAll("[data-view]").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.view === name);
  });

  document.querySelectorAll(".mobile-tab").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.view === name);
  });

  const titleMap = {
    dashboard: "Рабочая зона",
    chat: "AI-чат",
    image: "Генерация изображений",
    vision: "Анализ фото",
    voice: "Голосовые инструменты",
    admin: "Управление продуктом",
  };
  if (topTitle) topTitle.textContent = titleMap[name] || "LiraAI Web";

  if (name === "chat") {
    loadChatSessions().catch(console.error);
  }

  if (window.innerWidth <= 1100) {
    sidebar?.classList.remove("open");
  }
}

function setHistoryOpen(open) {
  if (!chatLayout) return;
  chatLayout.classList.toggle("history-open", open);
  historyToggleBtn?.classList.toggle("active", open);
  historyToggleBtn?.setAttribute("aria-expanded", open ? "true" : "false");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatDate(value) {
  if (!value) return "без даты";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getSessionBucket(value) {
  const now = new Date();
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Ранее";

  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startOfItemDay = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const diffDays = Math.floor((startOfToday - startOfItemDay) / 86400000);

  if (diffDays <= 0) return "Сегодня";
  if (diffDays <= 7) return "7 дней";
  return "Ранее";
}

async function api(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(data.detail || response.statusText || "API error");
    error.status = response.status;
    throw error;
  }
  return data;
}

async function loadNotifications() {
  try {
    const data = await api("/api/web/notifications");
    (data.notifications || []).forEach((item) => {
      showToast(item.message, item.tone || "info", item.title || "");
    });
  } catch (error) {
    if (error.status !== 401) {
      console.error(error);
    }
  }
}

function setChatStatus(message = "", tone = "") {
  if (!chatStatus) return;
  if (!message) {
    chatStatus.textContent = "";
    chatStatus.className = "chat-status hidden";
    return;
  }
  chatStatus.textContent = message;
  chatStatus.className = `chat-status ${tone}`.trim();
}

function setButtonLoading(button, loading, loadingText = "") {
  if (!button) return;
  if (loading) {
    if (!button.dataset.originalText) {
      button.dataset.originalText = button.textContent;
    }
    button.disabled = true;
    button.classList.add("is-loading");
    if (loadingText) button.textContent = loadingText;
    return;
  }

  button.disabled = false;
  button.classList.remove("is-loading");
  if (button.dataset.originalText) {
    button.textContent = button.dataset.originalText;
  }
}

function renderChatFeed(messages = []) {
  if (!chatFeed) return;
  if (!messages.length) {
    state.currentMessages = [];
    chatCanvas?.classList.add("is-empty");
    chatMainPanel?.classList.add("is-empty-view");
    chatLayout?.classList.remove("is-empty-view");
    chatHistoryPanel?.classList.remove("is-hidden");
    chatFeed.innerHTML = `
      <div class="chat-empty-state">
        <div class="chat-empty-mark">L</div>
        <strong>Новый чат</strong>
        <p>Напиши сообщение ниже или открой историю справа.</p>
      </div>
    `;
    return;
  }

  chatCanvas?.classList.remove("is-empty");
  chatMainPanel?.classList.remove("is-empty-view");
  chatLayout?.classList.remove("is-empty-view");
  chatHistoryPanel?.classList.remove("is-hidden");
  state.currentMessages = [...messages];
  chatFeed.innerHTML = messages.map((item) => `
    <div class="chat-row ${item.role === "user" ? "user" : "bot"} ${item.pending ? "pending" : ""}">
      <div class="chat-bubble ${item.role === "user" ? "user" : "bot"} ${item.pending ? "pending" : ""}">
        <strong>${item.role === "user" ? "Ты" : escapeHtml(item.model || "LiraAI")}</strong>
        <div class="chat-bubble-content">${item.pending
          ? `<span class="typing-label">Уже спешу ответить вам</span><span class="typing-dots"><i></i><i></i><i></i></span>`
          : escapeHtml(item.content || "").replaceAll("\n", "<br>")}</div>
        ${item.role === "assistant" && !item.pending && item.content
          ? `<button class="copy-answer-btn" type="button" data-copy-text="${escapeForAttribute(item.content)}">Копировать</button>`
          : ""}
      </div>
    </div>
  `).join("");
  chatFeed.scrollTop = chatFeed.scrollHeight;
}

function renderRecentMessages(items = []) {
  const root = byId("recent-messages");
  if (!root) return;
  if (!items.length) {
    root.innerHTML = `<div class="stack-item"><strong>История пока пустая</strong><small>После первых сообщений здесь появятся последние ответы и запросы.</small></div>`;
    return;
  }
  root.innerHTML = items.map((item) => `
    <div class="stack-item compact">
      <strong>${item.role === "assistant" ? "LiraAI" : "Ты"}</strong>
      <div>${escapeHtml(item.content || "")}</div>
      <small>${escapeHtml(item.model || "без модели")} · ${formatDate(item.created_at)}</small>
    </div>
  `).join("");
}

function renderChatSessions(sessions = []) {
  const root = byId("chat-sessions");
  if (!root) return;
  if (!sessions.length) {
    root.innerHTML = state.sessionsSupported
      ? `<div class="stack-item compact"><strong>Чатов пока нет</strong><small>Нажми New chat и начни новый диалог.</small></div>`
      : `<div class="stack-item compact subtle"><strong>История временно недоступна</strong><small>Текущий backend ещё без chat sessions. Обычный чат продолжит работать.</small></div>`;
    return;
  }

  const groups = {};
  sessions.forEach((session) => {
    const bucket = getSessionBucket(session.updated_at || session.created_at);
    if (!groups[bucket]) groups[bucket] = [];
    groups[bucket].push(session);
  });

  const order = ["Сегодня", "7 дней", "Ранее"];
  root.innerHTML = order
    .filter((bucket) => groups[bucket]?.length)
    .map((bucket) => `
      <div class="session-group">
        <div class="session-group-title">${bucket}</div>
        ${groups[bucket].map((session) => `
          <div class="session-card ${session.session_id === state.currentSessionId ? "active" : ""}">
            <button
              class="session-item ${session.session_id === state.currentSessionId ? "active" : ""}"
              type="button"
              data-session-id="${session.session_id}">
              <strong>${escapeHtml(session.title || "Новый чат")}</strong>
              <small>${escapeHtml(session.preview || session.assistant_mode || "Новый диалог")}</small>
            </button>
            <button
              class="session-delete-btn"
              type="button"
              data-delete-session-id="${session.session_id}"
              aria-label="Удалить чат">×</button>
          </div>
        `).join("")}
      </div>
    `).join("");
}

async function deleteChatSession(sessionId) {
  try {
    let data;
    try {
      data = await api(`/api/web/chat/sessions/${sessionId}`, { method: "DELETE" });
    } catch (error) {
      if (error.status !== 405) {
        throw error;
      }
      data = await api(`/api/web/chat/sessions/${sessionId}/delete`, { method: "POST" });
    }
    state.sessions = data.sessions || [];

    if (state.currentSessionId === sessionId) {
      state.currentSessionId = data.next_session_id || null;
      if (state.currentSessionId) {
        await openChatSession(state.currentSessionId);
      } else {
        state.currentMessages = [];
        state.fallbackMessages = [];
        renderChatFeed([]);
        renderChatSessions(state.sessions);
      }
    } else {
      renderChatSessions(state.sessions);
    }

    showToast("Чат удалён.", "success");
    setChatStatus("Чат удалён.", "success");
  } catch (error) {
    showToast(error.message, "error", "Удаление чата");
    setChatStatus(`Не удалось удалить чат: ${error.message}`, "error");
  }
}

function renderChart(rootId, items, secondary = false) {
  const root = byId(rootId);
  if (!root) return;
  if (!items.length) {
    root.innerHTML = `<div class="stack-item"><strong>Нет данных</strong><small>График появится, когда накопится активность.</small></div>`;
    return;
  }
  const max = Math.max(...items.map((item) => item.count ?? item.users ?? 0), 1);
  root.innerHTML = `
    <div class="chart">
      ${items.map((item) => {
        const value = item.count ?? item.users ?? 0;
        const height = Math.max(18, Math.round((value / max) * 180));
        return `
          <div class="bar-group">
            <div class="bar-value">${value}</div>
            <div class="bar ${secondary ? "secondary" : ""}" style="height:${height}px"></div>
            <div class="bar-label">${item.label}</div>
          </div>
        `;
      }).join("")}
    </div>
  `;
}

function renderAdminUsers(users = []) {
  const root = byId("admin-users");
  if (!root) return;
  if (!users.length) {
    root.innerHTML = `<div class="stack-item"><strong>Пользователей пока нет</strong></div>`;
    return;
  }
  root.innerHTML = users.map((user) => `
    <div class="user-row">
      <div>
        <strong>${escapeHtml(user.first_name || user.username || user.user_id)} ${user.is_banned ? "❌" : ""}</strong>
        <div class="user-meta">
          <span>@${escapeHtml(user.username || "без username")}</span>
          <span>${user.user_id}</span>
          <span>${escapeHtml(user.access_level || "user")}</span>
          <span>сегодня: ${user.today_generations || 0}</span>
          <span>всего: ${user.total_count || 0}</span>
        </div>
      </div>
      <div class="user-actions">
        <button class="mini-btn" type="button" data-action="level" data-level="user" data-user-id="${user.user_id}">user</button>
        <button class="mini-btn" type="button" data-action="level" data-level="subscriber" data-user-id="${user.user_id}">subscriber</button>
        <button class="mini-btn" type="button" data-action="level" data-level="sub+" data-user-id="${user.user_id}">sub+</button>
        ${user.is_banned
          ? `<button class="mini-btn" type="button" data-action="unban" data-user-id="${user.user_id}">разбанить</button>`
          : `<button class="mini-btn danger" type="button" data-action="ban" data-user-id="${user.user_id}">бан</button>`}
      </div>
    </div>
  `).join("");
}

function renderAudit(logs = []) {
  const root = byId("audit-log");
  if (!root) return;
  if (!logs.length) {
    root.innerHTML = `<div class="stack-item"><strong>Audit log пуст</strong></div>`;
    return;
  }
  root.innerHTML = logs.map((item) => `
    <div class="stack-item compact">
      <strong>${escapeHtml(item.action_type || "action")}</strong>
      <div>${escapeHtml(item.admin_username || item.admin_user_id || "admin")} → ${escapeHtml(item.target_user_id || "system")}</div>
      <small>${formatDate(item.created_at)}</small>
    </div>
  `).join("");
}

async function loadDashboard() {
  const data = await api("/api/web/dashboard/summary");
  byId("metric-today").textContent = data.limits.today_generations;
  byId("metric-total").textContent = data.limits.total_generations;
  byId("metric-messages").textContent = data.limits.messages_today;
  byId("metric-limit").textContent = data.limits.daily_limit;
  renderRecentMessages(data.recent_messages);
}

async function loadAdmin() {
  if (!boot.isAdmin) return;
  const overview = await api("/api/web/admin/overview");
  byId("admin-total-users").textContent = overview.summary.total_users;
  byId("admin-active-users").textContent = overview.summary.active_today;
  byId("admin-banned-users").textContent = overview.summary.banned_users;
  byId("admin-pending-payments").textContent = overview.summary.pending_payments;
  renderChart("activity-chart", overview.activity_chart);
  renderChart("generation-chart", overview.generation_chart, true);
  renderAudit(overview.recent_audit);

  const users = await api("/api/web/admin/users");
  renderAdminUsers(users.users);
}

async function loadChatSessions(selectSession = true) {
  try {
    const data = await api("/api/web/chat/sessions");
    state.sessionsSupported = true;
    state.sessions = data.sessions || [];
    renderChatSessions(state.sessions);
    if (selectSession && !state.currentSessionId && state.sessions.length) {
      await openChatSession(state.sessions[0].session_id);
    }
    setChatStatus("");
  } catch (error) {
    if (error.status === 404) {
      state.sessionsSupported = false;
      state.sessions = [];
      renderChatSessions([]);
      setChatStatus("");
      return;
    }
    setChatStatus(`Не удалось загрузить список чатов: ${error.message}`, "error");
    throw error;
  }
}

async function openChatSession(sessionId) {
  if (!state.sessionsSupported) {
    state.currentSessionId = null;
    renderChatFeed(state.fallbackMessages);
    setChatStatus("");
    return;
  }

  try {
    const data = await api(`/api/web/chat/sessions/${sessionId}`);
    state.currentSessionId = sessionId;
    renderChatSessions(state.sessions);
    renderChatFeed(data.messages || []);
    if (data.session) {
      if (chatModel) chatModel.value = data.session.model_key || "groq-gpt-oss";
      if (assistantMode) assistantMode.value = data.session.assistant_mode || "assistant";
    }
    setChatStatus("");
  } catch (error) {
    if (error.status === 404) {
      state.sessionsSupported = false;
      state.currentSessionId = null;
      renderChatFeed([]);
      renderChatSessions([]);
      setChatStatus("");
      return;
    }
    setChatStatus(`Не удалось открыть чат: ${error.message}`, "error");
    throw error;
  }
}

async function createNewChat() {
  if (!state.sessionsSupported) {
    state.currentSessionId = null;
    state.fallbackMessages = [];
    state.currentMessages = [];
    renderChatFeed(state.fallbackMessages);
    setChatStatus("Новый чат создан локально. История чатов появится после обновления backend.", "success");
    showToast("Новый локальный чат создан.", "success");
    return;
  }

  try {
    setChatStatus("Создаю новый чат...");
    setButtonLoading(newChatBtn, true, "Создаю...");
    const data = await api("/api/web/chat/sessions", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        model_key: chatModel?.value || "groq-gpt-oss",
        assistant_mode: assistantMode?.value || "assistant",
      }),
    });
    if (data.session) {
      state.currentSessionId = data.session.session_id;
      state.fallbackMessages = [];
      state.currentMessages = [];
      await loadChatSessions(false);
      renderChatFeed([]);
      renderChatSessions(state.sessions);
      setChatStatus("Новый чат создан.", "success");
      showToast("Новый чат создан.", "success");
    }
  } catch (error) {
    if (error.status === 404) {
      state.sessionsSupported = false;
      state.currentSessionId = null;
      state.sessions = [];
      state.fallbackMessages = [];
      state.currentMessages = [];
      renderChatFeed(state.fallbackMessages);
      renderChatSessions([]);
      setChatStatus("Backend ещё без chat sessions. Переключила чат в базовый режим.", "success");
      showToast("История чатов временно недоступна. Работает базовый режим.", "info");
      return;
    }
    setChatStatus(`Не удалось создать чат: ${error.message}`, "error");
    throw error;
  } finally {
    setButtonLoading(newChatBtn, false);
  }
}

async function submitChat(event) {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  try {
    setChatStatus("Уже спешу ответить вам...", "success");
    setButtonLoading(chatSubmitBtn, true, "Отправка...");
    if (state.sessionsSupported && !state.currentSessionId) {
      await createNewChat();
    }

    const pendingMessages = [
      ...state.currentMessages,
      { role: "user", content: message, model: "Ты" },
      { role: "assistant", content: "", model: chatModel?.selectedOptions?.[0]?.textContent || "LiraAI", pending: true },
    ];
    renderChatFeed(pendingMessages);

    const data = await api("/api/web/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        message,
        model_key: chatModel?.value || "groq-gpt-oss",
        session_id: state.sessionsSupported ? state.currentSessionId : null,
        assistant_mode: assistantMode?.value || "assistant",
      }),
    });

    chatInput.value = "";
    if (data.session_id) {
      state.currentSessionId = data.session_id;
    }

    if (Array.isArray(data.messages) && data.messages.length) {
      state.fallbackMessages = [];
      renderChatFeed(data.messages);
      if (state.sessionsSupported) {
        await loadChatSessions(false);
        renderChatSessions(state.sessions);
      }
    } else {
      state.fallbackMessages = [
        ...state.currentMessages,
        { role: "user", content: message, model: "Ты" },
        { role: "assistant", content: data.answer || "", model: data.model || "LiraAI" },
      ];
      renderChatFeed(state.fallbackMessages);
    }

    setChatStatus("");
    loadDashboard().catch(() => {});
  } catch (error) {
    setChatStatus(`Не удалось отправить сообщение: ${error.message}`, "error");
  } finally {
    setButtonLoading(chatSubmitBtn, false);
  }
}

async function copyAnswer(text) {
  if (!text) return;

  try {
    await navigator.clipboard.writeText(text);
    showToast("Ответ скопирован.", "success");
  } catch (error) {
    showToast("Не удалось скопировать ответ.", "error");
  }
}

async function submitImage(event) {
  event.preventDefault();
  const prompt = byId("image-prompt").value.trim();
  const box = byId("image-result");
  if (!prompt) return;
  box.classList.remove("empty");
  box.innerHTML = "Генерирую изображение...";
  try {
    const data = await api("/api/web/image/generate", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message: prompt}),
    });
    box.innerHTML = `<img src="data:${data.mime_type};base64,${data.image_base64}" alt="Generated image">`;
    showToast("Изображение готово.", "success");
    loadDashboard().catch(() => {});
  } catch (error) {
    box.textContent = `Ошибка генерации: ${error.message}`;
    showToast(error.message, "error", "Ошибка генерации");
  }
}

async function submitUpload(event, inputId, endpoint, outputId, key) {
  event.preventDefault();
  const fileInput = byId(inputId);
  const output = byId(outputId);
  const file = fileInput.files[0];
  if (!file) return;
  output.classList.remove("empty");
  output.textContent = "Обрабатываю файл...";
  const form = new FormData();
  form.append("file", file);
  try {
    const response = await fetch(endpoint, {method: "POST", body: form});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Ошибка обработки");
    output.textContent = data[key];
    showToast("Файл обработан.", "success");
  } catch (error) {
    output.textContent = `Ошибка: ${error.message}`;
    showToast(error.message, "error", "Ошибка обработки");
  }
}

async function logout() {
  await api("/api/web/auth/logout", {method: "POST"});
  window.location.href = "/web";
}

async function handleAdminActions(event) {
  const button = event.target.closest("[data-action]");
  if (!button) return;
  const userId = button.dataset.userId;
  const action = button.dataset.action;
  try {
    if (action === "level") {
      const result = await api(`/api/web/admin/users/${userId}/level`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({access_level: button.dataset.level}),
      });
      showToast(result.message || "Изменение применено.", "success", "Уровень обновлён");
    } else if (action === "ban") {
      const days = prompt("Бан на сколько дней? Оставь пустым для 7 дней.");
      const result = await api(`/api/web/admin/users/${userId}/ban`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({days: days ? Number(days) : 7, permanent: false}),
      });
      showToast(result.message || "Пользователь заблокирован.", "success", "Бан применён");
    } else if (action === "unban") {
      const result = await api(`/api/web/admin/users/${userId}/unban`, {method: "POST"});
      showToast(result.message || "Пользователь разблокирован.", "success", "Блокировка снята");
    }
    await loadAdmin();
  } catch (error) {
    showToast(error.message, "error", "Админ-действие");
  }
}

document.querySelectorAll("[data-view]").forEach((button) => {
  button.addEventListener("click", () => setView(button.dataset.view));
});

document.querySelectorAll("[data-view-jump]").forEach((button) => {
  button.addEventListener("click", () => setView(button.dataset.viewJump));
});

byId("chat-sessions")?.addEventListener("click", async (event) => {
  const deleteBtn = event.target.closest("[data-delete-session-id]");
  if (deleteBtn) {
    event.stopPropagation();
    await deleteChatSession(deleteBtn.dataset.deleteSessionId);
    return;
  }
  const button = event.target.closest("[data-session-id]");
  if (!button) return;
  await openChatSession(button.dataset.sessionId);
  if (window.innerWidth <= 1500) {
    setHistoryOpen(false);
  }
});

chatFeed?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-copy-text]");
  if (!button) return;
  copyAnswer(button.dataset.copyText);
});

historyToggleBtn?.addEventListener("click", () => {
  setHistoryOpen(!chatLayout?.classList.contains("history-open"));
});

byId("new-chat-btn")?.addEventListener("click", () => {
  createNewChat().catch(console.error);
});

chatInput?.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" || event.shiftKey || event.isComposing) return;
  event.preventDefault();
  byId("chat-form")?.requestSubmit();
});

sidebarToggle?.addEventListener("click", () => {
  sidebar?.classList.toggle("open");
});

document.addEventListener("click", (event) => {
  if (window.innerWidth > 1100) return;
  if (!sidebar?.classList.contains("open")) return;
  if (sidebar.contains(event.target) || sidebarToggle?.contains(event.target)) return;
  sidebar.classList.remove("open");
});

document.addEventListener("click", (event) => {
  if (window.innerWidth > 1500) return;
  if (!chatLayout?.classList.contains("history-open")) return;
  if (chatHistoryPanel?.contains(event.target) || historyToggleBtn?.contains(event.target)) return;
  setHistoryOpen(false);
});

window.addEventListener("resize", () => {
  if (window.innerWidth > 1500) {
    setHistoryOpen(false);
  }
});

byId("chat-form")?.addEventListener("submit", submitChat);
byId("image-form")?.addEventListener("submit", submitImage);
byId("vision-form")?.addEventListener("submit", (event) => submitUpload(event, "vision-file", "/api/web/vision/analyze", "vision-result", "description"));
byId("voice-form")?.addEventListener("submit", (event) => submitUpload(event, "voice-file", "/api/web/voice/transcribe", "voice-result", "text"));
byId("logout-btn")?.addEventListener("click", logout);
byId("admin-users")?.addEventListener("click", handleAdminActions);

setView("chat");
loadDashboard().catch(console.error);
loadAdmin().catch(console.error);
loadChatSessions().catch(console.error);
loadNotifications().catch(console.error);
window.setInterval(() => {
  loadNotifications().catch(() => {});
}, 15000);
