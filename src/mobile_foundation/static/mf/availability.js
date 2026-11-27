/** Opt-in fetch boundary. Keeps the application DOM and never replays requests. */
export function createAvailability({container = document.body, probeUrl, fetcher = globalThis.fetch.bind(globalThis)} = {}) {
  const banner = document.createElement('aside');
  banner.setAttribute('role', 'status');
  banner.setAttribute('aria-live', 'polite');
  banner.hidden = true;
  banner.className = 'mf-notice';
  const message = document.createElement('p');
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'mf-btn mf-btn--secondary';
  button.textContent = '연결 다시 확인';
  button.hidden = !probeUrl;
  banner.append(message, button);
  container.prepend(banner);
  let disposed = false;
  function unavailable(offline = false) {
    if (disposed) return;
    message.textContent = offline
      ? '네트워크 연결을 확인해 주세요. 입력 내용은 이 화면에 유지됩니다.'
      : '서비스에 연결할 수 없습니다. 입력을 유지하고 있습니다. 저장 결과 확인 후 다시 시도해 주세요.';
    banner.hidden = false;
  }
  async function request(input, init) {
    try {
      const response = await fetcher(input, init);
      if ([502, 503, 504].includes(response.status)) unavailable();
      else if (response.ok && !disposed) banner.hidden = true;
      return response;
    } catch (error) {
      if (error?.name !== 'AbortError') unavailable(globalThis.navigator?.onLine === false);
      throw error;
    }
  }
  async function probe() {
    if (!probeUrl || button.disabled) return;
    button.disabled = true;
    try { await request(probeUrl, {method: 'GET', cache: 'no-store', signal: AbortSignal.timeout(5000)}); }
    catch { /* request already reports connectivity; never replay an application mutation. */ }
    finally { button.disabled = false; }
  }
  const offline = () => unavailable(true);
  button.addEventListener('click', probe);
  globalThis.addEventListener('offline', offline);
  if (globalThis.navigator?.onLine === false) offline();
  return {request, unavailable, dispose() {
    disposed = true;
    globalThis.removeEventListener('offline', offline);
    button.removeEventListener('click', probe);
    banner.remove();
  }};
}
