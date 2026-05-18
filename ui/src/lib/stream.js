const controllers = {};

export async function consumeSSE(url, body, onEvent) {
  const id = `${url}_${Date.now()}`;

  const controller = new AbortController();
  controllers[id] = controller;

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop();

      for (const part of parts) {
        for (const line of part.split('\n')) {
          if (line.startsWith('data: ')) {
            try {
              onEvent(JSON.parse(line.slice(6)));
            } catch {
              // malformed event, skip
            }
          }
        }
      }
    }
  } finally {
    delete controllers[id];
  }
}

export function cancelAllStreams() {
  for (const [id, ctrl] of Object.entries(controllers)) {
    ctrl.abort();
    delete controllers[id];
  }
}
