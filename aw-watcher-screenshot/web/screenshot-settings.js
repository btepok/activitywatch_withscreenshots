(function () {
  var BUCKET = "aw-watcher-screenshot-settings";

  function api(path, options) {
    return fetch(path, options || {});
  }

  function loadSettings() {
    return api("/api/0/buckets/" + BUCKET + "/events?limit=1").then(function (response) {
      if (!response.ok) return null;
      return response.json().then(function (events) {
        return events && events.length ? events[0].data : null;
      });
    });
  }

  function saveSettings(data) {
    var bucketBody = JSON.stringify({
      client: "aw-webui",
      type: "screenshot-settings",
      hostname: "unknown",
    });
    return api("/api/0/buckets/" + BUCKET, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: bucketBody,
    }).then(function () {
      return api("/api/0/buckets/" + BUCKET + "/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify([
          {
            timestamp: new Date().toISOString(),
            duration: 0,
            data: data,
          },
        ]),
      });
    });
  }

  function ensurePanel() {
    var panel = document.getElementById("aw-shot-panel");
    if (panel) return panel;
    panel = document.createElement("div");
    panel.id = "aw-shot-panel";
    panel.innerHTML =
      '<div style="font-weight:600;margin-bottom:8px">Скриншоты</div>' +
      '<label style="display:flex;gap:8px;align-items:center;margin-bottom:8px">' +
      '<input id="aw-shot-enabled" type="checkbox"> Снимать экран</label>' +
      '<label style="display:flex;gap:8px;align-items:center;margin-bottom:10px">Каждые ' +
      '<input id="aw-shot-interval" type="number" min="1" step="1" style="width:72px">' +
      '<select id="aw-shot-unit"><option value="seconds">секунд</option>' +
      '<option value="minutes">минут</option></select></label>' +
      '<button id="aw-shot-save" type="button">Сохранить</button>' +
      '<div id="aw-shot-status" style="margin-top:8px;font-size:12px"></div>';
    panel.style.cssText =
      "position:fixed;z-index:2000;background:#fff;color:#222;border:1px solid #ddd;" +
      "border-radius:8px;padding:12px;box-shadow:0 8px 24px rgba(0,0,0,.15);width:260px";
    document.body.appendChild(panel);
    panel.addEventListener("click", function (event) {
      event.stopPropagation();
    });
    document.getElementById("aw-shot-save").addEventListener("click", onSave);
    return panel;
  }

  function fill(data) {
    document.getElementById("aw-shot-enabled").checked = !data || data.enabled !== false;
    document.getElementById("aw-shot-interval").value =
      data && data.interval ? data.interval : 60;
    document.getElementById("aw-shot-unit").value =
      data && data.interval_unit === "minutes" ? "minutes" : "seconds";
  }

  function openPanel(anchor) {
    var panel = ensurePanel();
    var rect = anchor.getBoundingClientRect();
    panel.style.top = rect.bottom + 8 + "px";
    panel.style.left = Math.max(8, rect.right - 260) + "px";
    panel.style.display = "block";
    document.getElementById("aw-shot-status").textContent = "";
    loadSettings()
      .then(fill)
      .catch(function () {
        document.getElementById("aw-shot-status").textContent = "Не удалось прочитать настройки";
      });
  }

  function closePanel() {
    var panel = document.getElementById("aw-shot-panel");
    if (panel) panel.style.display = "none";
  }

  function onSave() {
    var status = document.getElementById("aw-shot-status");
    var interval = Number(document.getElementById("aw-shot-interval").value);
    var unit = document.getElementById("aw-shot-unit").value;
    if (!interval || interval <= 0) {
      status.textContent = "Интервал должен быть больше нуля";
      return;
    }
    status.textContent = "Сохраняю...";
    saveSettings({
      enabled: document.getElementById("aw-shot-enabled").checked,
      interval: interval,
      interval_unit: unit,
    })
      .then(function (response) {
        if (!response.ok) throw new Error("save failed");
        status.textContent = "Сохранено, применится сразу";
      })
      .catch(function () {
        status.textContent = "Не удалось сохранить";
      });
  }

  function mount(link) {
    if (document.getElementById("aw-shot-btn")) return;
    var item = document.createElement("li");
    item.className = "nav-item";
    item.id = "aw-shot-item";
    item.innerHTML = '<a class="nav-link" href="#" id="aw-shot-btn">Скриншоты</a>';
    var parent = link.closest("li") || link.parentElement;
    parent.parentElement.insertBefore(item, parent);
  }

  function findSettingsLink() {
    var nav = document.querySelector(".aw-navbar") || document.querySelector("nav.navbar");
    if (!nav) return null;
    var links = nav.querySelectorAll("a[href]");
    for (var i = 0; i < links.length; i++) {
      if (links[i].id === "aw-shot-btn") continue;
      var href = links[i].getAttribute("href") || "";
      if (href.indexOf("settings") !== -1) return links[i];
    }
    return null;
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest && event.target.closest("#aw-shot-btn");
    if (button) {
      event.preventDefault();
      var panel = document.getElementById("aw-shot-panel");
      if (panel && panel.style.display === "block") closePanel();
      else openPanel(button);
      return;
    }
    if (!event.target.closest || !event.target.closest("#aw-shot-panel")) closePanel();
  });

  var observer = new MutationObserver(function () {
    var link = findSettingsLink();
    if (link) mount(link);
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });
})();
