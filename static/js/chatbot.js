/**
 * Apex Construction Estimating Chatbot
 * Client-side Controller: Handles chat messaging, file uploads, real-time scope tracking, and UI modals.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const chatStream = document.getElementById('chatStream');
  const chatInput = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');
  const attachFileBtn = document.getElementById('attachFileBtn');
  const fileUploadInput = document.getElementById('fileUploadInput');
  const typingIndicator = document.getElementById('typingIndicator');
  const contextReplies = document.getElementById('contextReplies');
  const quickPillsBar = document.getElementById('quickPillsBar');

  // Sidebar Elements
  const scopeSidebar = document.getElementById('scopeSidebar');
  const toggleTrackerBtn = document.getElementById('toggleTrackerBtn');
  const scopeProgressBar = document.getElementById('scopeProgressBar');
  const scopeCounter = document.getElementById('scopeCounter');
  const scopeType = document.getElementById('scopeType');
  const scopeSize = document.getElementById('scopeSize');
  const scopeTrades = document.getElementById('scopeTrades');
  const scopeLocation = document.getElementById('scopeLocation');
  const scopePlans = document.getElementById('scopePlans');
  const scopeBidDue = document.getElementById('scopeBidDue');
  const scopeContact = document.getElementById('scopeContact');
  const uploadedFilesList = document.getElementById('uploadedFilesList');
  const sidebarUploadBtn = document.getElementById('sidebarUploadBtn');
  const openSummaryBtn = document.getElementById('openSummaryBtn');
  const clearChatBtn = document.getElementById('clearChatBtn');

  // Modals
  const uploadModal = document.getElementById('uploadModal');
  const uploadModalBtn = document.getElementById('uploadModalBtn');
  const closeUploadModal = document.getElementById('closeUploadModal');
  const modalDropZone = document.getElementById('modalDropZone');
  const modalBrowseBtn = document.getElementById('modalBrowseBtn');
  const uploadProgressBox = document.getElementById('uploadProgressBox');
  const uploadProgressFill = document.getElementById('uploadProgressFill');
  const uploadStatusText = document.getElementById('uploadStatusText');

  const proposalModal = document.getElementById('proposalModal');
  const proposalModalBtn = document.getElementById('proposalModalBtn');
  const closeProposalModal = document.getElementById('closeProposalModal');
  const cancelProposalBtn = document.getElementById('cancelProposalBtn');
  const leadForm = document.getElementById('leadForm');

  const summaryModal = document.getElementById('summaryModal');
  const closeSummaryModal = document.getElementById('closeSummaryModal');
  const leadRawView = document.getElementById('leadRawView');
  const copyLeadBtn = document.getElementById('copyLeadBtn');
  const toastNotification = document.getElementById('toastNotification');

  // Session ID Management
  let sessionId = localStorage.getItem('apex_estimator_session_id');
  if (!sessionId) {
    sessionId = 'sess_' + Math.random().toString(36).substring(2, 11) + '_' + Date.now();
    localStorage.setItem('apex_estimator_session_id', sessionId);
  }

  let currentState = null;

  // --------------------------------------------------------------------------
  // Message Sending & Formatting gg
  // --------------------------------------------------------------------------

  function showToast(message, duration = 3000) {
    toastNotification.textContent = message;
    toastNotification.style.display = 'block';
    setTimeout(() => {
      toastNotification.style.display = 'none';
    }, duration);
  }

  function scrollToBottom() {
    chatStream.scrollTop = chatStream.scrollHeight;
  }

  // Store local object URLs so contractors can download blueprints directly on their PC
  const localFileUrls = window._localFileUrls || {};
  window._localFileUrls = localFileUrls;

  function formatMarkdown(text) {
    if (!text) return '';
    let parsed = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>');

    // Convert markdown download links: [text](url)
    parsed = parsed.replace(/\[(.*?)\]\((.*?)\)/g, (match, label, url) => {
      let actualUrl = url;
      for (const fn in localFileUrls) {
        if (label.includes(fn) || url.includes(fn)) {
          actualUrl = localFileUrls[fn];
          break;
        }
      }
      return `<a href="${actualUrl}" download target="_blank" class="chat-file-link"><i class="fa-solid fa-file-arrow-down"></i> ${label}</a>`;
    });

    // Convert bullet points
    parsed = parsed.replace(/• (.*?)(<br>|<\/p>|$)/g, '<li>$1</li>');
    if (parsed.includes('<li>')) {
      parsed = parsed.replace(/(<li>.*<\/li>)/g, '<ul>$1</ul>');
    }

    return `<p>${parsed}</p>`;
  }

  function appendUserMessage(text) {
    const row = document.createElement('div');
    row.className = 'message-row user-row';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble user-bubble';
    bubble.innerHTML = formatMarkdown(text);

    row.appendChild(bubble);
    chatStream.appendChild(row);
    scrollToBottom();
  }

  function appendBotMessage(text, meta = {}) {
    const row = document.createElement('div');
    row.className = 'message-row bot-row';

    const avatar = document.createElement('div');
    avatar.className = 'avatar bot-avatar-mini';
    avatar.innerHTML = '<i class="fa-solid fa-hard-hat"></i>';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble bot-bubble';
    bubble.innerHTML = formatMarkdown(text);

    row.appendChild(avatar);
    row.appendChild(bubble);
    chatStream.appendChild(row);
    scrollToBottom();
  }

  function setTyping(isTyping) {
    typingIndicator.style.display = isTyping ? 'flex' : 'none';
    if (isTyping) scrollToBottom();
  }

  function renderContextReplies(replies) {
    contextReplies.innerHTML = '';
    if (!replies || replies.length === 0) return;

    replies.forEach(reply => {
      const chip = document.createElement('button');
      chip.className = 'context-reply-chip';
      chip.textContent = reply;
      chip.addEventListener('click', () => {
        chatInput.value = reply;
        sendMessage();
      });
      contextReplies.appendChild(chip);
    });
  }

  // --------------------------------------------------------------------------
  // Scope Tracker Update
  // --------------------------------------------------------------------------

  function updateScopeTracker(state) {
    if (!state) return;
    currentState = state;

    scopeType.textContent = state.project_type || 'Pending';
    scopeSize.textContent = state.square_footage || 'Pending';
    scopeLocation.textContent = state.project_location || 'Pending';
    scopePlans.textContent = state.plans_available || 'Pending';
    scopeBidDue.textContent = state.bid_due_date || 'Standard (2–3 Days)';

    // Contact
    let contactInfo = [];
    if (state.name) contactInfo.push(state.name);
    if (state.email) contactInfo.push(state.email);
    if (state.phone) contactInfo.push(state.phone);
    scopeContact.textContent = contactInfo.length > 0 ? contactInfo.join(' • ') : 'Pending';

    // Trades
    scopeTrades.innerHTML = '';
    if (state.trades && state.trades.length > 0) {
      state.trades.forEach(t => {
        const tag = document.createElement('span');
        tag.className = 'trade-tag';
        tag.textContent = t;
        scopeTrades.appendChild(tag);
      });
    } else {
      scopeTrades.innerHTML = '<span class="empty-tag">None identified yet</span>';
    }

    // Uploaded Files (Clickable download links)
    uploadedFilesList.innerHTML = '';
    if (state.uploaded_files && state.uploaded_files.length > 0) {
      state.uploaded_files.forEach(f => {
        const li = document.createElement('li');
        const fn = typeof f === 'object' ? (f.filename || 'plan.pdf') : f;
        const dl = localFileUrls[fn] || (typeof f === 'object' && f.download_url ? f.download_url : `/api/download/${fn}`);
        li.innerHTML = `<a href="${dl}" download="${fn}" class="sidebar-file-link" title="Click to download ${fn}">
          <i class="fa-solid fa-file-pdf"></i>
          <span class="file-name-text">${fn}</span>
          <i class="fa-solid fa-arrow-down-to-bracket dl-btn-icon"></i>
        </a>`;
        uploadedFilesList.appendChild(li);
      });
    } else {
      uploadedFilesList.innerHTML = '<li class="no-files">No drawing sets attached yet</li>';
    }

    // Calculate Completion Score
    let points = 0;
    if (state.project_type) points += 20;
    if (state.trades && state.trades.length > 0) points += 25;
    if (state.square_footage) points += 15;
    if (state.plans_available && state.plans_available !== 'Pending') points += 20;
    if (state.email || state.phone) points += 20;

    scopeProgressBar.style.width = points + '%';
    scopeCounter.textContent = points + '% Qualified';
  }

  // --------------------------------------------------------------------------
  // API Calls: Chat & Reset
  // --------------------------------------------------------------------------

  async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    appendUserMessage(text);
    chatInput.value = '';
    chatInput.style.height = 'auto';
    contextReplies.innerHTML = '';

    setTyping(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId, state: currentState })
      });

      const data = await response.json();
      setTimeout(() => {
        setTyping(false);
        if (data.response) {
          appendBotMessage(data.response);
          renderContextReplies(data.quick_replies);
          updateScopeTracker(data.state);
        } else if (data.error) {
          appendBotMessage('Sorry, an error occurred: ' + data.error);
        }
      }, 350);
    } catch (err) {
      setTyping(false);
      appendBotMessage('Connection error. Please verify the server is running and try again.');
      console.error(err);
    }
  }

  async function resetSession() {
    if (!confirm('Start a fresh conversation? Current project details will be cleared.')) return;
    try {
      const response = await fetch('/api/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
      const data = await response.json();
      sessionId = data.session_id;
      localStorage.setItem('apex_estimator_session_id', sessionId);

      // Clear UI
      const welcomeCard = chatStream.querySelector('.bot-welcome-card');
      chatStream.innerHTML = '';
      if (welcomeCard) chatStream.appendChild(welcomeCard);
      contextReplies.innerHTML = '';

      updateScopeTracker({
        project_type: null,
        square_footage: null,
        trades: [],
        project_location: null,
        plans_available: null,
        bid_due_date: null,
        name: null,
        email: null,
        phone: null,
        uploaded_files: []
      });

      showToast('Conversation reset. Ready for a new project!');
    } catch (err) {
      console.error(err);
    }
  }

  // --------------------------------------------------------------------------
  // File Upload Handlers
  // --------------------------------------------------------------------------

  async function handleFileUpload(fileInput) {
    if (!fileInput) return;
    const files = (fileInput instanceof FileList || Array.isArray(fileInput)) ? Array.from(fileInput) : [fileInput];
    if (files.length === 0) return;

    uploadProgressBox.style.display = 'block';
    uploadProgressFill.style.width = '20%';
    uploadStatusText.textContent = files.length === 1
      ? `Uploading ${files[0].name}...`
      : `Uploading ${files.length} project drawing files...`;

    let totalBytes = 0;
    const metadataList = [];
    files.forEach(f => {
      totalBytes += f.size;
      const blobUrl = URL.createObjectURL(f);
      localFileUrls[f.name] = blobUrl;
      metadataList.push({
        filename: f.name,
        size_bytes: f.size,
        download_url: blobUrl
      });
    });

    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    const canSendFullFile = isLocal || totalBytes < 4 * 1024 * 1024;

    const formData = new FormData();
    formData.append('session_id', sessionId);
    if (currentState) {
      formData.append('state', JSON.stringify(currentState));
    }
    formData.append('files_metadata', JSON.stringify(metadataList));

    if (canSendFullFile) {
      files.forEach(f => formData.append('files', f));
    }

    try {
      uploadProgressFill.style.width = '65%';
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });

      uploadProgressFill.style.width = '100%';
      const data = await response.json();

      setTimeout(() => {
        uploadProgressBox.style.display = 'none';
        uploadProgressFill.style.width = '0%';
        uploadModal.style.display = 'none';

        if (data.response) {
          appendBotMessage(data.response);
          renderContextReplies(data.quick_replies);
          updateScopeTracker(data.state);
          const count = files.length;
          showToast(`${count} drawing file${count > 1 ? 's' : ''} uploaded successfully!`);
        } else {
          showToast(data.error || 'Upload error');
        }
      }, 400);
    } catch (err) {
      uploadProgressBox.style.display = 'none';
      showToast('File upload failed. Please try again.');
      console.error(err);
    }
  }

  // --------------------------------------------------------------------------
  // Event Listeners
  // --------------------------------------------------------------------------

  // Send message events
  sendBtn.addEventListener('click', sendMessage);
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Auto-resize chat textarea
  chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
  });

  // Quick prompt pills
  quickPillsBar.addEventListener('click', (e) => {
    const pill = e.target.closest('.pill');
    if (pill) {
      const text = pill.getAttribute('data-text');
      if (text) {
        chatInput.value = text;
        sendMessage();
      }
    }
  });

  // Clear chat
  clearChatBtn.addEventListener('click', resetSession);

  // Toggle scope sidebar on mobile/tablet
  toggleTrackerBtn.addEventListener('click', () => {
    scopeSidebar.classList.toggle('open');
  });

  // Native File Input
  attachFileBtn.addEventListener('click', () => {
    fileUploadInput.click();
  });

  fileUploadInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFileUpload(e.target.files);
    }
  });

  // Upload Modal triggers
  uploadModalBtn.addEventListener('click', () => {
    uploadModal.style.display = 'flex';
  });
  sidebarUploadBtn.addEventListener('click', () => {
    uploadModal.style.display = 'flex';
  });
  closeUploadModal.addEventListener('click', () => {
    uploadModal.style.display = 'none';
  });
  modalBrowseBtn.addEventListener('click', () => {
    fileUploadInput.click();
  });

  // Drag and Drop
  modalDropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    modalDropZone.classList.add('dragover');
  });
  modalDropZone.addEventListener('dragleave', () => {
    modalDropZone.classList.remove('dragover');
  });
  modalDropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    modalDropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files);
    }
  });

  // Proposal Modal
  proposalModalBtn.addEventListener('click', () => {
    // Pre-populate if state known
    if (currentState) {
      if (currentState.name) document.getElementById('leadName').value = currentState.name;
      if (currentState.company) document.getElementById('leadCompany').value = currentState.company;
      if (currentState.email) document.getElementById('leadEmail').value = currentState.email;
      if (currentState.phone) document.getElementById('leadPhone').value = currentState.phone;
      if (currentState.project_type) document.getElementById('leadProjType').value = currentState.project_type;
      if (currentState.square_footage) document.getElementById('leadSize').value = currentState.square_footage;
      if (currentState.bid_due_date) document.getElementById('leadBidDate').value = currentState.bid_due_date;
    }
    proposalModal.style.display = 'flex';
  });

  closeProposalModal.addEventListener('click', () => proposalModal.style.display = 'none');
  cancelProposalBtn.addEventListener('click', () => proposalModal.style.display = 'none');

  leadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      session_id: sessionId,
      name: document.getElementById('leadName').value.trim(),
      company: document.getElementById('leadCompany').value.trim(),
      email: document.getElementById('leadEmail').value.trim(),
      phone: document.getElementById('leadPhone').value.trim(),
      project_type: document.getElementById('leadProjType').value.trim(),
      square_footage: document.getElementById('leadSize').value.trim(),
      bid_due_date: document.getElementById('leadBidDate').value.trim()
    };

    try {
      const response = await fetch('/api/lead/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      proposalModal.style.display = 'none';

      if (data.response) {
        appendBotMessage(data.response);
        updateScopeTracker(data.state);
        showToast('Estimating proposal request submitted successfully!');
      }
    } catch (err) {
      console.error(err);
      showToast('Error submitting proposal request.');
    }
  });

  // Summary Modal View
  openSummaryBtn.addEventListener('click', async () => {
    try {
      const response = await fetch(`/api/state/${sessionId}`);
      const state = await response.json();
      currentState = state;

      let summaryText =
        '==================================================\n' +
        'NEW ESTIMATING LEAD SUMMARY\n' +
        '==================================================\n' +
        `Name: ${state.name || 'Not provided'}\n` +
        `Company: ${state.company || 'Not provided'}\n` +
        `Email: ${state.email || 'Not provided'}\n` +
        `Phone: ${state.phone || 'Not provided'}\n\n` +
        `Project Type: ${state.project_type || 'General Construction'}\n` +
        `Project Location: ${state.project_location || 'Not provided'}\n` +
        `Project Size: ${state.square_footage || 'Not provided'}\n` +
        `Stage: ${state.construction_stage || 'New Construction / Unspecified'}\n\n` +
        `Trades:\n${state.trades && state.trades.length ? state.trades.map(t => '- ' + t).join('\n') : 'None specified'}\n\n` +
        `Estimate Type: ${state.estimate_type || 'Detailed Cost Estimate / Bid Estimate'}\n` +
        `Plans Available: ${state.plans_available || 'Pending Client Review'}\n` +
        `Drawing Sheets: ${state.drawing_sheets || 'To be confirmed upon receipt'}\n` +
        `Bid Due Date: ${state.bid_due_date || 'Standard / Not urgent'}\n\n` +
        `Additional Requirements:\n${state.special_requirements && state.special_requirements.length ? state.special_requirements.map(s => '- ' + s).join('\n') : 'None'}\n\n` +
        `Uploaded Plans: ${state.uploaded_files && state.uploaded_files.length ? state.uploaded_files.join(', ') : 'None'}\n` +
        `Requested Turnaround: ${state.turnaround_required || 'Standard 2–3 Business Days'}\n` +
        '==================================================';

      leadRawView.textContent = summaryText;
      summaryModal.style.display = 'flex';
    } catch (err) {
      console.error(err);
      showToast('Error loading lead summary.');
    }
  });

  closeSummaryModal.addEventListener('click', () => summaryModal.style.display = 'none');

  copyLeadBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(leadRawView.textContent).then(() => {
      showToast('Lead summary copied to clipboard!');
    });
  });

  // Close modals on outside click
  window.addEventListener('click', (e) => {
    if (e.target === uploadModal) uploadModal.style.display = 'none';
    if (e.target === proposalModal) proposalModal.style.display = 'none';
    if (e.target === summaryModal) summaryModal.style.display = 'none';
  });

  // Initial State Fetch
  fetch(`/api/state/${sessionId}`)
    .then(res => res.json())
    .then(data => updateScopeTracker(data))
    .catch(() => {});
});
