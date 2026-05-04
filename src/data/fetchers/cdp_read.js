/**
 * cdp_read.js — Chrome CDP 读取器（Node.js）
 * 用法:
 *   node cdp_read.js new <url> <selector> [timeout_ms]
 *   node cdp_read.js read <pageId> <selector> [timeout_ms]
 *
 * 依赖: NODE_PATH=/home/wingo/.npm-global/lib/node_modules node cdp_read.js ...
 * Chrome: --remote-debugging-port=9222
 */
const WebSocket = require('ws');

const BROWSER_WS = 'ws://127.0.0.1:9222/devtools/browser/37bb6b0a-c104-4343-9973-4f4e34652bf6';

function send(ws, msg) {
    return new Promise((resolve, reject) => {
        const id = Date.now().toString() + Math.random().toString(36).slice(2);
        const full = { id, ...(typeof msg === 'string' ? { method: msg } : msg) };
        let done = false;
        const timer = setTimeout(() => {
            if (!done) { done = true; reject(new Error('ws timeout')); }
        }, 20000);
        ws.on('message', (data) => {
            try {
                const d = JSON.parse(data.toString());
                if (d.id === id) {
                    done = true; clearTimeout(timer);
                    resolve(d);
                }
            } catch (e) {}
        });
        ws.send(JSON.stringify(full));
    });
}

async function main() {
    const mode = process.argv[2]; // 'new' or 'read'
    const target = process.argv[3]; // URL or pageId
    const selector = process.argv[4] || 'body';
    const timeout = parseInt(process.argv[5] || '15000');

    if (!target) {
        console.log(JSON.stringify({ status: 'failed', error: 'usage: node cdp_read.js new|read <url|pageId> <selector> [ms]' }));
        return;
    }

    try {
        let pageId = target;

        if (mode === 'new') {
            // Connect to browser WS, create new tab
            const browserWs = new WebSocket(BROWSER_WS);
            await new Promise((res, rej) => { browserWs.on('open', res); browserWs.on('error', rej); });

            const r = await send(browserWs, {
                method: 'Target.createTarget',
                params: { url: target, browserContextId: null }
            });
            pageId = r.result?.targetId;
            if (!pageId) throw new Error('no targetId returned');
            browserWs.close();

            // Wait for tab to initialize
            await new Promise(r => setTimeout(r, 2500));
        }

        // Connect to page
        const pageWs = new WebSocket(`ws://127.0.0.1:9222/devtools/page/${pageId}`);
        await new Promise((res, rej) => { pageWs.on('open', res); pageWs.on('error', rej); });

        await send(pageWs, 'Page.enable');
        await send(pageWs, 'Runtime.enable');

        // Wait for Page.loadEventFired (full page load)
        await new Promise((resolve) => {
            pageWs.on('message', function handler(data) {
                try {
                    const msg = JSON.parse(data.toString());
                    if (msg.method === 'Page.loadEventFired') {
                        pageWs.removeListener('message', handler);
                        resolve();
                    }
                } catch (e) {}
            });
            // timeout fallback
            setTimeout(resolve, timeout);
        });

        // Extra wait for SPA
        await new Promise(r => setTimeout(r, 2000));

        // Read innerText
        const expr = `document.querySelector("${selector}") ? document.querySelector("${selector}").innerText : "NOT_FOUND"`;
        const result = await send(pageWs, {
            id: 'eval_' + Date.now(),
            method: 'Runtime.evaluate',
            params: { expression: expr, returnByValue: true }
        });

        pageWs.close();
        const text = result.result?.result?.value || null;
        console.log(JSON.stringify({ status: 'success', text, pageId }));

    } catch (e) {
        console.log(JSON.stringify({ status: 'failed', error: e.message }));
    }
}

main();
