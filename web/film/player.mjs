import {frameSvg,duration,chapters,chapterAt} from './scene.mjs';
const $=id=>document.getElementById(id),clock=s=>`${String(Math.floor(s/60)).padStart(2,'0')}:${String(Math.floor(s%60)).padStart(2,'0')}`;
let t=0,playing=false,previous=0,active=-1;
$('seek').max=duration;
chapters.forEach((c,i)=>{const b=document.createElement('button');b.textContent=`${String(i+1).padStart(2,'0')} ${c.title}`;b.onclick=()=>{t=c.at;draw()};$('chapters').append(b)});
function draw(){$('screen').innerHTML=frameSvg(!playing&&t===0?2.5:t);$('seek').value=t;$('clock').textContent=`${clock(t)} / ${clock(duration)}`;const i=chapterAt(t);if(i!==active){active=i;$('scene-status').textContent=`目前章節：${chapters[i].title}`;[...$('chapters').children].forEach((b,k)=>b.setAttribute('aria-current',String(i===k)))}}
function play(value){playing=value;$('play').textContent=playing?'暫停動畫':'播放動畫';previous=0;}
$('play').onclick=()=>{if(t>=duration)t=0;play(!playing);draw()};$('restart').onclick=()=>{t=0;play(false);draw()};$('seek').oninput=()=>{t=Number($('seek').value);draw()};
$('fullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen()}catch{$('scene-status').textContent='此瀏覽器不支援全螢幕，仍可使用播放器。'}};
document.addEventListener('fullscreenchange',()=>document.body.classList.toggle('fullscreen',Boolean(document.fullscreenElement)));
document.addEventListener('visibilitychange',()=>{if(document.hidden)play(false)});
window.addEventListener('keydown',e=>{if(['INPUT','SELECT','BUTTON','A'].includes(document.activeElement?.tagName))return;if(e.code==='Space'){e.preventDefault();play(!playing)}if(e.key==='ArrowRight'){t=Math.min(duration,t+5);draw()}if(e.key==='ArrowLeft'){t=Math.max(0,t-5);draw()}});
function loop(now){if(playing){if(previous)t=Math.min(duration,t+(now-previous)/1000*Number($('speed').value));previous=now;draw();if(t>=duration)play(false)}requestAnimationFrame(loop)}draw();requestAnimationFrame(loop);
// Explicit play only: also respects reduced-motion and prevents unexpected autoplay.
