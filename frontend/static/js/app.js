// KartoffelFax frontend: navigation, message list, detail pane, live status socket.
import { openCompose } from "./compose.js";
import { renderContacts } from "./contacts.js";
import { renderSettings } from "./settings.js";
import { api, esc, formatDate } from "./util.js";

const state = { view: "folder", currentFolder: "inbox", selectedId: null };

const messageList = document.getElementById("message-list");
const detailView = document.getElementById("detail-view");
const connectionDot = document.getElementById("connection-dot");
const connectionLabel = document.getElementById("connection-label");

const STATUS_LABELS = {
  draft: "Entwurf", queued: "In Warteschlange", dialing: "Wählt", sending: "Sendet",
  sent: "Gesendet", failed: "Fehlgeschlagen", received: "Empfangen", cancelled: "Abgebrochen",
};

function setActiveNav(selector) {
  document.querySelectorAll(".folder-item").forEach((el) => el.classList.remove("active"));
  document.querySelector(selector)?.classList.add("active");
}

async function loadFolder(folder) {
  state.view = "folder";
  state.currentFolder = folder;
  state.selectedId = null;
  messageList.classList.remove("hidden");
  setActiveNav(`[data-folder="${folder}"]`);
  detailView.innerHTML = `<div class="flex h-full items-center justify-center text-neutral-400"><p>Wähle ein Fax aus, um die Vorschau anzuzeigen.</p></div>`;
  await refreshList();
}

async function refreshList() {
  try {
    renderMessageList(await api(`/api/fax/${state.currentFolder}`));
  } catch (err) {
    messageList.innerHTML = `<p class="p-4 text-sm text-red-500">Fehler beim Laden: ${esc(err.message)}</p>`;
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
      <button class="message-item block w-full border-b border-neutral-100 px-4 py-3 text-left hover:bg-amber-50 ${m.id === state.selectedId ? "bg-amber-100" : ""}" data-id="${m.id}">
        <div class="flex justify-between text-sm font-medium">
          <span>${esc(m.fax_number)}</span>
          <span class="status-label text-xs text-neutral-500">${esc(STATUS_LABELS[m.status] ?? m.status)}</span>
        </div>
        <div class="truncate text-xs text-neutral-500">${esc(m.subject ?? "")}</div>
      </button>`
    )
    .join("");
}

async function showDetail(id) {
  state.selectedId = id;
  messageList.querySelectorAll(".message-item").forEach((el) =>
    el.classList.toggle("bg-amber-100", Number(el.dataset.id) === id)
  );
  try {
    const [msg, events] = await Promise.all([
      api(`/api/fax/message/${id}`),
      api(`/api/fax/message/${id}/events`).catch(() => []),
    ]);
    detailView.innerHTML = `
      <div class="mx-auto max-w-3xl space-y-4">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="text-lg font-semibold">${esc(msg.subject || "(ohne Betreff)")}</h2>
            <p class="text-sm text-neutral-600">${msg.direction === "incoming" ? "Von" : "An"} ${esc(msg.fax_number)}</p>
          </div>
          <span class="rounded bg-neutral-200 px-2 py-1 text-xs">${esc(STATUS_LABELS[msg.status] ?? msg.status)}</span>
        </div>
        ${msg.error_message ? `<p class="rounded bg-red-50 p-2 text-sm text-red-700">${esc(msg.error_message)}</p>` : ""}
        <dl class="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
          <dt class="text-neutral-500">Erstellt</dt><dd>${esc(formatDate(msg.created_at))}</dd>
          ${msg.sent_at ? `<dt class="text-neutral-500">Gesendet</dt><dd>${esc(formatDate(msg.sent_at))}</dd>` : ""}
          ${msg.received_at ? `<dt class="text-neutral-500">Empfangen</dt><dd>${esc(formatDate(msg.received_at))}</dd>` : ""}
          ${msg.page_count ? `<dt class="text-neutral-500">Seiten</dt><dd>${esc(msg.page_count)}</dd>` : ""}
        </dl>
        ${
          msg.pdf_path
            ? `<iframe title="Fax-Vorschau" src="/api/fax/message/${id}/pdf" class="h-[28rem] w-full rounded border border-neutral-300 bg-white"></iframe>`
            : `<p class="rounded border border-dashed border-neutral-300 p-4 text-sm text-neutral-400">Noch keine PDF-Vorschau verfügbar.</p>`
        }
        <div>
          <h3 class="mb-2 text-sm font-semibold">Verlauf</h3>
          <ol class="space-y-1 border-l-2 border-amber-300 pl-3 text-sm">
            ${
              events.length
                ? events
                    .map((e) => `<li><span class="text-neutral-500">${esc(formatDate(e.created_at))}</span> ${esc(e.event_type)}${e.detail ? ` – ${esc(e.detail)}` : ""}</li>`)
                    .join("")
                : `<li class="text-neutral-400">Keine Ereignisse.</li>`
            }
          </ol>
        </div>
        <button id="detail-delete" class="rounded border border-neutral-300 bg-white px-3 py-1.5 text-sm text-red-700 hover:bg-neutral-100">Löschen</button>
      </div>`;
    detailView.querySelector("#detail-delete").addEventListener("click", async () => {
      if (!confirm("Fax wirklich löschen?")) return;
      try {
        await api(`/api/fax/message/${id}`, { method: "DELETE" });
        await loadFolder(state.currentFolder);
      } catch (err) {
        alert(`Löschen fehlgeschlagen: ${err.message}`);
      }
    });
  } catch (err) {
    detailView.innerHTML = `<p class="text-sm text-red-600">Fehler beim Laden: ${esc(err.message)}</p>`;
  }
}

async function showView(view, render) {
  state.view = view;
  state.selectedId = null;
  messageList.classList.add("hidden");
  setActiveNav(`[data-view="${view}"]`);
  await render(detailView);
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
  socket.onmessage = async (event) => {
    let data;
    try {
      data = JSON.parse(event.data);
    } catch {
      return;
    }
    // Event schema is not fixed yet: any event naming a fax triggers a refresh of what is on screen.
    const faxId = data.fax_id ?? data.fax_message_id;
    if (faxId === undefined || state.view !== "folder") return;
    await refreshList();
    if (state.selectedId === faxId) await showDetail(faxId);
  };
}

document.getElementById("folder-list").addEventListener("click", (event) => {
  const folder = event.target.closest("[data-folder]");
  if (folder) return loadFolder(folder.dataset.folder);
  const view = event.target.closest("[data-view]");
  if (view?.dataset.view === "contacts") showView("contacts", renderContacts);
  if (view?.dataset.view === "settings") showView("settings", renderSettings);
});

messageList.addEventListener("click", (event) => {
  const item = event.target.closest("[data-id]");
  if (item) showDetail(Number(item.dataset.id));
});

document.getElementById("btn-new-fax").addEventListener("click", () =>
  openCompose({
    onSent: async () => {
      await loadFolder("outbox");
    },
  })
);

loadFolder(state.currentFolder);
connectStatusSocket();
