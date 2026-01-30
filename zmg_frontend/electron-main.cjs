const { app, BrowserWindow } = require('electron')

function createWindow () {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      // 🟢 必须关闭安全策略，解决跨域和iframe拒绝连接
      webSecurity: false, 
      allowRunningInsecureContent: true,
      // 🟢 核心修复：开启插件支持，解决 PDF 无法预览
      plugins: true 
    }
  })

  // 连接本地前端服务
  win.loadURL('http://localhost:5173')

  // 🟢 开启开发者工具 (方便你看到报错信息，发布时可以注释掉)
  // win.webContents.openDevTools()
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// 忽略 HTTPS 证书错误 (解决局域网/自签名证书问题)
app.commandLine.appendSwitch('ignore-certificate-errors')
// 允许加载 PDF 插件
app.commandLine.appendSwitch('enable-features', 'PdfViewer')