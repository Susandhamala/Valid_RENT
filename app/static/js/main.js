/* ── SIDEBAR TOGGLE ─────────────────────────────────────────── */
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}
document.addEventListener('click', (e) => {
  const sb = document.getElementById('sidebar');
  const toggle = document.getElementById('menuToggle');
  if (sb && !sb.contains(e.target) && toggle && !toggle.contains(e.target)) {
    sb.classList.remove('open');
  }
});

/* ── TOAST NOTIFICATIONS ────────────────────────────────────── */
const TOAST_ICONS = {
  success: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M8 12l3 3 5-5"/></svg>`,
  error:   `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
  info:    `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="0.5" fill="#3b82f6"/></svg>`,
  warning: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><circle cx="12" cy="17" r="0.5" fill="#f59e0b"/></svg>`,
};

function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    ${TOAST_ICONS[type] || TOAST_ICONS.info}
    <div class="toast-body">${message}</div>
    <span class="toast-close" onclick="removeToast(this.parentElement)">&times;</span>
  `;
  container.appendChild(toast);
  setTimeout(() => removeToast(toast), duration);
}

function removeToast(el) {
  if (!el || !el.parentNode) return;
  el.style.animation = 'toastOut .25s ease forwards';
  setTimeout(() => el.remove(), 250);
}

// Flash messages from server
if (window.__flashMessages) {
  window.__flashMessages.forEach(([cat, msg]) => {
    const type = cat === 'error' ? 'error' : cat === 'success' ? 'success' : cat === 'warning' ? 'warning' : 'info';
    setTimeout(() => showToast(msg, type), 100);
  });
}

/* ── MODAL ──────────────────────────────────────────────────── */
function openModal(html) {
  document.getElementById('modalContent').innerHTML = html;
  document.getElementById('globalModal').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeModal() {
  document.getElementById('globalModal').classList.remove('open');
  document.body.style.overflow = '';
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

/* ── CONFIRM DIALOG ─────────────────────────────────────────── */
function confirmAction(message, formId) {
  openModal(`
    <div class="modal-title">Confirm Action</div>
    <div class="modal-body">${message}</div>
    <div class="modal-actions">
      <button class="btn btn-ghost" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" onclick="document.getElementById('${formId}').submit(); closeModal()">Confirm</button>
    </div>
  `);
}

/* ── CATEGORY SELECTOR ──────────────────────────────────────── */
function selectCategory(el, inputId) {
  document.querySelectorAll('.category-card').forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');
  const input = document.getElementById(inputId);
  if (input) input.value = el.dataset.value;
}

/* ── FILE UPLOAD PREVIEW ────────────────────────────────────── */
function initFileUpload(inputId, labelId) {
  const input = document.getElementById(inputId);
  const label = document.getElementById(labelId);
  if (!input || !label) return;
  input.addEventListener('change', () => {
    const file = input.files[0];
    label.textContent = file ? file.name : 'Choose file...';
  });
}

/* ── WEBCAM ─────────────────────────────────────────────────── */
let webcamStream = null;
let capturedPhoto = null;

async function startWebcam() {
  try {
    const video = document.getElementById('webcamVideo');
    webcamStream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
    video.srcObject = webcamStream;
    document.getElementById('startCamBtn').style.display = 'none';
    document.getElementById('captureBtn').style.display = 'inline-flex';
    document.getElementById('webcamVideo').style.display = 'block';
  } catch (err) {
    showToast('Camera access denied or unavailable: ' + err.message, 'error');
  }
}

function capturePhoto() {
  const video = document.getElementById('webcamVideo');
  const canvas = document.getElementById('webcamCanvas');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  capturedPhoto = canvas.toDataURL('image/jpeg', 0.85);

  const preview = document.getElementById('photoPreview');
  if (preview) {
    preview.src = capturedPhoto;
    preview.style.display = 'block';
  }

  // Stop stream
  if (webcamStream) { webcamStream.getTracks().forEach(t => t.stop()); webcamStream = null; }
  document.getElementById('webcamVideo').style.display = 'none';
  document.getElementById('captureBtn').style.display = 'none';
  document.getElementById('retakeBtn').style.display = 'inline-flex';
  document.getElementById('submitPhotoBtn').style.display = 'inline-flex';
  showToast('Photo captured! Review and submit.', 'success');
}

function retakePhoto() {
  capturedPhoto = null;
  document.getElementById('photoPreview').style.display = 'none';
  document.getElementById('retakeBtn').style.display = 'none';
  document.getElementById('submitPhotoBtn').style.display = 'none';
  document.getElementById('startCamBtn').style.display = 'inline-flex';
}

async function submitPhoto(agreementId) {
  const consent = document.getElementById('consentCheck').checked;
  if (!consent) { showToast('You must give consent before submitting.', 'warning'); return; }
  if (!capturedPhoto) { showToast('Please capture a photo first.', 'warning'); return; }

  const btn = document.getElementById('submitPhotoBtn');
  btn.disabled = true;
  btn.textContent = 'Saving...';

  try {
    const formData = new FormData();
    formData.append('photo_data', capturedPhoto);
    formData.append('consent', 'true');

    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    const headers = {};
    if (csrfToken) headers['X-CSRFToken'] = csrfToken;

    const res = await fetch(`/photos/save/${agreementId}`, { method: 'POST', headers, body: formData });
    const data = await res.json();

    if (data.success) {
      showToast(data.message, 'success');
      document.getElementById('photoStatus').textContent = '✓ Photo saved successfully';
      document.getElementById('photoStatus').className = 'badge badge-success mt-4';
      btn.style.display = 'none';
    } else {
      showToast(data.message, 'error');
      btn.disabled = false;
      btn.textContent = 'Submit Photo';
    }
  } catch (err) {
    showToast('Network error: ' + err.message, 'error');
    btn.disabled = false;
    btn.textContent = 'Submit Photo';
  }
}

/* ── SCROLL REVEAL ──────────────────────────────────────────── */
function initScrollAnimations() {
  // legacy pop-in support
  const legacyObserver = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) e.target.style.animationPlayState = 'running'; });
  }, { threshold: 0.1 });
  document.querySelectorAll('.pop-in-delay-1,.pop-in-delay-2,.pop-in-delay-3,.pop-in-delay-4,.pop-in-delay-5')
    .forEach(el => { el.style.animationPlayState = 'paused'; legacyObserver.observe(el); });

  // new .reveal system
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); revealObserver.unobserve(e.target); } });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });
  document.querySelectorAll('.reveal, .reveal-scale').forEach(el => revealObserver.observe(el));

  // auto-reveal cards, algo-cards, arch-boxes that don't have .reveal
  const autoObserver = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.style.opacity = '1';
        e.target.style.transform = 'translateY(0)';
        autoObserver.unobserve(e.target);
      }
    });
  }, { threshold: 0.06, rootMargin: '0px 0px -30px 0px' });
  document.querySelectorAll('.algo-card, .arch-box, .ref-wrap, .flow-step').forEach((el, i) => {
    el.style.cssText += `opacity:0;transform:translateY(18px);transition:opacity .45s ${i*0.05}s cubic-bezier(.22,1,.36,1),transform .45s ${i*0.05}s cubic-bezier(.22,1,.36,1)`;
    autoObserver.observe(el);
  });
}

/* ── BUTTON RIPPLE ──────────────────────────────────────────── */
function initRipple() {
  document.addEventListener('click', e => {
    const btn = e.target.closest('.btn');
    if (!btn) return;
    const r = document.createElement('span');
    r.className = 'ripple';
    const rect = btn.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    r.style.cssText = `width:${size}px;height:${size}px;left:${e.clientX-rect.left-size/2}px;top:${e.clientY-rect.top-size/2}px`;
    btn.appendChild(r);
    setTimeout(() => r.remove(), 500);
  });
}

/* ── TOPBAR SHADOW ON SCROLL ────────────────────────────────── */
function initTopbarScroll() {
  const tb = document.querySelector('.topbar');
  if (!tb) return;
  window.addEventListener('scroll', () => tb.classList.toggle('scrolled', window.scrollY > 8), { passive: true });
}

/* ── PASSWORD STRENGTH ──────────────────────────────────────── */
function initPasswordStrength(inputId, indicatorId, submitId) {
  const input = document.getElementById(inputId);
  const indicator = document.getElementById(indicatorId);
  const submit = document.getElementById(submitId);
  if (!input || !indicator) return;

  const rules = [
    { id: 'pw-len',     label: 'At least 8 characters',        test: v => v.length >= 8 },
    { id: 'pw-upper',   label: 'One uppercase letter (A-Z)',    test: v => /[A-Z]/.test(v) },
    { id: 'pw-lower',   label: 'One lowercase letter (a-z)',    test: v => /[a-z]/.test(v) },
    { id: 'pw-digit',   label: 'One number (0-9)',              test: v => /\d/.test(v) },
    { id: 'pw-special', label: 'One special character (!@#$%)', test: v => /[!@#$%^&*()\-_=+\[\]{};:'"\\|,.<>/?]/.test(v) },
  ];

  indicator.innerHTML = rules.map(r =>
    `<div id="${r.id}" style="font-size:.78rem;color:var(--gray-400);margin:2px 0;display:flex;align-items:center;gap:6px">
       <span class="pw-check">✗</span> ${r.label}
     </div>`
  ).join('');

  function update() {
    const val = input.value;
    let passed = 0;
    rules.forEach(r => {
      const ok = r.test(val);
      const el = document.getElementById(r.id);
      if (!el) return;
      el.style.color = ok ? '#22c55e' : 'var(--gray-400)';
      el.querySelector('.pw-check').textContent = ok ? '✓' : '✗';
      if (ok) passed++;
    });
    if (submit) submit.disabled = passed < rules.length;
  }

  input.addEventListener('input', update);
  update();
}

/* ── DATE RANGE VALIDATION ──────────────────────────────────── */
function initDateRangeValidation(startId, endId, errorId) {
  const startEl = document.getElementById(startId);
  const endEl = document.getElementById(endId);
  const errorEl = document.getElementById(errorId);
  if (!startEl || !endEl) return;

  const today = new Date().toISOString().split('T')[0];
  startEl.min = today;

  function validate() {
    const s = startEl.value;
    const e = endEl.value;
    if (s) {
      const nextDay = new Date(s);
      nextDay.setDate(nextDay.getDate() + 1);
      endEl.min = nextDay.toISOString().split('T')[0];
    }
    if (s && e && e <= s) {
      if (errorEl) { errorEl.textContent = 'End date must be after start date.'; errorEl.style.display = 'block'; }
      endEl.setCustomValidity('End date must be after start date.');
    } else {
      if (errorEl) errorEl.style.display = 'none';
      endEl.setCustomValidity('');
    }
    const sDate = new Date(s);
    const todayDate = new Date(today);
    if (s && sDate < todayDate) {
      if (errorEl) { errorEl.textContent = 'Start date cannot be in the past.'; errorEl.style.display = 'block'; }
      startEl.setCustomValidity('Start date cannot be in the past.');
    } else {
      startEl.setCustomValidity('');
    }
  }

  startEl.addEventListener('change', validate);
  endEl.addEventListener('change', validate);
  validate();
}

function _statusBadgeClass(status) {
  const map = {
    pending: 'badge-warning',
    under_review: 'badge-info',
    negotiating: 'badge-info',
    approved: 'badge-success',
    rejected: 'badge-danger',
    agreement_created: 'badge-success',
  };
  return map[status] || 'badge-info';
}

/* ── INIT ───────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initScrollAnimations();
  initRipple();
  initTopbarScroll();
  initFileUpload('agreementFile', 'fileLabel');
});
