import { api, buttonClass, esc, inputClass, secondaryButtonClass } from "./util.js";

const FIELDS = [
  ["display_name", "Name *"],
  ["company", "Firma"],
  ["fax_number", "Faxnummer"],
  ["phone_number", "Telefon"],
  ["email", "E-Mail"],
  ["street", "Straße"],
  ["postal_code", "PLZ"],
  ["city", "Ort"],
  ["notes", "Notizen"],
];

export async function renderContacts(container) {
  container.innerHTML = `
    <div class="mx-auto max-w-3xl space-y-4">
      <div class="flex items-center gap-3">
        <h2 class="text-lg font-semibold">Kontakte</h2>
        <input id="contact-search" type="search" placeholder="Suchen…" class="${inputClass} max-w-xs" />
        <button id="contact-new" class="${buttonClass} ml-auto">Neuer Kontakt</button>
      </div>
      <div id="contact-form-slot"></div>
      <div id="contact-list" class="divide-y divide-neutral-200 rounded border border-neutral-200 bg-white"></div>
    </div>`;

  const listEl = container.querySelector("#contact-list");
  const formSlot = container.querySelector("#contact-form-slot");
  const search = container.querySelector("#contact-search");

  async function refresh() {
    try {
      const query = search.value.trim();
      const contacts = await api(`/api/contacts${query ? `?query=${encodeURIComponent(query)}` : ""}`);
      listEl.innerHTML = contacts.length
        ? contacts.map(rowHtml).join("")
        : `<p class="p-4 text-sm text-neutral-400">Keine Kontakte.</p>`;
      listEl.querySelectorAll("[data-edit]").forEach((btn) =>
        btn.addEventListener("click", () => showForm(contacts.find((c) => c.id === Number(btn.dataset.edit))))
      );
      listEl.querySelectorAll("[data-delete]").forEach((btn) =>
        btn.addEventListener("click", async () => {
          if (!confirm("Kontakt wirklich löschen?")) return;
          try {
            await api(`/api/contacts/${btn.dataset.delete}`, { method: "DELETE" });
            await refresh();
          } catch (err) {
            alert(`Löschen fehlgeschlagen: ${err.message}`);
          }
        })
      );
    } catch (err) {
      listEl.innerHTML = `<p class="p-4 text-sm text-red-600">Fehler beim Laden: ${esc(err.message)}</p>`;
    }
  }

  function showForm(contact = null) {
    formSlot.innerHTML = `
      <form class="space-y-3 rounded border border-amber-300 bg-amber-50 p-4">
        <h3 class="font-medium">${contact ? "Kontakt bearbeiten" : "Neuer Kontakt"}</h3>
        <div class="grid grid-cols-2 gap-3">
          ${FIELDS.map(
            ([key, label]) => `
            <label class="text-xs text-neutral-600 ${key === "notes" ? "col-span-2" : ""}">${label}
              <input name="${key}" value="${esc(contact?.[key] ?? "")}" class="${inputClass} mt-1" ${
                key === "display_name" ? "required" : ""
              } />
            </label>`
          ).join("")}
        </div>
        <p class="form-error hidden text-sm text-red-600"></p>
        <div class="flex gap-2">
          <button type="submit" class="${buttonClass}">Speichern</button>
          <button type="button" class="cancel ${secondaryButtonClass}">Abbrechen</button>
        </div>
      </form>`;
    const form = formSlot.querySelector("form");
    form.querySelector(".cancel").addEventListener("click", () => (formSlot.innerHTML = ""));
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const data = Object.fromEntries(new FormData(form));
      for (const key of Object.keys(data)) if (data[key] === "") data[key] = null;
      try {
        await api(contact ? `/api/contacts/${contact.id}` : "/api/contacts", {
          method: contact ? "PATCH" : "POST",
          json: data,
        });
        formSlot.innerHTML = "";
        await refresh();
      } catch (err) {
        const errEl = form.querySelector(".form-error");
        errEl.textContent = err.message;
        errEl.classList.remove("hidden");
      }
    });
  }

  container.querySelector("#contact-new").addEventListener("click", () => showForm());
  let timer;
  search.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(refresh, 250);
  });
  await refresh();
}

function rowHtml(c) {
  const sub = [c.company, c.fax_number && `Fax ${c.fax_number}`, c.phone_number && `Tel ${c.phone_number}`]
    .filter(Boolean)
    .map(esc)
    .join(" · ");
  return `
    <div class="flex items-center gap-3 px-4 py-3">
      <div class="min-w-0 flex-1">
        <div class="truncate text-sm font-medium">${esc(c.display_name)}</div>
        <div class="truncate text-xs text-neutral-500">${sub}</div>
      </div>
      <button data-edit="${c.id}" class="${secondaryButtonClass}">Bearbeiten</button>
      <button data-delete="${c.id}" class="${secondaryButtonClass} text-red-700">Löschen</button>
    </div>`;
}
