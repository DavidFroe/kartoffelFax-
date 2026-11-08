import { api, buttonClass, esc, inputClass, secondaryButtonClass } from "./util.js";

export async function openCompose({ onSent }) {
  const overlay = document.createElement("div");
  overlay.className = "fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4";
  overlay.innerHTML = `
    <form class="w-full max-w-lg space-y-4 rounded bg-white p-6 shadow-xl">
      <h2 class="text-lg font-semibold">Neues Fax</h2>
      <label class="block text-xs text-neutral-600">Empfänger aus Kontakten
        <select name="contact" class="${inputClass} mt-1"><option value="">– Faxnummer frei eingeben –</option></select>
      </label>
      <label class="block text-xs text-neutral-600">Faxnummer *
        <input name="fax_number" required class="${inputClass} mt-1" />
      </label>
      <label class="block text-xs text-neutral-600">Betreff
        <input name="subject" class="${inputClass} mt-1" />
      </label>
      <div>
        <div class="dropzone cursor-pointer rounded border-2 border-dashed border-neutral-300 p-6 text-center text-sm text-neutral-500">
          Dateien hierher ziehen oder klicken (PDF, Bilder)
        </div>
        <input type="file" multiple hidden class="file-input" />
        <ul class="file-list mt-2 space-y-1 text-sm"></ul>
      </div>
      <p class="form-error hidden text-sm text-red-600"></p>
      <div class="flex justify-end gap-2">
        <button type="button" class="cancel ${secondaryButtonClass}">Abbrechen</button>
        <button type="submit" class="${buttonClass}">Senden</button>
      </div>
    </form>`;
  document.body.appendChild(overlay);

  const form = overlay.querySelector("form");
  const select = form.elements.contact;
  const faxInput = form.elements.fax_number;
  const dropzone = overlay.querySelector(".dropzone");
  const fileInput = overlay.querySelector(".file-input");
  const fileList = overlay.querySelector(".file-list");
  const errorEl = overlay.querySelector(".form-error");
  const uploads = [];
  let contacts = [];

  const close = () => overlay.remove();
  const showError = (message) => {
    errorEl.textContent = message;
    errorEl.classList.remove("hidden");
  };

  try {
    contacts = await api("/api/contacts");
    for (const c of contacts) {
      const option = document.createElement("option");
      option.value = c.id;
      option.textContent = c.fax_number ? `${c.display_name} (${c.fax_number})` : `${c.display_name} (keine Faxnummer)`;
      option.disabled = !c.fax_number;
      select.appendChild(option);
    }
  } catch (err) {
    showError(`Kontakte konnten nicht geladen werden: ${err.message}`);
  }

  select.addEventListener("change", () => {
    const contact = contacts.find((c) => c.id === Number(select.value));
    if (contact) faxInput.value = contact.fax_number;
  });

  function renderFiles() {
    fileList.innerHTML = uploads
      .map((u, i) => `<li class="flex justify-between rounded bg-neutral-100 px-2 py-1"><span class="truncate">${esc(u.original_name)}</span><button type="button" data-remove="${i}" class="text-red-700">✕</button></li>`)
      .join("");
    fileList.querySelectorAll("[data-remove]").forEach((btn) =>
      btn.addEventListener("click", () => {
        uploads.splice(Number(btn.dataset.remove), 1);
        renderFiles();
      })
    );
  }

  async function upload(files) {
    for (const file of files) {
      const body = new FormData();
      body.append("file", file);
      try {
        uploads.push(await api("/api/fax/upload", { method: "POST", body }));
      } catch (err) {
        showError(`Upload von ${file.name} fehlgeschlagen: ${err.message}`);
      }
    }
    renderFiles();
  }

  dropzone.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", () => upload([...fileInput.files]));
  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("border-amber-500", "bg-amber-50");
  });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("border-amber-500", "bg-amber-50"));
  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("border-amber-500", "bg-amber-50");
    upload([...e.dataTransfer.files]);
  });

  overlay.querySelector(".cancel").addEventListener("click", close);
  overlay.addEventListener("mousedown", (e) => {
    if (e.target === overlay) close();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const sent = await api("/api/fax/send", {
        json: {
          fax_number: faxInput.value.trim(),
          subject: form.elements.subject.value.trim() || null,
          contact_id: select.value ? Number(select.value) : null,
          source_file_paths: uploads.map((u) => u.stored_path),
        },
      });
      close();
      onSent(sent);
    } catch (err) {
      showError(err.message);
    }
  });
}
