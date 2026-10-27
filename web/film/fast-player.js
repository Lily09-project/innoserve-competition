const video = document.getElementById("product-video");
const status = document.getElementById("video-status");
const announce = () => {
  status.textContent = `${Math.floor(video.currentTime)} / 45 秒 · ${video.playbackRate}×`;
};
document.getElementById("video-speed").onchange = (event) => {
  video.playbackRate = Number(event.target.value);
  announce();
};
async function startAt(time) {
  video.currentTime = time;
  try {
    await video.play();
  } catch {
    status.textContent = "請按播放器的播放按鈕開始。";
  }
}
document.getElementById("restart-video").onclick = () => startAt(0);
document.querySelectorAll("[data-time]").forEach((button) => {
  button.onclick = () => startAt(Number(button.dataset.time));
});
let lastSecond = -1;
video.addEventListener("timeupdate", () => {
  const second = Math.floor(video.currentTime);
  if (second !== lastSecond) {
    lastSecond = second;
    announce();
  }
});
video.addEventListener("seeked", announce);
video.addEventListener("play", announce);
video.addEventListener("ended", () => {
  status.textContent = "快版播放完成 · 可返回工作台操作事件";
});
video.addEventListener("error", () => {
  status.textContent = "影片載入失敗，請重新整理或下載觀看。";
});
document.addEventListener("visibilitychange", () => {
  if (document.hidden) video.pause();
});
