async function load(){return fetch('./data.json').then(r=>r.json())}

function addTooltip(){
  let t=document.getElementById('chartTip');
  if(!t){t=document.createElement('div');t.id='chartTip';t.className='chart-tip';document.body.appendChild(t)}
  return t;
}

function drawBars(id,labels,vals,colors){
  const c=document.getElementById(id),x=c.getContext('2d');
  c.width=c.clientWidth;c.height=320;
  const w=c.width,h=c.height,p=38,m=Math.max(...vals,0.01);
  const bars=[];
  x.clearRect(0,0,w,h);x.strokeStyle='#30406f';x.strokeRect(p,p,w-2*p,h-2*p);
  vals.forEach((v,i)=>{const bw=(w-2*p)/vals.length*0.62,xx=p+(i+0.2)*(w-2*p)/vals.length,bh=(v/m)*(h-2*p),y=h-p-bh;
    x.fillStyle=colors?.[i%colors.length]||'#60a5fa';x.fillRect(xx,y,bw,bh);
    x.fillStyle='#dbeafe';x.font='12px sans-serif';x.fillText(labels[i],xx,h-p+16);x.fillText((v*100).toFixed(1)+'%',xx,y-6);
    bars.push({x:xx,y,w:bw,h:bh,label:labels[i],value:v});
  });
  const tip=addTooltip();
  c.onmousemove=(e)=>{const r=c.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;const b=bars.find(b=>mx>=b.x&&mx<=b.x+b.w&&my>=b.y&&my<=b.y+b.h);if(b){tip.style.display='block';tip.style.left=e.pageX+12+'px';tip.style.top=e.pageY+12+'px';tip.innerHTML=`<b>${b.label}</b><br>${(b.value*100).toFixed(2)}% switch rate`;}else tip.style.display='none';};
  c.onmouseleave=()=>tip.style.display='none';
}

function drawLine(id,vals){const c=document.getElementById(id),x=c.getContext('2d');c.width=c.clientWidth;c.height=320;const w=c.width,h=c.height,p=35,m=Math.max(...vals,1);x.clearRect(0,0,w,h);x.strokeStyle='#30406f';x.strokeRect(p,p,w-2*p,h-2*p);x.strokeStyle='#5eead4';x.lineWidth=3;x.beginPath();vals.forEach((v,i)=>{const xx=p+i*(w-2*p)/(vals.length-1),yy=h-p-(v/m)*(h-2*p);if(i===0)x.moveTo(xx,yy);else x.lineTo(xx,yy)});x.stroke();}

function chipGroup(id,items,onPick){
  const el=document.getElementById(id);
  el.innerHTML=items.map((s,i)=>`<button class='chip ${i===0?'active':''}' data-v='${s}'>${s}</button>`).join('');
  el.querySelectorAll('.chip').forEach(btn=>btn.onclick=()=>{el.querySelectorAll('.chip').forEach(b=>b.classList.remove('active'));btn.classList.add('active');onPick(btn.dataset.v)});
}
