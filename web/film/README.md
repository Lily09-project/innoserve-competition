# 純程式產品動畫

啟動作品後，開啟 `http://127.0.0.1:8765/film/index.html`，或從事件工作台點「產品動畫」。

本片長 150 秒，九個章節，沒有生成式圖片、虛擬人物或外部媒體。以自行繪製的網路設備、移動封包與事件面板呈現方法。拓樸為示意；成果頁使用已完成實測。到期回復段標示動畫加速，實測有效期為實際 30 秒。

- `scene.mjs`：章節、字幕、時間軸與純函式 `frameSvg(time)`。
- `player.mjs`：播放、暫停、拖曳進度、速度、跳章、全螢幕與鍵盤。
- `index.html`：播放器，不會自動啟動模型或部署策略。
- `../../scripts/render_product_film.mjs`：同一畫面函式離線輸出 MP4。HTML 與影片共享時間軸。

## 重新輸出

需要 Node.js、sharp 及 FFmpeg。環境變數 `RENDER_NODE_MODULES` 指向含 sharp 的 node_modules 目錄，`FFMPEG_BINARY` 指向 FFmpeg 執行檔。

```text
node scripts/render_product_film.mjs OUTPUT_DIRECTORY
```

加 `--preview` 只輸出九張章節預覽。正式輸出 1920×1080、24fps、H.264/yuv420p、無語音；既有 MP4 不覆寫。`render.json` 記錄尺寸、幀數與容量。可用 `scene.mjs` 修改文字與內容後重新輸出。

播放器使用 ES module，請由本機展示服務開啟；MP4 可直接離線播放。方向鍵控制進度，空白鍵播放／暫停；焦點在原生控制元件時保留該元件的鍵盤操作。
