const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const waitPort = require('wait-port');

let splash, mainWindow, djangoProcess;

function createSplashScreen() {
    splash = new BrowserWindow({
        width: 400,
        height: 300,
        frame: false,
        resizable: false,
        icon: path.join(__dirname, 'assets', 'landslidelens-icon.ico'),
        backgroundColor: '#ffffff',
    });
    splash.loadFile('splash.html');
}

function createMainWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        icon: path.join(__dirname, 'assets', 'landslidelens-icon.ico'),
        show: false,
        webPreferences: {
            contextIsolation: true
        }
    });

    waitPort({ host: '127.0.0.1', port: 8000, timeout: 20000 }).then(open => {
        if (open) {
            mainWindow.loadURL('http://127.0.0.1:8000/');
            splash.close();
            mainWindow.show();
        } else {
            splash.close();
            app.quit();
        }
    });
}

app.on('ready', () => {
    createSplashScreen();

    djangoProcess = spawn(path.join(__dirname, 'python', 'python.exe'), ['djangoStartup.py'], {
        cwd: __dirname,
        env: {
            ...process.env,
            PYTHONPATH: path.join(__dirname, 'python', 'Lib')
        }
    });

    djangoProcess.stdout.on('data', data => console.log(`Django: ${data}`));
    djangoProcess.stderr.on('data', data => console.error(`Django Error: ${data}`));

    createMainWindow();
});

app.on('window-all-closed', () => {
    if (djangoProcess) djangoProcess.kill();
    app.quit();
});
