async function simulateDeposit(e){
  e.preventDefault();
  const form = e.target;
  const tx_id = form.tx_id.value || Math.random().toString(36).slice(2);
  const amount = parseFloat(form.amount.value || '10');
  const email = prompt('Enter your account email (for demo webhook):');
  const payload = { tx_id, user_email: email, amount, status: 'confirmed' };
  try {
    const res = await fetch('/api/deposit/webhook', { method:'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
    const data = await res.json();
    if(data.ok){
      const bal = document.getElementById('balance');
      if(bal){ bal.textContent = (data.balance).toFixed(4) + ' USDT'; }
      alert('Credited +' + amount + ' USDT');
    } else {
      alert('Webhook failed: ' + (data.error || 'unknown'));
    }
  } catch(err){
    alert('Webhook error');
  }
  return false;
}
(function ensureTicker(){
const track = document.getElementById('flashTicker');
if(!track) return;
const clone = track.cloneNode(true);
track.parentNode.appendChild(clone);
})();

// Tabs
(function(){
  const btns = document.querySelectorAll('.tab-btn');
  const panels = document.querySelectorAll('.tab-panel');
  btns.forEach(b => b.addEventListener('click', () => {
    btns.forEach(x => x.classList.remove('active'));
    panels.forEach(p => p.classList.remove('active'));
    b.classList.add('active');
    const sel = document.getElementById(b.dataset.tab);
    if(sel) sel.classList.add('active');
  }));
})();

// Refresh balance
async function refreshBalance(){
  try{
    const res = await fetch('/api/balance');
    const data = await res.json();
    if(data.ok){
      const el = document.getElementById('balance');
      if(el) el.textContent = (data.balance).toFixed(4) + ' USDT';
    }
  }catch(e){}
}
// Show welcome modal after 5s for guests, once per session
(function(){
  var modal = document.getElementById('welcomeModal');
  if(!modal) return; // user is logged in (modal not rendered)
  if(sessionStorage.getItem('flashusdt_seen_modal')) return;
  setTimeout(function(){
    showWelcomeModal();
  }, 5000);
})();

function showWelcomeModal(){
  var modal = document.getElementById('welcomeModal');
  if(!modal) return;
  modal.classList.remove('hidden');
  modal.setAttribute('aria-hidden', 'false');
  sessionStorage.setItem('flashusdt_seen_modal','1');
}

function hideWelcomeModal(){
  var modal = document.getElementById('welcomeModal');
  if(!modal) return;
  modal.classList.add('hidden');
  modal.setAttribute('aria-hidden', 'true');
}
// Mobile Navigation Toggle
(function(){
  const toggle = document.getElementById('navToggle');
  const menu = document.getElementById('navMobile');
  
  if(toggle && menu){
    toggle.addEventListener('click', function(){
      // Toggle CSS classes
      toggle.classList.toggle('active');
      menu.classList.toggle('active');
    });

    // Close menu when clicking a link inside it
    const links = menu.querySelectorAll('a');
    links.forEach(link => {
      link.addEventListener('click', () => {
        toggle.classList.remove('active');
        menu.classList.remove('active');
      });
    });
  }
})();

// --- THEME & PASSWORD TOGGLES ---

// 1. Theme Toggle Logic
(function initTheme() {
  const savedTheme = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);
})();

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  updateThemeIcon(next);
}

function updateThemeIcon(theme) {
  const btn = document.getElementById('themeBtn');
  if (btn) {
    // Show Sun (☀️) for light mode, Moon (🌙) for dark mode
    btn.textContent = theme === 'dark' ? '☀️' : '🌙'; 
    btn.title = theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
  }
}

// 2. Password Visibility Toggle
function togglePassword(inputId, iconElement) {
  const input = document.getElementById(inputId);
  if (input.type === 'password') {
    input.type = 'text';
    iconElement.textContent = '👁️‍🗨️'; // Icon when showing
  } else {
    input.type = 'password';
    iconElement.textContent = '👁️'; // Icon when hiding
  }
}