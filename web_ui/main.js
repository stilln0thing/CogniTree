/* main.js — WebSocket client, chat UI, tool call rendering */

'use strict';

// ── Config ──────────────────────────────────────────────────────────────────
const WS_URL      = `ws://${window.location.hostname || 'localhost'}:8765/ws`;
const THREAD_ID   = 'default';
const RECONNECT_DELAY_MS = 3000;

// ── DOM refs ─────────────────────────────────────────────────────────────────
const landingPage     = document.getElementById('landing-page');
const chatPage        = document.getElementById('chat-page');
const startConvoBtn   = document.getElementById('start-convo-btn');
const backToHomeBtn   = document.getElementById('back-to-home-btn');
const toggleSidebarBtn = document.getElementById('toggle-sidebar-btn');
const toggleCanvasBtn  = document.getElementById('toggle-canvas-btn');
const closeCanvasBtn   = document.getElementById('close-canvas-btn');
const newThreadBtn     = document.getElementById('new-thread-btn');
const sidebar          = document.getElementById('sidebar');
const canvasPanel      = document.getElementById('canvas-panel');
const messageStream    = document.getElementById('message-stream');
const greeting         = document.getElementById('greeting');
const promptInput      = document.getElementById('prompt-input');
const sendBtn          = document.getElementById('send-btn');
const connectionToast  = document.getElementById('connection-toast');
const toastText        = document.getElementById('toast-text');
const canvasEmpty      = document.getElementById('canvas-empty');

// ── State ─────────────────────────────────────────────────────────────────────
let socket              = null;
let isConnected         = false;
let currentAssistantEl  = null;   // The .msg-bubble div being streamed into
let currentToolCards    = {};     // keyed by tool name, value is {card, bodyEl, statusEl}
let greetingVisible     = true;

// ── Navigation ────────────────────────────────────────────────────────────────
function showChat() {
  landingPage.classList.remove('active');
  landingPage.style.display = 'none';
  chatPage.classList.add('active');
  chatPage.style.display = 'flex';
  initWebSocket();
}

function showLanding() {
  chatPage.classList.remove('active');
  chatPage.style.display = 'none';
  landingPage.style.display = 'block';
  landingPage.classList.add('active');
}

startConvoBtn.addEventListener('click', showChat);
backToHomeBtn.addEventListener('click', showLanding);

// ── Sidebar & Canvas toggles ──────────────────────────────────────────────────
toggleSidebarBtn.addEventListener('click', () => sidebar.classList.toggle('collapsed'));

function openCanvas() {
  canvasPanel.classList.remove('collapsed');
}

function closeCanvas() {
  canvasPanel.classList.add('collapsed');
}

toggleCanvasBtn.addEventListener('click', openCanvas);
closeCanvasBtn.addEventListener('click', closeCanvas);

// ── New Thread ────────────────────────────────────────────────────────────────
newThreadBtn.addEventListener('click', resetChat);

function resetChat() {
  messageStream.innerHTML = '';
  messageStream.appendChild(greeting);
  greeting.style.display = '';
  greetingVisible = true;
  currentAssistantEl = null;
  currentToolCards = {};
  if (window.treeCanvas) window.treeCanvas.reset();
  if (canvasEmpty) canvasEmpty.style.display = '';
}

// ── Suggestion buttons ────────────────────────────────────────────────────────
document.querySelectorAll('.suggestion-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const prompt = btn.getAttribute('data-prompt');
    if (prompt) {
      promptInput.value = prompt;
      updateSendBtn();
      sendMessage();
    }
  });
});

// ── Input auto-resize & send button state ─────────────────────────────────────
promptInput.addEventListener('input', () => {
  promptInput.style.height = 'auto';
  promptInput.style.height = Math.min(promptInput.scrollHeight, 200) + 'px';
  updateSendBtn();
});

promptInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

sendBtn.addEventListener('click', sendMessage);

function updateSendBtn() {
  sendBtn.disabled = promptInput.value.trim() === '' || !isConnected;
}

// ── Toast ─────────────────────────────────────────────────────────────────────
function showToast(text, state = 'default', duration = 3000) {
  toastText.textContent = text;
  connectionToast.className = `connection-toast show ${state}`;
  if (duration > 0) {
    setTimeout(() => {
      connectionToast.classList.remove('show');
    }, duration);
  }
}

// ── WebSocket ─────────────────────────────────────────────────────────────────
function initWebSocket() {
  if (socket && socket.readyState === WebSocket.OPEN) return;

  showToast('Connecting to server...', 'default', 0);

  socket = new WebSocket(WS_URL);

  socket.onopen = () => {
    isConnected = true;
    updateSendBtn();
    showToast('Connected to CogniTree', 'connected', 2500);
    console.log('[CogniTree] WebSocket connected.');
  };

  socket.onmessage = (event) => {
    try {
      handleServerMessage(JSON.parse(event.data));
    } catch (err) {
      console.warn('[CogniTree] Message parse error:', err);
    }
  };

  socket.onclose = () => {
    isConnected = false;
    updateSendBtn();
    showToast('Disconnected — reconnecting...', 'error', 0);
    console.warn('[CogniTree] WebSocket closed. Reconnecting in', RECONNECT_DELAY_MS, 'ms...');
    setTimeout(initWebSocket, RECONNECT_DELAY_MS);
  };

  socket.onerror = (err) => {
    console.error('[CogniTree] WebSocket error:', err);
  };
}

// ── Message handling ──────────────────────────────────────────────────────────
function handleServerMessage(data) {
  switch (data.type) {
    case 'token':
      onToken(data.content || '');
      break;

    case 'tool_start':
      // payload: { name, args }
      onToolStart(data.payload || {});
      break;

    case 'tool_done':
      // payload: { name, result }
      onToolEnd(data.payload || {});
      break;

    case 'done':
      onDone();
      break;

    case 'error':
      onError(data.message || (typeof data.payload === 'string' ? data.payload : JSON.stringify(data.payload)) || 'Unknown error');
      break;

    default:
      console.log('[CogniTree] Unhandled message type:', data.type, data);
  }
}

function onToken(text) {
  ensureAssistantBubble();
  // Append token text to current bubble
  currentAssistantEl.textContent += text;
  scrollToBottom();
}

function onToolStart(payload) {
  const toolName  = payload.name || 'unknown_tool';
  // Backend sends `args` for tool input
  const toolInput = payload.args ? JSON.stringify(payload.args, null, 2) : '';

  ensureAssistantBubble();

  const card = buildToolCard(toolName, toolInput, 'running');
  currentAssistantEl.parentElement.appendChild(card.el);

  currentToolCards[toolName] = card;
  scrollToBottom();
}

function onToolEnd(payload) {
  const toolName = payload.name || 'unknown_tool';
  // Backend sends `result` for tool output
  const output   = payload.result ?? payload.output ?? '';
  const isError  = payload.error === true;

  const card = currentToolCards[toolName];
  if (card) {
    card.statusEl.textContent = isError ? 'error' : 'done';
    card.statusEl.className   = `tool-card-status ${isError ? 'error' : 'done'}`;
    if (output) {
      card.bodyEl.textContent = typeof output === 'string' ? output : JSON.stringify(output, null, 2);
    }
    delete currentToolCards[toolName];
  }
  scrollToBottom();
}

function onDone() {
  currentAssistantEl = null;
  scrollToBottom();
}

function onError(message) {
  ensureAssistantBubble();
  const errEl = document.createElement('div');
  errEl.style.cssText = 'margin-top:.5rem;padding:.5rem .75rem;border-radius:8px;background:rgba(248,113,113,.1);border:1px solid rgba(248,113,113,.25);color:#f87171;font-size:.8125rem;font-family:var(--font-mono)';
  errEl.textContent = `Error: ${message}`;
  currentAssistantEl.parentElement.appendChild(errEl);
  currentAssistantEl = null;
  scrollToBottom();
}

// ── DOM helpers ───────────────────────────────────────────────────────────────
function ensureAssistantBubble() {
  if (currentAssistantEl) return;
  hideGreeting();

  const group = document.createElement('div');
  group.className = 'msg-group';

  const row = document.createElement('div');
  row.className = 'msg-row assistant';

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar assistant';
  avatar.textContent = 'CT';

  const body = document.createElement('div');
  body.className = 'msg-body';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';

  // Show thinking dots initially
  const thinking = document.createElement('div');
  thinking.className = 'msg-thinking';
  thinking.innerHTML = '<span></span><span></span><span></span>';
  bubble.appendChild(thinking);

  body.appendChild(bubble);
  row.appendChild(avatar);
  row.appendChild(body);
  group.appendChild(row);
  messageStream.appendChild(group);

  // Once text starts flowing, remove the thinking dots
  const originalAppend = bubble.textContent;
  bubble.textContent = '';
  thinking.remove();

  currentAssistantEl = bubble;
  scrollToBottom();
}

function buildToolCard(toolName, inputText, initialStatus) {
  const card = document.createElement('div');
  card.className = 'tool-card';

  const header = document.createElement('div');
  header.className = 'tool-card-header';

  header.innerHTML = `
    <svg class="tool-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
    </svg>
  `;

  const nameEl = document.createElement('span');
  nameEl.className = 'tool-card-name';
  nameEl.textContent = toolName;

  const statusEl = document.createElement('span');
  statusEl.className = `tool-card-status ${initialStatus}`;
  statusEl.textContent = initialStatus;

  const toggleEl = document.createElement('svg');
  toggleEl.className = 'tool-card-toggle';
  toggleEl.setAttribute('width', '14');
  toggleEl.setAttribute('height', '14');
  toggleEl.setAttribute('viewBox', '0 0 24 24');
  toggleEl.setAttribute('fill', 'none');
  toggleEl.setAttribute('stroke', 'currentColor');
  toggleEl.setAttribute('stroke-width', '2');
  toggleEl.innerHTML = '<polyline points="6 9 12 15 18 9"/>';

  header.appendChild(nameEl);
  header.appendChild(statusEl);
  header.appendChild(toggleEl);

  const body = document.createElement('div');
  body.className = 'tool-card-body';
  if (inputText) body.textContent = inputText;

  header.addEventListener('click', () => card.classList.toggle('expanded'));

  card.appendChild(header);
  card.appendChild(body);

  return { el: card, bodyEl: body, statusEl };
}

function hideGreeting() {
  if (greetingVisible) {
    greeting.style.display = 'none';
    greetingVisible = false;
  }
}

function appendUserMessage(text) {
  hideGreeting();

  const group = document.createElement('div');
  group.className = 'msg-group';

  const row = document.createElement('div');
  row.className = 'msg-row user';

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar user';
  avatar.textContent = 'U';

  const body = document.createElement('div');
  body.className = 'msg-body';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.textContent = text;

  body.appendChild(bubble);
  row.appendChild(avatar);
  row.appendChild(body);
  group.appendChild(row);
  messageStream.appendChild(group);
}

function scrollToBottom() {
  messageStream.scrollTop = messageStream.scrollHeight;
}

// ── Send message ──────────────────────────────────────────────────────────────
function sendMessage() {
  const text = promptInput.value.trim();
  if (!text || !isConnected) return;

  appendUserMessage(text);

  // Add node to decision tree canvas
  if (window.treeCanvas) {
    window.treeCanvas.addNode(Date.now().toString(), text);
    if (canvasEmpty) canvasEmpty.style.display = 'none';
  }

  currentAssistantEl = null;

  socket.send(JSON.stringify({
    type:      'chat',
    prompt:    text,
    thread_id: THREAD_ID,
  }));

  promptInput.value = '';
  promptInput.style.height = 'auto';
  updateSendBtn();
  scrollToBottom();
}

// ── Time-travel node click callback (called by tree.js) ──────────────────────
window.onNodeSelect = (node) => {
  const group = document.createElement('div');
  group.className = 'msg-group';

  const row = document.createElement('div');
  row.className = 'msg-row assistant';

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar assistant';
  avatar.textContent = 'CT';

  const body = document.createElement('div');
  body.className = 'msg-body';

  const ttCard = document.createElement('div');
  ttCard.className = 'timetravel-card';
  ttCard.innerHTML = `<strong>Time-traveled</strong> to checkpoint: "${node.label}"<br><span style="opacity:.7;font-size:.75rem">State snapshot restored. You can now branch from this point.</span>`;

  body.appendChild(ttCard);
  row.appendChild(avatar);
  row.appendChild(body);
  group.appendChild(row);
  messageStream.appendChild(group);
  scrollToBottom();
};

// ── Init ──────────────────────────────────────────────────────────────────────
updateSendBtn();
