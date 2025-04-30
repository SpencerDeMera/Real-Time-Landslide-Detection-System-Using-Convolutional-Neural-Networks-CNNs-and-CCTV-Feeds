const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const waitPort = require('wait-port');

let djangoProcess;

function createWindow() {
  const win = new BrowserWindow({
      width: 1200,
      height: 800,
      icon: path.join(__dirname, 'assets', 'landslidelens-icon.ico'),
      webPreferences: {
          nodeIntegration: false,
          contextIsolation: true,
      }
  });

  console.log("Waiting for Django on port 8000...");
  waitPort({ host: '127.0.0.1', port: 8000, timeout: 15000 }).then(open => {
    if (open) {
        win.loadURL('http://127.0.0.1:8000');
    } else {
        win.loadURL('data:text/html,<h1>Could not connect to Django server on 127.0.0.1:8000</h1>');
    }
  }).catch((err) => {
      console.log("waitPort error:", err);
      win.loadURL('data:text/html,<h1>wait-port error: ' + err + '</h1>');
  });
}


app.whenReady().then(() => {
  const djangoPath = path.join(__dirname, 'DjangoProject');
  const pythonExe = path.join(djangoPath, '.venv', 'Scripts', 'python.exe');
  console.log("Launching Django with:", pythonExe, "in", djangoPath);
  
  djangoProcess = spawn(pythonExe, ['manage.py', 'runserver', '0.0.0.0:8000'], {
      cwd: djangoPath,
      stdio: 'inherit',
      shell: false
  });
  
  djangoProcess.on('error', (err) => {
      console.error('Failed to start Django process:', err);
  });
  djangoProcess.on('exit', (code, signal) => {
      console.log(`Django process exited with code ${code}, signal ${signal}`);
  });

    createWindow();

    app.on('activate', function () {
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

app.on('window-all-closed', () => {
    if (djangoProcess) djangoProcess.kill();
    if (process.platform !== 'darwin') app.quit();
});
