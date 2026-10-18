// KartoffelFax frontend bootstrap: folder navigation, message list, live status socket.

const state = {
  currentFolder: "inbox",
};

const folderList = document.getElementById("folder-list");
const messageList = document.getElementById("message-list");
const connectionDot = document.getElementById("connection-dot");
const connectionLabel = document.getElementById("connection-label");

async function loadFolder(folder) {
  state.currentFolder = folder;
  document.querySelectorAll(".folder-item").forEach((el) => el.classList.remove("active"));
  document.querySelector(`[data-folder="${folder}"]`)?.classList.add("active");

  messageList.innerHTML = `<p class="p-4 text-sm text-neutral-400">Lade ${folder}…</p>`;
  try {
    const res = await fetch(`/api/fax/${folder}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const messages = await res.json();
    renderMessageList(messages);
  } catch (err) {
    messageList.innerHTML = `<p class="p-4 text-sm text-red-500">Fehler beim Laden: ${err.message}</p>`;
  }
}

function renderMessageList(messages) {
  if (!messages.length) {
    messageList.innerHTML = `<p class="p-4 text-sm text-neutral-400">Keine Faxe in diesem Ordner.</p>`;
    return;
  }
  messageList.innerHTML = messages
    .map(
      (m) => `
      <button class="message-item block w-full border-b border-neutral-100 px-4 py-3 text-left hover:bg-amber-50" data-id="${m.id}">
        <div class="flex justify-between text-sm font-medium">
          <span>${m.fax_number}</span>
          <span class="text-xs text-neutral-400">${m.status}</span>
        </div>
        <div class="truncate text-xs text-neutral-500">${m.subject ?? ""}</div>
      </button>`
    )
    .join("");
}

function connectStatusSocket() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${proto}://${location.host}/ws/status`);

  socket.onopen = () => {
    connectionDot.className = "h-2 w-2 rounded-full bg-green-500";
    connectionLabel.textContent = "Verbunden";
  };
  socket.onclose = () => {
    connectionDot.className = "h-2 w-2 rounded-full bg-red-500";
    connectionLabel.textContent = "Getrennt";
    setTimeout(connectStatusSocket, 3000);
  };
  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // TODO: update message list / detail view based on event type (e.g. 'fax_status_changed')
    console.debug("status event", data);
  };
}

folderList.addEventListener("click", (event) => {
  const target = event.target.closest("[data-folder]");
  if (target) loadFolder(target.dataset.folder);
});

loadFolder(state.currentFolder);
connectStatusSocket();
