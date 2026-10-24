// preload.js — bridge segura entre o renderer (Flask) e o processo main do Electron
// Expõe 'electronAPI.printToPDF()' via contextBridge e intercepta window.print()
// para redirecionar ao handler nativo de PDF do processo main.
//
// Segurança: contextIsolation: true + sandbox: true permanecem ativos.
// ipcRenderer e contextBridge funcionam em sandboxed preloads (Electron 20+).

const { contextBridge, ipcRenderer } = require('electron');

// Expõe a API segura para o renderer
contextBridge.exposeInMainWorld('electronAPI', {
  /**
   * Solicita ao processo main que gere um PDF da página atual e o abra.
   * Retorna uma Promise<{ ok: boolean, error?: string }>
   */
  printToPDF: () => ipcRenderer.invoke('print-to-pdf'),

  /** Flag para o renderer saber que está dentro do Electron */
  isElectron: true,
});

// Intercepta window.print() no mundo isolado do preload.
// Como o preload corre no mesmo mundo que o renderer (mas isolado via contextBridge),
// precisamos injetar a interceptação via script no mundo do renderer.
// A forma correta é usar o evento 'did-finish-load' no main e injetar JS —
// mas como temos sandbox, usamos executeJavaScript via o canal IPC de retorno.
//
// Abordagem alternativa e mais simples: o renderer já chama imprimirOuPDF()
// que detecta window.electronAPI.isElectron e redireciona. O window.print()
// nativo nunca é chamado diretamente pelo nosso código, mas pode ser chamado
// por Ctrl+P. Para cobrir isso, usamos o evento 'before-input-event' no main.js.
