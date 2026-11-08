import { api, buttonClass, esc, inputClass, secondaryButtonClass } from "./util.js";

export async function renderSettings(container) {
  container.innerHTML = `
    <div class="mx-auto max-w-3xl space-y-4">
      <div class="flex items-center gap-3">
        <h2 class="text-lg font-semibold">Fritz!Box-Verbindungen</h2>
        <button id="conn-new" class="${buttonClass} ml-auto">Neue Verbindung</button>
      </div>
      <div id="conn-form-slot"></div>
      <div id="conn-list" class="divide-y divide-neutral-200 rounded border border-neutral-200 bg-white"></div>
    </div>`;

  const listEl = container.querySelector("#conn-list");
  const formSlot = container.querySelector("#conn-form-slot");

  async function refresh() {
    try {
      const conns = await api("/api/settings/connections");
      listEl.innerHTML = conns.length
        ? conns.map(rowHtml).join("")
        : `<p class="p-4 text-sm text-neutral-400">Noch keine Verbindung eingerichtet.</p>`;
      listEl.querySelectorAll("[data-test]").forEach((btn) =>
        btn.addEventListener("click", () => runTest(btn.dataset.test, listEl.querySelector(`[data-result="${btn.dataset.test}"]`), btn))
      );
    } catch (err) {
      listEl.innerHTML = `<p class="p-4 text-sm text-red-600">Fehler beim Laden: ${esc(err.message)}</p>`;
    }
  }

  async function runTest(id, resultEl, btn) {
    btn.disabled = true;
    resultEl.textContent = "Teste…";
    resultEl.className = "mt-1 text-xs text-neutral-500";
    try {
      const r = await api(`/api/settings/connections/${id}/test`, { method: "POST" });
      if (!r.reachable) {
        resultEl.textContent = "Nicht erreichbar" + (r.vpn_interface_up === false ? " (VPN-Interface ist down)" : "");
        resultEl.className = "mt-1 text-xs text-red-600";
      } else if (r.error) {
        resultEl.textContent = `Erreichbar, aber: ${r.error}`;
        resultEl.className = "mt-1 text-xs text-amber-700";
      } else {
        const info = r.device_info ?? {};
        resultEl.textContent = `OK – ${info.NewModelName ?? "Fritz!Box"} ${info.NewSoftwareVersion ?? ""}`.trim();
        resultEl.className = "mt-1 text-xs text-green-700";
      }
    } catch (err) {
      resultEl.textContent = `Test fehlgeschlagen: ${err.message}`;
      resultEl.className = "mt-1 text-xs text-red-600";
    } finally {
      btn.disabled = false;
    }
  }

  function showForm() {
    const field = (name, label, attrs = "") =>
      `<label class="text-xs text-neutral-600">${label}<input name="${name}" ${attrs} class="${inputClass} mt-1" /></label>`;
    formSlot.innerHTML = `
      <form class="space-y-3 rounded border border-amber-300 bg-amber-50 p-4">
        <h3 class="font-medium">Neue Verbindung</h3>
        <div class="grid grid-cols-2 gap-3">
          ${field("name", "Name *", "required")}
          ${field("host", "Host / IP *", 'required placeholder="192.168.178.1"')}
          ${field("tr064_port", "TR-064-Port", 'type="number" value="49000"')}
          ${field("tr064_username", "TR-064-Benutzer")}
          ${field("tr064_password", "TR-064-Passwort", 'type="password" autocomplete="new-password"')}
          ${field("sip_port", "SIP-Port", 'type="number" value="5060"')}
          ${field("sip_username", "SIP-Benutzer")}
          ${field("sip_password", "SIP-Passwort", 'type="password" autocomplete="new-password"')}
          <label class="text-xs text-neutral-600">Transport
            <select name="transport" class="${inputClass} mt-1">
              <option value="sip_t38">SIP / T.38</option>
              <option value="sip_g711">SIP / G.711</option>
              <option value="capi_tcp">CAPI über TCP</option>
            </select>
          </label>
          ${field("vpn_interface", "VPN-Interface (optional)", 'placeholder="wg0"')}
          <label class="col-span-2 flex items-center gap-2 text-sm"><input type="checkbox" name="requires_vpn" /> Benötigt VPN</label>
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
      const f = new FormData(form);
      const text = (key) => (f.get(key) || null);
      const payload = {
        name: f.get("name"),
        host: f.get("host"),
        tr064_port: Number(f.get("tr064_port")) || 49000,
        tr064_username: text("tr064_username"),
        tr064_password: text("tr064_password"),
        sip_port: Number(f.get("sip_port")) || 5060,
        sip_username: text("sip_username"),
        sip_password: text("sip_password"),
        transport: f.get("transport"),
        requires_vpn: f.get("requires_vpn") === "on",
        vpn_interface: text("vpn_interface"),
      };
      try {
        await api("/api/settings/connections", { json: payload });
        formSlot.innerHTML = "";
        await refresh();
      } catch (err) {
        const errEl = form.querySelector(".form-error");
        errEl.textContent = err.message;
        errEl.classList.remove("hidden");
      }
    });
  }

  container.querySelector("#conn-new").addEventListener("click", showForm);
  await refresh();
}

function rowHtml(c) {
  return `
    <div class="flex items-start gap-3 px-4 py-3">
      <div class="min-w-0 flex-1">
        <div class="truncate text-sm font-medium">${esc(c.name)}</div>
        <div class="truncate text-xs text-neutral-500">${esc(c.host)}:${esc(c.tr064_port)} · ${esc(c.transport)}${c.requires_vpn ? " · VPN" : ""}</div>
        <div data-result="${c.id}" class="mt-1 text-xs"></div>
      </div>
      <button data-test="${c.id}" class="${secondaryButtonClass}">Testen</button>
    </div>`;
}
