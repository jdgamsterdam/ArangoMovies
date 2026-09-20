console.log("script.js loaded");

function setAltState(value) {
    const el = document.getElementById("alt-key-state");
    if (!el) return;

    if (el.textContent === value) return;
    el.textContent = value;
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
}

function setAltClickStore(armed) {
    if (!(window.dash_clientside && window.dash_clientside.set_props)) {
        console.warn("dash_clientside.set_props not available");
        return;
    }

    window.dash_clientside.set_props("alt-click-store", {
        data: {
            armed: armed,
            ts: Date.now()
        }
    });
}

function attachAltPointerHandler() {
    const root = document.getElementById("cytoscape1");
    if (!root) {
        console.warn("cytoscape1 not found");
        return false;
    }

    if (root.dataset.altPointerAttached === "true") {
        return true;
    }

    root.addEventListener(
        "pointerdown",
        function (e) {
            if (e.altKey) {
                setAltClickStore(true);
            } else {
                setAltClickStore(false);
            }
        },
        true
    );

    root.dataset.altPointerAttached = "true";
    console.log("ALT pointer handler attached to cytoscape1");
    return true;
}

function attachWhenReady(retries = 40) {
    if (attachAltPointerHandler()) return;
    if (retries <= 0) {
        console.warn("Could not attach ALT pointer handler");
        return;
    }
    setTimeout(() => attachWhenReady(retries - 1), 300);
}

// keep this only if you still want the hidden Div state for other logic/debugging
document.addEventListener("keydown", (e) => {
    if (e.altKey) setAltState("true");
});

document.addEventListener("keyup", (e) => {
    if (!e.altKey) {
        setAltState("false");
        setAltClickStore(false);
    }
});

window.addEventListener("blur", () => {
    setAltState("false");
    setAltClickStore(false);
});

document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
        setAltState("false");
        setAltClickStore(false);
    }
});

document.addEventListener("pointerup", () => {
    setAltState("false");
});

window.addEventListener("load", () => {
    attachWhenReady();
});