// Polling-based updates (no WebSockets needed)
let cpsData = {};
let requestsData = [];
let messagesData = [];
let updateInterval = null;

// Initialize
function init() {
    fetchData();
    // Poll every 2 seconds
    updateInterval = setInterval(fetchData, 2000);
}

async function fetchData() {
    try {
        const response = await fetch('/api/state');
        const data = await response.json();
        
        cpsData = data.cps || {};
        requestsData = data.requests || [];
        messagesData = data.messages || [];
        
        renderAll();
    } catch (error) {
        console.error('Error fetching data:', error);
        addMessage('Error de conexión con el servidor', 'error');
    }
}

function renderAll() {
    renderCPGrid();
    renderRequestsTable();
}

function renderCPGrid() {
    const grid = document.getElementById('cpGrid');
    grid.innerHTML = '';
    
    // Ordenar CPs por ID
    const sortedCPs = Object.entries(cpsData).sort((a, b) => a[0].localeCompare(b[0]));
    
    sortedCPs.forEach(([cp_id, cp]) => {
        const panel = createCPPanel(cp_id, cp);
        grid.appendChild(panel);
    });
}

function createCPPanel(cp_id, cp) {
    const panel = document.createElement('div');
    panel.className = 'cp-panel';
    
    // Determinar el estado y color
    let status = 'disconnected';
    if (!cp.connected) {
        status = 'disconnected';
    } else if (cp.stopped_by_central) {
        status = 'out-of-order';
    } else if (!cp.ok) {
        status = 'fault';
    } else if (cp.charging) {
        status = 'charging';
    } else {
        status = 'available';
    }
    
    panel.classList.add(status);
    
    // Header
    const header = document.createElement('div');
    header.className = 'cp-header';
    header.textContent = cp_id;
    panel.appendChild(header);
    
    // Location
    const location = document.createElement('div');
    location.className = 'cp-location';
    location.textContent = cp.location || 'Unknown';
    panel.appendChild(location);
    
    // Status text
    const statusText = document.createElement('div');
    statusText.style.marginTop = '10px';
    if (!cp.connected) {
        statusText.textContent = 'DESCONECTADO';
        statusText.style.color = '#aaa';
    } else if (cp.stopped_by_central) {
        statusText.textContent = 'Out of Order';
        statusText.style.color = '#fff';
        statusText.style.fontWeight = 'bold';
    } else if (!cp.ok) {
        statusText.textContent = 'FALLO';
        statusText.style.color = '#fff';
        statusText.style.fontWeight = 'bold';
    } else if (cp.charging) {
        statusText.textContent = 'Cargando...';
        statusText.style.color = '#fff';
    } else {
        statusText.textContent = 'Disponible';
        statusText.style.color = '#fff';
    }
    panel.appendChild(statusText);
    
    // Info box si está cargando
    if (cp.charging && cp.driver_id) {
        const infoBox = document.createElement('div');
        infoBox.className = 'cp-info-box';
        
        const driverId = document.createElement('div');
        driverId.className = 'driver-id';
        driverId.textContent = `Driver ${cp.driver_id}`;
        infoBox.appendChild(driverId);
        
        const metrics = document.createElement('div');
        metrics.className = 'metrics';
        
        const kwLine = document.createElement('div');
        kwLine.className = 'metric-line';
        kwLine.innerHTML = `<span class="kw-value">${cp.last_kw.toFixed(2)}kWh</span>`;
        metrics.appendChild(kwLine);
        
        const eurLine = document.createElement('div');
        eurLine.className = 'metric-line';
        eurLine.innerHTML = `<span class="eur-value">${cp.euros_accum.toFixed(2)}€</span>`;
        metrics.appendChild(eurLine);
        
        infoBox.appendChild(metrics);
        panel.appendChild(infoBox);
    }
    
    return panel;
}

function renderRequestsTable() {
    const tbody = document.getElementById('requestsTable');
    tbody.innerHTML = '';
    
    // Mostrar las últimas 10 solicitudes
    const recentRequests = requestsData.slice(-10).reverse();
    
    recentRequests.forEach(req => {
        const row = document.createElement('tr');
        
        const dateCell = document.createElement('td');
        dateCell.textContent = req.date;
        row.appendChild(dateCell);
        
        const timeCell = document.createElement('td');
        timeCell.textContent = req.time;
        row.appendChild(timeCell);
        
        const driverCell = document.createElement('td');
        driverCell.textContent = req.driver_id;
        row.appendChild(driverCell);
        
        const cpCell = document.createElement('td');
        cpCell.textContent = req.cp_id;
        row.appendChild(cpCell);
        
        tbody.appendChild(row);
    });
}

function addMessage(text) {
    const now = new Date();
    const time = now.toLocaleTimeString('es-ES');
    
    messagesData.push({ time, text });
    
    // Mantener solo los últimos 50 mensajes
    if (messagesData.length > 50) {
        messagesData = messagesData.slice(-50);
    }
    
    renderMessages();
}

function renderMessages() {
    const container = document.getElementById('messagesContainer');
    container.innerHTML = '';
    
    // Mostrar solo los últimos 20 mensajes
    const recentMessages = messagesData.slice(-20);
    
    recentMessages.forEach(msg => {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message';
        
        const timeSpan = document.createElement('span');
        timeSpan.className = 'message-time';
        timeSpan.textContent = `[${msg.time}]`;
        msgDiv.appendChild(timeSpan);
        
        const textSpan = document.createElement('span');
        textSpan.className = 'message-text';
        textSpan.textContent = msg.text;
        msgDiv.appendChild(textSpan);
        
        container.appendChild(msgDiv);
    });
    
    // Auto-scroll al último mensaje
    container.scrollTop = container.scrollHeight;
}

// Iniciar la aplicación
init();
