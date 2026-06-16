/* =============================================================================
 * Fort Smith Public Library — "Marian" library magic assistant (PROTOTYPE)
 *
 * This is a non-functional concept demo. Everything below is SAMPLE DATA and a
 * small rules engine that *mimics* what a real LLM assistant would do once it is
 * wired to a read-only view of the library's Polaris ILS and live data feeds.
 *
 * No network calls, no real catalog, no customer data. Safe to open by double-
 * clicking index.html.
 * ========================================================================== */

const ASSISTANT_NAME = "Marian"; // working name — see README for alternates

/* ----------------------------------------------------------------------------
 * SAMPLE DATA  (stand-in for the real, read-only ILS view + feeds)
 * ------------------------------------------------------------------------- */

const BRANCHES = {
  main:    { name: "Main Library",        addr: "3201 Rogers Ave",  phone: "(479) 783-0229" },
  dallas:  { name: "Dallas Branch",       addr: "8100 Dallas St",   phone: "(479) 484-5650" },
  miller:  { name: "Miller Branch",       addr: "8701 S. 28th St",  phone: "(479) 646-3945" },
  windsor: { name: "Windsor Drive Branch",addr: "4701 Windsor Dr",  phone: "(479) 783-0229" },
};

const HOURS = {
  main:    { Mon:"9–8", Tue:"9–8", Wed:"9–8", Thu:"9–8", Fri:"9–5", Sat:"10–5", Sun:"1–5" },
  dallas:  { Mon:"9–5", Tue:"9–5", Wed:"9–5", Thu:"9–5", Fri:"9–5", Sat:"10–2", Sun:"Closed" },
  miller:  { Mon:"9–5", Tue:"9–5", Wed:"9–5", Thu:"9–5", Fri:"9–5", Sat:"10–2", Sun:"Closed" },
  windsor: { Mon:"9–5", Tue:"9–5", Wed:"9–5", Thu:"Closed", Fri:"9–5", Sat:"10–2", Sun:"Closed" },
};

// Reading levels: picture | earlyreader | middle | ya | adult
const CATALOG = [
  { t:"Fourth Wing", a:"Rebecca Yarros", lvl:"ya", subj:["fantasy","dragons","romantasy"],
    fmt:"Book", copies:{main:6,dallas:2,miller:1,windsor:1}, avail:{main:0,dallas:0,miller:0,windsor:0}, holds:23 },
  { t:"Iron Flame", a:"Rebecca Yarros", lvl:"ya", subj:["fantasy","dragons","romantasy"],
    fmt:"Book", copies:{main:5,dallas:2,miller:1,windsor:0}, avail:{main:1,dallas:0,miller:0,windsor:0}, holds:14 },
  { t:"The Women", a:"Kristin Hannah", lvl:"adult", subj:["historical fiction","vietnam","nurses"],
    fmt:"Book", copies:{main:8,dallas:3,miller:2,windsor:2}, avail:{main:2,dallas:1,miller:0,windsor:1}, holds:5 },
  { t:"Atomic Habits", a:"James Clear", lvl:"adult", subj:["self-help","productivity","psychology"],
    fmt:"Book", copies:{main:4,dallas:2,miller:1,windsor:1}, avail:{main:1,dallas:1,miller:1,windsor:0}, holds:0 },
  { t:"Educated", a:"Tara Westover", lvl:"adult", subj:["memoir","family","education"],
    fmt:"Book", copies:{main:3,dallas:1,miller:1,windsor:1}, avail:{main:1,dallas:0,miller:1,windsor:0}, holds:1 },
  { t:"Braiding Sweetgrass", a:"Robin Wall Kimmerer", lvl:"adult", subj:["nature","indigenous","essays","botany"],
    fmt:"Book", copies:{main:2,dallas:1,miller:1,windsor:1}, avail:{main:1,dallas:1,miller:0,windsor:1}, holds:0 },
  { t:"The Hunger Games", a:"Suzanne Collins", lvl:"ya", subj:["dystopia","adventure","survival"],
    fmt:"Book", copies:{main:5,dallas:2,miller:2,windsor:1}, avail:{main:2,dallas:1,miller:1,windsor:0}, holds:0 },
  { t:"Percy Jackson: The Lightning Thief", a:"Rick Riordan", lvl:"middle", subj:["mythology","adventure","fantasy"],
    fmt:"Book", copies:{main:4,dallas:2,miller:1,windsor:1}, avail:{main:2,dallas:0,miller:1,windsor:1}, holds:0 },
  { t:"Wonder", a:"R.J. Palacio", lvl:"middle", subj:["friendship","school","kindness"],
    fmt:"Book", copies:{main:3,dallas:1,miller:1,windsor:1}, avail:{main:1,dallas:1,miller:1,windsor:1}, holds:0 },
  { t:"Dog Man: The Scarlet Shedder", a:"Dav Pilkey", lvl:"earlyreader", subj:["graphic novel","humor","animals"],
    fmt:"Book", copies:{main:6,dallas:3,miller:2,windsor:2}, avail:{main:0,dallas:1,miller:0,windsor:1}, holds:8 },
  { t:"The Very Hungry Caterpillar", a:"Eric Carle", lvl:"picture", subj:["picture book","counting","nature"],
    fmt:"Book", copies:{main:5,dallas:3,miller:2,windsor:2}, avail:{main:3,dallas:2,miller:1,windsor:2}, holds:0 },
  { t:"Where the Wild Things Are", a:"Maurice Sendak", lvl:"picture", subj:["picture book","imagination","classic"],
    fmt:"Book", copies:{main:4,dallas:2,miller:1,windsor:1}, avail:{main:2,dallas:1,miller:1,windsor:0}, holds:0 },
  { t:"Hell on the Border: He Hanged Eighty-Eight Men", a:"S.W. Harman", lvl:"adult", subj:["local history","fort smith","judge parker","frontier"],
    fmt:"Book", copies:{main:1,dallas:0,miller:0,windsor:0}, avail:{main:1,dallas:0,miller:0,windsor:0}, holds:0, local:true },
];

const EVENTS = [
  { title:"Toddler Story Time", branch:"main", day:"Tue", time:"10:30 AM", aud:"Ages 1–3",
    desc:"Songs, rhymes, and picture books to build early literacy.", recurring:true },
  { title:"Baby Bounce & Rhyme", branch:"dallas", day:"Wed", time:"10:00 AM", aud:"Ages 0–18 mo",
    desc:"Lap-sit rhymes and bonding for our youngest readers.", recurring:true },
  { title:"Family Story Time", branch:"windsor", day:"Thu", time:"10:30 AM", aud:"All ages",
    desc:"Stories and a craft for the whole family.", recurring:true },
  { title:"LEGO Club", branch:"main", day:"Sat", time:"2:00 PM", aud:"Ages 5–12",
    desc:"Build-of-the-week challenges. Bricks provided.", recurring:true },
  { title:"Teen Anime & Manga Club", branch:"main", day:"Fri", time:"4:00 PM", aud:"Grades 6–12",
    desc:"Screenings, snacks, and manga swap.", recurring:true },
  { title:"Adult Book Club: \"The Women\"", branch:"main", day:"Thu", time:"6:00 PM", aud:"Adults",
    desc:"This month we discuss Kristin Hannah's \"The Women.\"", recurring:false },
  { title:"Genealogy Workshop: Researching Your Roots", branch:"main", day:"Sat", time:"10:30 AM", aud:"Adults",
    desc:"Hands-on intro to Ancestry Library Edition with a reference librarian.", recurring:false },
  { title:"Computer Basics 101", branch:"dallas", day:"Wed", time:"1:00 PM", aud:"Adults",
    desc:"Free one-on-one help with email, internet, and job applications.", recurring:false },
];

const DATABASES = [
  { name:"Ancestry Library Edition", topic:["genealogy","family history","ancestry","roots"],
    note:"Census, military, and vital records. In-library access.", tag:"Genealogy" },
  { name:"Gale In Context", topic:["homework","students","research","school","report","essay"],
    note:"Vetted articles for student research, by reading level.", tag:"Students" },
  { name:"Arkansas Traveler / Digital Library", topic:["arkansas","statewide","articles","magazines"],
    note:"Statewide databases free to AR residents.", tag:"Arkansas" },
  { name:"Consumer Reports", topic:["product","reviews","buy","car","appliance"],
    note:"Unbiased product ratings and buying guides.", tag:"Consumer" },
  { name:"Mango Languages", topic:["language","spanish","learn","french","esl"],
    note:"Self-paced courses in 70+ languages.", tag:"Learning" },
  { name:"LinkedIn Learning", topic:["career","job","skills","software","resume","business"],
    note:"Video courses for career and software skills.", tag:"Career" },
  { name:"HelpNow Online Tutoring", topic:["tutor","homework help","math","writing"],
    note:"Live tutors + writing lab, 1 PM–10 PM daily.", tag:"Students" },
  { name:"Libby & Hoopla", topic:["ebook","audiobook","movie","stream","digital"],
    note:"Borrow ebooks, audiobooks, and movies on your phone.", tag:"Digital" },
];

/* ----------------------------------------------------------------------------
 * SUGGESTED PROMPTS  (shown as chips)
 * ------------------------------------------------------------------------- */
const SUGGESTIONS = [
  "📍 Location & hours",
  "🕐 When's the next story time?",
  "🔎 Find me a book about dragons",
  "📚 Reserve \"The Women\" for pickup",
  "🧒 Book ideas for my 7-year-old",
  "🔄 Get a book from another library",
  "🗓️ What's happening this week?",
  "🔬 Help me research my family tree",
];

/* ----------------------------------------------------------------------------
 * TINY RULES ENGINE  (stands in for the LLM's intent routing)
 * ------------------------------------------------------------------------- */

function norm(s){ return s.toLowerCase(); }
function has(q, ...words){ return words.some(w => q.includes(w)); }

function detectBranch(q){
  if (has(q,"dallas")) return "dallas";
  if (has(q,"miller")) return "miller";
  if (has(q,"windsor")) return "windsor";
  if (has(q,"main","downtown","rogers")) return "main";
  return null;
}

function detectAge(q){
  let m = q.match(/(\d+)\s*[- ]?\s*(year|yr|yo)/);
  if (m) return parseInt(m[1],10);
  m = q.match(/(\d+)(st|nd|rd|th)\s*grad/);
  if (m) return parseInt(m[1],10) + 5; // grade -> ~age
  if (has(q,"toddler","preschool")) return 3;
  if (has(q,"teen","teenager","high school")) return 15;
  if (has(q,"kid","child","children")) return 8;
  return null;
}

function levelForAge(age){
  if (age <= 4) return "picture";
  if (age <= 7) return "earlyreader";
  if (age <= 11) return "middle";
  if (age <= 17) return "ya";
  return "adult";
}

function findBooks(q){
  const tokens = q.replace(/[^a-z0-9 ]/g," ").split(/\s+/).filter(w=>w.length>2);
  const stop = new Set(["the","and","for","book","books","about","find","need","want","reserve","hold","get","read","looking","library","please","with","that"]);
  const terms = tokens.filter(w=>!stop.has(w));
  const scored = CATALOG.map(b=>{
    const hay = (b.t+" "+b.a+" "+b.subj.join(" ")).toLowerCase();
    let score = 0;
    for (const term of terms){ if (hay.includes(term)) score += (b.t.toLowerCase().includes(term)?3:1); }
    return {b, score};
  }).filter(x=>x.score>0).sort((x,y)=>y.score-x.score);
  return scored.map(x=>x.b);
}

/* ----------------------------------------------------------------------------
 * RESPONSE BUILDERS  (return HTML strings for rich "cards")
 * ------------------------------------------------------------------------- */

function availabilityLine(b){
  const parts = Object.keys(BRANCHES).map(k=>{
    const a = b.avail[k]||0, c = b.copies[k]||0;
    if (c===0) return null;
    const cls = a>0 ? "ok" : "out";
    return `<span class="avail ${cls}">${BRANCHES[k].name.replace(" Library","").replace(" Branch","")}: ${a>0?a+" in":"out"}</span>`;
  }).filter(Boolean).join("");
  return `<div class="avail-row">${parts}</div>`;
}

function bookCard(b, {reserve=false}={}){
  const totalAvail = Object.values(b.avail).reduce((a,c)=>a+c,0);
  const badge = totalAvail>0
    ? `<span class="pill pill-ok">${totalAvail} available now</span>`
    : `<span class="pill pill-wait">Holds: ${b.holds} ahead · all copies out</span>`;
  const action = reserve
    ? (totalAvail>0
        ? `<button class="card-btn" onclick="placeHold('${esc(b.t)}')">Place hold &amp; pick a branch</button>`
        : `<button class="card-btn" onclick="placeHold('${esc(b.t)}')">Join the hold list (#${b.holds+1})</button>`)
    : `<button class="card-btn ghost" onclick="ask('Reserve \\'${esc(b.t)}\\' for pickup')">Reserve this</button>`;
  return `<div class="bookcard">
    <div class="cover" aria-hidden="true">${b.t.split(" ").slice(0,1)[0][0]}</div>
    <div class="bookmeta">
      <div class="booktitle">${esc(b.t)}</div>
      <div class="byline">${esc(b.a)} · ${b.fmt}</div>
      ${badge}
      ${availabilityLine(b)}
      ${action}
    </div>
  </div>`;
}

function esc(s){ return String(s).replace(/'/g,"\\'").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }

function hoursCard(branchKey){
  const keys = branchKey ? [branchKey] : Object.keys(BRANCHES);
  const cards = keys.map(k=>{
    const b = BRANCHES[k], h = HOURS[k];
    const rows = Object.entries(h).map(([d,v])=>`<tr><td>${d}</td><td>${v}</td></tr>`).join("");
    return `<div class="infocard">
      <div class="infohead">${b.name}</div>
      <div class="subtle">${b.addr} · ${b.phone}</div>
      <table class="hours">${rows}</table>
    </div>`;
  }).join("");
  return `<p>Here are the current hours${branchKey?` for the ${BRANCHES[branchKey].name}`:""}:</p>
    <div class="cardgrid">${cards}</div>
    <p class="subtle">Times shown as open–close. Want directions or to book a study room?</p>`;
}

function storyTimeCard(){
  const st = EVENTS.filter(e=>/story time|bounce/i.test(e.title));
  const rows = st.map(e=>`<div class="eventrow">
      <div class="when">${e.day} · ${e.time}</div>
      <div class="what"><strong>${esc(e.title)}</strong> — ${BRANCHES[e.branch].name}<br>
        <span class="subtle">${e.aud} · ${esc(e.desc)}</span></div>
    </div>`).join("");
  return `<p>The next story time is <strong>Tuesday at 10:30 AM</strong> (Toddler Story Time, Main Library). Here's the full weekly line-up:</p>
    <div class="eventlist">${rows}</div>
    <p class="subtle">Want me to add a reminder or show all kids' programs?</p>`;
}

function eventsCard(q){
  let list = EVENTS.slice();
  const br = detectBranch(q);
  if (br) list = list.filter(e=>e.branch===br);
  if (has(q,"kid","child","family","toddler","story")) list = list.filter(e=>/age|family|all ages|grades/i.test(e.aud));
  if (has(q,"teen")) list = list.filter(e=>/grade|teen/i.test(e.aud));
  if (has(q,"adult","book club","genealogy","computer")) list = list.filter(e=>/adult/i.test(e.aud));
  if (!list.length) list = EVENTS.slice(0,5);
  const rows = list.slice(0,6).map(e=>`<div class="eventrow">
      <div class="when">${e.day} · ${e.time}</div>
      <div class="what"><strong>${esc(e.title)}</strong> — ${BRANCHES[e.branch].name}<br>
        <span class="subtle">${e.aud} · ${esc(e.desc)}</span></div>
    </div>`).join("");
  return `<p>Here's what's coming up${br?` at the ${BRANCHES[br].name}`:" across the library"}:</p>
    <div class="eventlist">${rows}</div>
    <p class="subtle">I can filter by age group, branch, or day — just say the word.</p>`;
}

function suggestionsCard(age){
  const lvl = levelForAge(age);
  const picks = CATALOG.filter(b=>b.lvl===lvl).slice(0,4);
  const label = {picture:"picture books",earlyreader:"early readers",middle:"middle-grade",ya:"young adult",adult:"adult"}[lvl];
  const cards = picks.map(b=>bookCard(b)).join("");
  return `<p>For a ${age}-year-old I'd reach for <strong>${label}</strong>. A few that are popular right now:</p>
    <div class="cardstack">${cards}</div>
    <p class="subtle">Tell me what they love — animals, mythology, humor — and I'll tailor it. I keep suggestions age-appropriate and can flag content notes for caregivers.</p>`;
}

function databasesCard(q){
  let list = DATABASES.filter(d=>d.topic.some(t=>q.includes(t)));
  if (!list.length) list = DATABASES.slice(0,4);
  const cards = list.slice(0,4).map(d=>`<div class="dbcard">
      <div class="dbtag">${d.tag}</div>
      <div class="dbname">${esc(d.name)}</div>
      <div class="subtle">${esc(d.note)}</div>
      <a class="dblink" href="#" onclick="return false;">Open database →</a>
    </div>`).join("");
  const augment = `<div class="augment">
      <div class="infohead">➕ Augmented research <span class="beta">add-on feature</span></div>
      <p class="subtle">Beyond our licensed databases, I can pull a few vetted starting points from the open web and always show you the source so you can judge it:</p>
      <ul class="srclist">
        <li>📄 Library of Congress — primary-source guides</li>
        <li>📄 Smithsonian Learning Lab — images &amp; lesson sets</li>
        <li>📄 USA.gov / data.gov — official statistics</li>
      </ul>
      <p class="subtle tiny">Every answer is grounded in cited sources — no made-up facts.</p>
    </div>`;
  return `<p>Great research question. Here are the library databases that fit, free with your card:</p>
    <div class="cardgrid">${cards}</div>${augment}
    <p class="subtle">Want me to walk you through one, or set up a Genealogy Workshop seat?</p>`;
}

function illCard(title){
  return `<p>It looks like that title isn't in our collection right now. No problem — I can request it through <strong>Interlibrary Loan (ILL)</strong> from a partner library.</p>
    <div class="infocard">
      <div class="infohead">Interlibrary Loan request</div>
      <div class="ill-line"><span>Title</span><strong>${esc(title||"the item you described")}</strong></div>
      <div class="ill-line"><span>Estimated arrival</span><strong>7–14 days</strong></div>
      <div class="ill-line"><span>Pickup</span><strong>Main Library (or your home branch)</strong></div>
      <div class="ill-line"><span>Cost</span><strong>Free</strong></div>
      <button class="card-btn" onclick="confirmILL('${esc(title||"this item")}')">Submit ILL request</button>
    </div>
    <p class="subtle">I'll email you the moment it's ready to pick up.</p>`;
}

function holdConfirm(title, branchKey){
  const b = BRANCHES[branchKey] || BRANCHES.main;
  return `<p>✅ Done! I placed a hold on <strong>${esc(title)}</strong>.</p>
    <div class="infocard success">
      <div class="ill-line"><span>Pickup branch</span><strong>${b.name}</strong></div>
      <div class="ill-line"><span>Status</span><strong>Ready in ~1–2 days</strong></div>
      <div class="ill-line"><span>Hold shelf</span><strong>Under your last name</strong></div>
    </div>
    <p class="subtle">You'll get a text/email when it's on the hold shelf. Anything else?</p>`;
}

function intro(){
  return `<p>Hi! I'm <strong>${ASSISTANT_NAME}</strong>, the Fort Smith Public Library's assistant. I can help you find and reserve books, check what's available right now, plan a visit, discover events, or dig into research. Try one of the suggestions below, or just ask in your own words.</p>`;
}

/* ----------------------------------------------------------------------------
 * ROUTER  (maps a message to a response)
 * ------------------------------------------------------------------------- */

function route(message){
  const q = norm(message.trim());

  if (!q) return intro();

  // Reserve / hold flow
  if (has(q,"reserve","hold","check out","checkout","put on hold")){
    const books = findBooks(q);
    if (books.length){
      const b = books[0];
      return `<p>Here's what I found for that — placing a hold checks <em>real-time</em> availability across all four branches:</p>
        ${bookCard(b,{reserve:true})}`;
    }
    return illCard(null);
  }

  // Hours / location / plan a visit
  if (has(q,"hour","open","close","location","address","where","directions","phone","visit","parking")){
    return hoursCard(detectBranch(q));
  }

  // Story time
  if (has(q,"story time","storytime","story-time")){
    return storyTimeCard();
  }

  // Events / programs
  if (has(q,"event","program","class","club","happening","this week","calendar","workshop","activities")){
    return eventsCard(q);
  }

  // Age-appropriate suggestions
  const age = detectAge(q);
  if (age!==null && has(q,"suggest","recommend","idea","good book","what should","for my")){
    return suggestionsCard(age);
  }
  if (age!==null && has(q,"book","read")){
    return suggestionsCard(age);
  }

  // Research / databases
  if (has(q,"research","database","article","cite","genealogy","family tree","family history",
          "homework","tutor","language","career","resume","study")){
    return databasesCard(q);
  }

  // Interlibrary loan
  if (has(q,"interlibrary","ill","another library","other library","don't have","do you have","from a partner")){
    const books = findBooks(q);
    if (books.length){
      return `<p>Good news — we own that one:</p>${bookCard(books[0],{reserve:true})}`;
    }
    return illCard(null);
  }

  // Generic book search / recommendation
  if (has(q,"find","book","read","recommend","suggest","looking for","author","novel","about")){
    const books = findBooks(q);
    if (books.length){
      const cards = books.slice(0,4).map(b=>bookCard(b)).join("");
      return `<p>Here's what I found in the catalog (availability is live across all branches):</p>
        <div class="cardstack">${cards}</div>
        <p class="subtle">Say "reserve" plus a title and I'll place the hold for you.</p>`;
    }
    return illCard(null);
  }

  // Greeting / help / fallback
  if (has(q,"hi","hello","hey","help","what can you")) return intro();

  return `<p>I want to get this right. I can help with: <strong>finding &amp; reserving books</strong>, <strong>hours &amp; locations</strong>, <strong>events &amp; story times</strong>, <strong>kids' reading suggestions</strong>, <strong>interlibrary loan</strong>, and <strong>research help</strong>. Which of those is closest?</p>${intro()}`;
}

/* ----------------------------------------------------------------------------
 * UI WIRING
 * ------------------------------------------------------------------------- */

let pendingHoldTitle = null;

function el(id){ return document.getElementById(id); }

function openChat(){ el("chat").classList.add("open"); el("launcher").classList.add("hidden"); el("chat-input").focus(); }
function closeChat(){ el("chat").classList.remove("open"); el("launcher").classList.remove("hidden"); }

function addMsg(html, who){
  const wrap = document.createElement("div");
  wrap.className = "msg "+who;
  if (who==="bot"){
    wrap.innerHTML = `<div class="avatar">✨</div><div class="bubble">${html}</div>`;
  } else {
    wrap.innerHTML = `<div class="bubble">${html}</div>`;
  }
  el("messages").appendChild(wrap);
  el("messages").scrollTop = el("messages").scrollHeight;
  return wrap;
}

function typing(){
  const wrap = document.createElement("div");
  wrap.className = "msg bot typing";
  wrap.innerHTML = `<div class="avatar">✨</div><div class="bubble"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>`;
  el("messages").appendChild(wrap);
  el("messages").scrollTop = el("messages").scrollHeight;
  return wrap;
}

function ask(message){
  openChat();
  addMsg(escHtml(message), "user");
  el("chat-input").value = "";
  const t = typing();
  const delay = 550 + Math.random()*500;
  setTimeout(()=>{
    t.remove();
    addMsg(route(message), "bot");
  }, delay);
}

function escHtml(s){ return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }

function submitInput(e){
  e.preventDefault();
  const v = el("chat-input").value.trim();
  if (v) ask(v);
}

// hold flow: choose pickup branch via a quick prompt
function placeHold(title){
  pendingHoldTitle = title;
  addMsg(`<p>Which branch would you like to pick up <strong>${escHtml(title)}</strong> from?</p>
    <div class="chiprow">
      ${Object.keys(BRANCHES).map(k=>`<button class="chip" onclick="finishHold('${k}')">${BRANCHES[k].name}</button>`).join("")}
    </div>`, "bot");
}
function finishHold(branchKey){
  addMsg(holdConfirm(pendingHoldTitle, branchKey), "bot");
  pendingHoldTitle = null;
}
function confirmILL(title){
  addMsg(`<p>📨 Your interlibrary loan request for <strong>${escHtml(title)}</strong> is in. I'll notify you when it arrives (usually 7–14 days). Reference #ILL-${Math.floor(1000+Math.random()*9000)}.</p>`, "bot");
}

function renderSuggestions(){
  el("suggestions").innerHTML = SUGGESTIONS.map(s=>`<button class="chip" onclick="ask('${s.replace(/'/g,"\\'")}')">${s}</button>`).join("");
  el("hero-suggestions").innerHTML = SUGGESTIONS.slice(0,4).map(s=>`<button class="chip light" onclick="ask('${s.replace(/'/g,"\\'")}')">${s}</button>`).join("");
}

window.addEventListener("DOMContentLoaded", ()=>{
  renderSuggestions();
  addMsg(intro(), "bot");
  el("chat-form").addEventListener("submit", submitInput);
  el("assistant-name").textContent = ASSISTANT_NAME;
  el("assistant-name2").textContent = ASSISTANT_NAME;
});
