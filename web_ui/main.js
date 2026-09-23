/* main.js — Client UI logic, WebSocket connection & Decision Tree integration */

const wsUrl = `ws://${window.location.hostname || 'localhost'}:8765/ws`;
let socket = null;
let currentAssistantContentEl = null;

const chatMessages = document.getElementById('chat-messages');
const promptInput = document.getElementById('prompt-input');
const sendButton = document.getElementById('send-button');
const btnTogglePanel = document.getElementById('btn-toggle-panel');
const navToggleTree = document.getElementById('nav-toggle-tree');
const navNewThread = document.getElementById('nav-new-thread');
const treePane = document.getElementById('tree-pane');

function initWebSocket() {
  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log(" Connected to CogniTree FastAPI WebSocket!");
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);

      if (data.type === 'token') {
        if (!currentAssistantContentEl) {
          createAssistantMessageBubble();
        }
        currentAssistantContentEl.innerText += data.content;
        chatMessages.scrollTop = chatMessages.scrollHeight;
      } else if (data.type === 'tool_start') {
        if (!currentAssistantContentEl) {
          createAssistantMessageBubble();
        }
        currentAssistantContentEl.innerText += `\n\n🛠️ [Executing tool: ${data.payload.name}...]\n\n`;
        chatMessages.scrollTop = chatMessages.scrollHeight;
      } else if (data.type === 'done') {
        currentAssistantContentEl = null;
      } else if (data.type === 'error') {
        if (!currentAssistantContentEl) {
          createAssistantMessageBubble();
        }
        currentAssistantContentEl.innerText += `\n⚠️ Error: ${data.message || data.payload}`;
        currentAssistantContentEl = null;
      }
    } catch (err) {
      console.warn("WebSocket message parse error:", err);
    }
  };

  socket.onclose = () => {
    setTimeout(initWebSocket, 3000);
  };
}

function createAssistantMessageBubble() {
  const wrapper = document.createElement('div');
  wrapper.className = 'message-wrapper assistant';

  const avatar = document.createElement('div');
  avatar.className = 'avatar assistant';
  avatar.innerText = 'CT';

  const content = document.createElement('div');
  content.className = 'message-content';

  wrapper.appendChild(avatar);
  wrapper.appendChild(content);
  chatMessages.appendChild(wrapper);

  currentAssistantContentEl = content;
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function sendMessage() {
  const text = promptInput.value.trim();
  if (!text || !socket) return;

  // Render User Message Bubble
  const wrapper = document.createElement('div');
  wrapper.className = 'message-wrapper user';

  const avatar = document.createElement('div');
  avatar.className = 'avatar user';
  avatar.innerText = 'U';

  const content = document.createElement('div');
  content.className = 'message-content';
  content.innerText = text;

  wrapper.appendChild(avatar);
  wrapper.appendChild(content);
  chatMessages.appendChild(wrapper);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  // Add node to decision tree
  if (window.treeCanvas) {
    window.treeCanvas.addNode(Date.now().toString(), text);
  }

  // Reset assistant content element pointer
  currentAssistantContentEl = null;

  // Send payload over WebSocket
  socket.send(JSON.stringify({ type: 'chat', prompt: text, thread_id: 'default' }));
  promptInput.value = '';
}

sendButton.addEventListener('click', sendMessage);
promptInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

btnTogglePanel.addEventListener('click', () => treePane.classList.toggle('collapsed'));
if (navToggleTree) {
  navToggleTree.addEventListener('click', () => treePane.classList.toggle('collapsed'));
}

if (navNewThread) {
  navNewThread.addEventListener('click', () => {
    chatMessages.innerHTML = '';
    createAssistantMessageBubble();
    currentAssistantContentEl.innerText = "Started new conversation thread.";
    currentAssistantContentEl = null;
  });
}

// Handle time-travel node click
window.onNodeSelect = (node) => {
  const notificationBubble = document.createElement('div');
  notificationBubble.className = 'message-wrapper assistant';
  notificationBubble.innerHTML = `
    <div class="avatar assistant">CT</div>
    <div class="message-content" style="border-color: var(--primary);">
      🕒 <strong>Time-Traveled to checkpoint node:</strong> "${node.label}"<br>
      <span style="font-size: 0.8rem; color: var(--muted-foreground);">State snapshot restored. You can now branch off from this point!</span>
    </div>
  `;
  chatMessages.appendChild(notificationBubble);
  chatMessages.scrollTop = chatMessages.scrollHeight;
};

initWebSocket();
