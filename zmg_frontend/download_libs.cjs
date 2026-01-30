// zmg_frontend/download_libs.cjs
const fs = require('fs');
const path = require('path');
const https = require('https');

// 1. 创建存放目录 public/libs
const targetDir = path.join(__dirname, 'public', 'libs');
if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
    console.log(`已创建目录: ${targetDir}`);
}

// 2. 需要下载的文件清单 (使用国内极速源)
const files = [
    { name: 'mammoth.browser.min.js', url: 'https://cdn.bootcdn.net/ajax/libs/mammoth/1.6.0/mammoth.browser.min.js' },
    { name: 'xlsx.full.min.js', url: 'https://cdn.bootcdn.net/ajax/libs/xlsx/0.18.5/xlsx.full.min.js' },
    { name: 'jszip.min.js', url: 'https://cdn.bootcdn.net/ajax/libs/jszip/3.10.1/jszip.min.js' }
];

// 3. 下载函数
const download = (url, dest) => {
    return new Promise((resolve, reject) => {
        const file = fs.createWriteStream(dest);
        https.get(url, (response) => {
            if (response.statusCode !== 200) {
                reject(`请求失败: ${response.statusCode}`);
                return;
            }
            response.pipe(file);
            file.on('finish', () => {
                file.close();
                console.log(`✅ 下载成功: ${path.basename(dest)}`);
                resolve();
            });
        }).on('error', (err) => {
            fs.unlink(dest, () => {}); // 删除未完成的文件
            reject(err.message);
        });
    });
};

// 4. 执行下载
(async () => {
    console.log('正在下载依赖库到本地，请稍候...');
    for (const f of files) {
        try {
            await download(f.url, path.join(targetDir, f.name));
        } catch (e) {
            console.error(`❌ 下载 ${f.name} 失败: ${e}`);
            console.log('请检查网络，或手动下载文件放入 public/libs 目录');
        }
    }
    console.log('🎉 所有依赖已就绪！请继续修改 index.html');
})();