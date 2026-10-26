"""Shared helpers: thread-safe event recorder, invariant checkers, HTML generator.

Every synchronization program records each state change as an event.
write_html() embeds those events in a standalone page that replays them.
"""
import json
import threading
import time
from pathlib import Path


class Recorder:
    """Collects events. Its lock only protects the log, never the algorithm."""

    def __init__(self, actors, initial_state, n_forks=0):
        self._lock = threading.Lock()
        self._t0 = time.time()
        self.actors = list(actors)
        self.state = {a: initial_state for a in self.actors}
        self.forks = [None] * n_forks
        self.initial = dict(self.state)
        self.initial_forks = list(self.forks)
        self.events = []

    def emit(self, who, state, note, take=(), drop=()):
        with self._lock:
            self.state[who] = state
            for f in take:
                self.forks[f] = who
            for f in drop:
                self.forks[f] = None
            self.events.append({
                "t": round(time.time() - self._t0, 3), "who": who,
                "state": state, "note": note,
                "states": dict(self.state), "forks": list(self.forks)})


class RWGuard:
    """Independent check: a writer must never overlap a reader or another writer."""

    def __init__(self):
        self._l = threading.Lock()
        self.readers = self.writers = self.max_readers = self.violations = 0

    def enter_read(self):
        with self._l:
            self.readers += 1
            self.max_readers = max(self.max_readers, self.readers)
            if self.writers:
                self.violations += 1

    def leave_read(self):
        with self._l:
            self.readers -= 1

    def enter_write(self):
        with self._l:
            self.writers += 1
            if self.writers > 1 or self.readers:
                self.violations += 1

    def leave_write(self):
        with self._l:
            self.writers -= 1


class ForkGuard:
    """Independent check: two neighbouring philosophers never eat together."""

    def __init__(self, n):
        self._l = threading.Lock()
        self.n, self.eating, self.violations = n, set(), 0

    def enter(self, i):
        with self._l:
            if (i - 1) % self.n in self.eating or (i + 1) % self.n in self.eating:
                self.violations += 1
            self.eating.add(i)

    def leave(self, i):
        with self._l:
            self.eating.discard(i)


def print_trace(rec, count=8):
    print("First events of the trace:")
    for e in rec.events[:count]:
        print(f"  [{e['t']:6.2f}s] {e['who']:>3} -> {e['state']:<16} {e['note']}")


TEMPLATE = r"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>__TITLE__</title><style>
body{font-family:Segoe UI,Arial,sans-serif;background:#0f172a;color:#e2e8f0;margin:0;padding:20px;text-align:center}
h1{margin:0}.sub{color:#94a3b8}
button{padding:8px 16px;margin:4px;border:0;border-radius:6px;font-weight:bold;cursor:pointer}
.card{display:inline-block;width:110px;padding:12px;margin:6px;border-radius:10px;color:#fff}
#res{margin:10px;font-size:17px}
#log{max-width:780px;margin:10px auto;height:200px;overflow:auto;background:#1e293b;border-radius:8px;text-align:left;padding:8px;font:12px Consolas,monospace}
input[type=range]{width:260px;vertical-align:middle}
</style></head><body>
<h1>__TITLE__</h1><p class="sub">__SUB__</p>
<div id="view"></div><div id="res"></div>
<div><button id="b1" style="background:#22c55e">Start</button><button id="b2" style="background:#facc15">Pause</button><button id="b3" style="background:#fb7185">Reset</button>
Speed <input id="sp" type="range" min="1" max="10" value="3"></div>
<div>Timeline <input id="tl" type="range" min="0" max="0" value="0"></div>
<div id="log"></div>
<script>
const D=__DATA__,E=D.events,N=E.length,$=id=>document.getElementById(id);
const C={Idle:'#475569',Thinking:'#475569',Waiting:'#d97706',Hungry:'#d97706','Acquiring Forks':'#0284c7',Eating:'#16a34a',Reading:'#16a34a','Releasing Forks':'#7c3aed',Writing:'#dc2626',Finished:'#1e293b'};
let i=0,timer=null;
function drawRW(s){
  $('view').innerHTML=D.actors.map(a=>`<div class="card" style="background:${C[s[a]]}"><b>${a}</b><br>${s[a]}</div>`).join('');
  const rd=D.actors.filter(a=>s[a]==='Reading'),wr=D.actors.filter(a=>s[a]==='Writing'),wa=D.actors.filter(a=>s[a]==='Waiting');
  $('res').innerHTML='Shared resource: <b>'+(wr.length?'WRITE-LOCKED by '+wr[0]:rd.length?'READ by '+rd.join(', '):'FREE')+'</b> &nbsp; Waiting: '+(wa.join(', ')||'none');
}
function drawDP(s,f){
  let h='<svg viewBox="0 0 420 420" width="420"><circle cx="210" cy="210" r="95" fill="#1e293b"/>';
  D.actors.forEach((a,k)=>{const g=(-90+90*k)*Math.PI/180,x=210+150*Math.cos(g),y=210+150*Math.sin(g);
    h+=`<circle cx="${x}" cy="${y}" r="40" fill="${C[s[a]]}"/><text x="${x}" y="${y-2}" text-anchor="middle" fill="#fff" font-weight="bold">${a}</text><text x="${x}" y="${y+13}" text-anchor="middle" fill="#fff" font-size="10">${s[a]}</text>`;});
  f.forEach((o,k)=>{const g=(-90+90*k+45)*Math.PI/180,x=210+105*Math.cos(g),y=210+105*Math.sin(g);
    h+=`<rect x="${x-14}" y="${y-14}" width="28" height="28" rx="6" fill="${o?'#f97316':'#334155'}"/><text x="${x}" y="${y+4}" text-anchor="middle" fill="#fff" font-size="11">F${k+1}</text><text x="${x}" y="${y+27}" text-anchor="middle" fill="#cbd5e1" font-size="9">${o||'free'}</text>`;});
  $('view').innerHTML=h+'</svg>';
  const m={};D.actors.forEach(a=>m[a]=0);E.slice(0,i).forEach(e=>{if(e.state==='Eating')m[e.who]++;});
  $('res').innerHTML='Forks in use: '+f.filter(x=>x).length+'/'+f.length+' &nbsp; Meals: '+D.actors.map(a=>a+'='+m[a]).join(', ');
}
function render(){
  const s=i?E[i-1].states:D.initial,f=i?E[i-1].forks:D.initialForks;
  $('tl').max=N;$('tl').value=i;
  D.kind==='dp'?drawDP(s,f):drawRW(s);
  $('log').innerHTML=E.slice(0,i).map(e=>'['+e.t.toFixed(2)+'s] '+e.who+' -> '+e.state+': '+e.note).reverse().join('<br>');
}
function stop(){clearInterval(timer);timer=null;}
function step(){if(i<N){i++;render();}else stop();}
function play(){stop();if(i>=N)i=0;timer=setInterval(step,1100/$('sp').value);}
$('b1').onclick=play;$('b2').onclick=stop;
$('b3').onclick=()=>{stop();i=0;render();};
$('sp').oninput=()=>{if(timer)play();};
$('tl').oninput=()=>{stop();i=+$('tl').value;render();};
render();
</script></body></html>"""


def write_html(path, title, subtitle, rec, kind):
    """kind is 'rw' (readers-writers) or 'dp' (dining philosophers)."""
    data = {"kind": kind, "actors": rec.actors, "initial": rec.initial,
            "initialForks": rec.initial_forks, "events": rec.events}
    js = json.dumps(data).replace("</", "<\\/")
    html = TEMPLATE.replace("__TITLE__", title).replace("__SUB__", subtitle).replace("__DATA__", js)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    print(f"HTML written: {path}")
