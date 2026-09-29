/* Preserve HTTP failures while stopping the legacy Flash retry loop.
 * No command is acknowledged or replayed by this host-page recovery path. */
(() => {
    const originalFetch = window.fetch.bind(window);
    let recovering = false;
    window.fetch = async (...args) => {
        const response = await originalFetch(...args);
        const url = new URL(response.url || (args[0] instanceof Request ? args[0].url : args[0]), location.href);
        if (response.status !== 422 || url.origin !== location.origin ||
            url.pathname !== '/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/command.php') {
            return response;
        }
        let error;
        try { error = await response.clone().json(); } catch { return response; }
        if (error.code !== 'unsupported_action' || error.recovery !== 'reload_saved_empire' || recovering) {
            return response;
        }
        recovering = true;
        const host = document.getElementById('ruffle');
        if (!host) return response;
        // Removing the player disposes its VM and pending retry timers. The
        // reload loads authoritative saved state rather than optimistic UI state.
        host.replaceChildren();
        const panel = document.createElement('section');
        panel.setAttribute('role', 'alert');
        panel.style.cssText = 'box-sizing:border-box;width:760px;padding:48px;background:#fff4d6;border:2px solid #8a6332;color:#352714';
        const title = document.createElement('h2');
        title.textContent = 'This action is not available yet';
        const message = document.createElement('p');
        message.textContent = 'This request was not applied. Reload your saved empire to continue playing.';
        const button = document.createElement('button');
        button.textContent = 'Reload empire';
        button.addEventListener('click', () => location.replace('/ruffle.html?client=1.2.7'));
        panel.append(title, message, button);
        host.append(panel);
        button.focus();
        return response;
    };
})();
