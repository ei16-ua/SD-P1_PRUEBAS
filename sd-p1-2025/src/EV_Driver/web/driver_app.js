// State
let driverState = {
    driver_id: '',
    charging: false,
    current_cp: null,
    last_kw: 0.0,
    last_eur: 0.0,
    last_kwh: 0.0,
    finished_waiting_payment: false
};

let availableCPs = [];
let lastMessageCount = 0;
let targetKwh = 0; // Objetivo de carga en kWh
let currentCPMaxKw = 0; // Potencia máxima del CP actual
let startTime = null; // Momento de inicio de carga

// DOM Elements
const driverIdEl = document.getElementById('driverId');
const statusValueEl = document.getElementById('statusValue');
const currentCPEl = document.getElementById('currentCP');
const powerValueEl = document.getElementById('powerValue');
const consumptionValueEl = document.getElementById('consumptionValue');
const costValueEl = document.getElementById('costValue');
const chargingPanelEl = document.getElementById('chargingPanel');
const chargingCPEl = document.getElementById('chargingCP');
const chargingKWEl = document.getElementById('chargingKW');
const chargingKWHEl = document.getElementById('chargingKWH');
const chargingEUREl = document.getElementById('chargingEUR');
const cpSelectEl = document.getElementById('cpSelect');
const cpInputEl = document.getElementById('cpInput');
const requestBtnEl = document.getElementById('requestBtn');
const finishBtnEl = document.getElementById('finishBtn');
const payBtnEl = document.getElementById('payBtn');
const messagesLogEl = document.getElementById('messagesLog');
const targetKwhInputEl = document.getElementById('targetKwhInput');
const progressSectionEl = document.getElementById('progressSection');
const progressTextEl = document.getElementById('progressText');
const progressPercentEl = document.getElementById('progressPercent');
const progressFillEl = document.getElementById('progressFill');
const timeEstimateEl = document.getElementById('timeEstimate');

// Initialize
function init() {
    setupEventListeners();
    fetchData();
    // Poll every 2 seconds
    setInterval(fetchData, 2000);
}

// Fetch data from server
async function fetchData() {
    try {
        const response = await fetch('/api/state');
        const data = await response.json();
        
        updateState(data.state);
        
        if (data.cps) {
            updateCPList(data.cps);
        }
        
        // Update messages if there are new ones
        if (data.messages && data.messages.length > lastMessageCount) {
            for (let i = lastMessageCount; i < data.messages.length; i++) {
                const msg = data.messages[i];
                addMessage(msg.text, msg.level || 'info');
            }
            lastMessageCount = data.messages.length;
        }
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

function updateState(state) {
    driverState = state;
    driverIdEl.textContent = state.driver_id;
    
    // Debug: mostrar valores recibidos
    console.log('State received:', {
        charging: state.charging,
        last_kw: state.last_kw,
        last_kwh: state.last_kwh,
        last_eur: state.last_eur
    });
    
    if (state.charging) {
        // Iniciar timer si es la primera vez
        if (!startTime) {
            startTime = Date.now();
        }
        
        // ESTADO: CARGANDO
        statusValueEl.textContent = '🔌 CARGANDO';
        statusValueEl.style.color = '#0f0';
        currentCPEl.textContent = state.current_cp || '-';
        powerValueEl.textContent = `${state.last_kw.toFixed(2)} kW`;
        consumptionValueEl.textContent = `${state.last_kwh.toFixed(3)} kWh`;
        costValueEl.textContent = `${state.last_eur.toFixed(4)} €`;
        
        // Show charging panel
        chargingPanelEl.classList.remove('hidden');
        chargingCPEl.textContent = state.current_cp;
        chargingKWEl.textContent = state.last_kw.toFixed(2);
        chargingKWHEl.textContent = state.last_kwh.toFixed(3);
        chargingEUREl.textContent = state.last_eur.toFixed(4);
        
        // Actualizar progreso si hay objetivo
        if (targetKwh > 0) {
            updateProgress(state.last_kwh, state.last_kw);
        }
        
        // Show FINISH button only
        finishBtnEl.classList.remove('hidden');
        payBtnEl.classList.add('hidden');
        requestBtnEl.disabled = true;
        cpSelectEl.disabled = true;
        cpInputEl.disabled = true;
        targetKwhInputEl.disabled = true;
        
    } else if (state.finished_waiting_payment) {
        // ESTADO: ESPERANDO PAGO
        statusValueEl.textContent = '⏸️ ESPERANDO PAGO';
        statusValueEl.style.color = '#ff0';
        currentCPEl.textContent = state.current_cp || '-';
        powerValueEl.textContent = `${state.last_kw.toFixed(2)} kW`;
        consumptionValueEl.textContent = `${state.last_kwh.toFixed(3)} kWh`;
        costValueEl.textContent = `${state.last_eur.toFixed(4)} €`;
        
        // Show charging panel with final values
        chargingPanelEl.classList.remove('hidden');
        chargingCPEl.textContent = state.current_cp;
        chargingKWEl.textContent = state.last_kw.toFixed(2);
        chargingKWHEl.textContent = state.last_kwh.toFixed(3);
        chargingEUREl.textContent = state.last_eur.toFixed(4);
        
        // Mostrar progreso final si hay objetivo
        if (targetKwh > 0) {
            updateProgress(state.last_kwh, 0);
        }
        
        // Show PAY button only
        finishBtnEl.classList.add('hidden');
        payBtnEl.classList.remove('hidden');
        requestBtnEl.disabled = true;
        cpSelectEl.disabled = true;
        cpInputEl.disabled = true;
        targetKwhInputEl.disabled = true;
        
    } else {
        // ESTADO: EN ESPERA
        statusValueEl.textContent = '⏸️ EN ESPERA';
        statusValueEl.style.color = '#fff';
        currentCPEl.textContent = '-';
        powerValueEl.textContent = '0.00 kW';
        consumptionValueEl.textContent = '0.000 kWh';
        costValueEl.textContent = '0.0000 €';
        
        // Hide charging panel
        chargingPanelEl.classList.add('hidden');
        progressSectionEl.classList.add('hidden');
        
        // Resetear variables
        targetKwh = 0;
        startTime = null;
        
        // Hide both action buttons, enable request
        finishBtnEl.classList.add('hidden');
        payBtnEl.classList.add('hidden');
        requestBtnEl.disabled = false;
        cpSelectEl.disabled = false;
        cpInputEl.disabled = false;
        targetKwhInputEl.disabled = false;
    }
}

function updateTelemetry(kw, eur) {
    driverState.last_kw = kw;
    driverState.last_eur = eur;
    
    powerValueEl.textContent = `${kw.toFixed(2)} kW`;
    costValueEl.textContent = `${eur.toFixed(4)} €`;
    
    if (chargingKWEl && chargingEUREl) {
        chargingKWEl.textContent = kw.toFixed(2);
        chargingEUREl.textContent = eur.toFixed(4);
    }
}

function updateProgress(currentKwh, currentKw) {
    if (!targetKwh || targetKwh <= 0) {
        progressSectionEl.classList.add('hidden');
        return;
    }
    
    progressSectionEl.classList.remove('hidden');
    
    // Calcular porcentaje
    const percent = Math.min((currentKwh / targetKwh) * 100, 100);
    
    // Actualizar barra
    progressFillEl.style.width = `${percent}%`;
    progressTextEl.textContent = `${currentKwh.toFixed(3)} / ${targetKwh.toFixed(1)} kWh`;
    progressPercentEl.textContent = `${percent.toFixed(1)}%`;
    
    // Calcular tiempo restante
    if (currentKw > 0 && currentKwh < targetKwh) {
        const remainingKwh = targetKwh - currentKwh;
        const hoursRemaining = remainingKwh / currentKw;
        const minutesRemaining = Math.ceil(hoursRemaining * 60);
        
        if (minutesRemaining < 60) {
            timeEstimateEl.textContent = `⏱️ Tiempo restante: ${minutesRemaining} minutos`;
        } else {
            const hours = Math.floor(minutesRemaining / 60);
            const mins = minutesRemaining % 60;
            timeEstimateEl.textContent = `⏱️ Tiempo restante: ${hours}h ${mins}min`;
        }
    } else if (currentKwh >= targetKwh) {
        timeEstimateEl.textContent = '✅ Objetivo alcanzado';
        progressFillEl.style.background = 'linear-gradient(90deg, #38ef7d 0%, #11998e 100%)';
    } else {
        timeEstimateEl.textContent = '⏱️ Calculando tiempo...';
    }
}

function updateCPList(cps) {
    availableCPs = cps;
    
    // Save current selection
    const currentSelection = cpSelectEl.value;
    
    // Clear and repopulate select
    cpSelectEl.innerHTML = '<option value="">-- Selecciona un CP --</option>';
    
    cps.forEach(cp => {
        const option = document.createElement('option');
        option.value = cp.cp_id;
        
        let statusText = '';
        if (!cp.connected) {
            statusText = ' [DESCONECTADO]';
            option.disabled = true;
        } else if (cp.stopped_by_central) {
            statusText = ' [OUT OF ORDER]';
            option.disabled = true;
        } else if (!cp.ok) {
            statusText = ' [FALLO]';
            option.disabled = true;
        } else if (cp.charging) {
            statusText = ' [OCUPADO]';
            option.disabled = true;
        } else {
            statusText = ` [DISPONIBLE - ${cp.kw_max}kW - ${cp.price_eur_kwh}€/kWh]`;
        }
        
        option.textContent = `${cp.cp_id} - ${cp.location}${statusText}`;
        cpSelectEl.appendChild(option);
    });
    
    // Restore previous selection if it still exists
    if (currentSelection) {
        cpSelectEl.value = currentSelection;
    }
}

function setupEventListeners() {
    requestBtnEl.addEventListener('click', handleRequestService);
    finishBtnEl.addEventListener('click', handleFinishService);
    payBtnEl.addEventListener('click', handlePayService);
}

async function handleRequestService() {
    // Priorizar input manual sobre select
    let cpId = cpInputEl.value.trim().toUpperCase();
    
    if (!cpId) {
        cpId = cpSelectEl.value;
    }
    
    if (!cpId) {
        addMessage('Por favor selecciona un CP o escribe su ID', 'warning');
        return;
    }
    
    // Capturar objetivo de carga (opcional)
    const targetInput = parseFloat(targetKwhInputEl.value);
    if (targetInput && targetInput > 0) {
        targetKwh = targetInput;
        
        // Obtener potencia máxima del CP
        const selectedCP = availableCPs.find(cp => cp.cp_id === cpId);
        if (selectedCP && selectedCP.kw_max) {
            currentCPMaxKw = selectedCP.kw_max;
            
            // Calcular tiempo estimado inicial
            const estimatedHours = targetKwh / currentCPMaxKw;
            const estimatedMinutes = Math.ceil(estimatedHours * 60);
            
            // Calcular coste estimado
            const estimatedCost = targetKwh * selectedCP.price_eur_kwh;
            
            let timeStr = '';
            if (estimatedMinutes < 60) {
                timeStr = `~${estimatedMinutes} min`;
            } else {
                const hours = Math.floor(estimatedMinutes / 60);
                const mins = estimatedMinutes % 60;
                timeStr = `~${hours}h ${mins}min`;
            }
            
            addMessage(`🎯 Objetivo: ${targetKwh} kWh | Tiempo: ${timeStr} | Coste estimado: ~${estimatedCost.toFixed(2)}€`, 'info');
        } else {
            addMessage(`🎯 Objetivo de carga establecido: ${targetKwh} kWh`, 'info');
        }
    } else {
        targetKwh = 0;
    }
    
    requestBtnEl.disabled = true;
    requestBtnEl.textContent = 'SOLICITANDO...';
    
    try {
        const response = await fetch('/api/request', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ cp_id: cpId })
        });
        
        const result = await response.json();
        
        if (result.success) {
            addMessage(`✅ Autorización concedida para ${cpId}`, 'success');
            cpInputEl.value = '';  // Limpiar input manual
        } else {
            addMessage(`❌ Autorización denegada: ${result.reason}`, 'error');
            requestBtnEl.disabled = false;
            requestBtnEl.textContent = 'REQUEST SERVICE';
            targetKwh = 0; // Resetear objetivo si falla
        }
    } catch (error) {
        console.error('Error requesting service:', error);
        addMessage('Error al solicitar servicio', 'error');
        requestBtnEl.disabled = false;
        requestBtnEl.textContent = 'REQUEST SERVICE';
        targetKwh = 0;
    }
}

async function handleFinishService() {
    if (!driverState.current_cp) {
        addMessage('No hay ningún servicio activo', 'warning');
        return;
    }
    
    finishBtnEl.disabled = true;
    finishBtnEl.textContent = 'DETENIENDO...';
    
    try {
        const response = await fetch('/api/finish', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ cp_id: driverState.current_cp })
        });
        
        const result = await response.json();
        
        if (result.success) {
            addMessage(`✅ Carga detenida. Total: ${result.total_kw.toFixed(2)} kW, ${result.total_eur.toFixed(4)} €`, 'success');
        } else {
            addMessage('❌ Error al detener carga', 'error');
        }
    } catch (error) {
        console.error('Error finishing service:', error);
        addMessage('Error al detener carga', 'error');
    } finally {
        finishBtnEl.disabled = false;
        finishBtnEl.textContent = '🛑 DETENER CARGA';
    }
}

async function handlePayService() {
    payBtnEl.disabled = true;
    payBtnEl.textContent = 'PROCESANDO...';
    
    try {
        const response = await fetch('/api/pay', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            addMessage('💳 Pago confirmado - Sesión completada', 'success');
        } else {
            addMessage('❌ Error al procesar pago', 'error');
        }
    } catch (error) {
        console.error('Error paying:', error);
        addMessage('Error al procesar pago', 'error');
    } finally {
        payBtnEl.disabled = false;
        payBtnEl.textContent = '💳 PAGAR Y SALIR';
        requestBtnEl.textContent = 'REQUEST SERVICE';
    }
}

function addMessage(text, level = 'info') {
    const now = new Date();
    const time = now.toLocaleTimeString('es-ES');
    
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message';
    
    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-time';
    timeSpan.textContent = `[${time}]`;
    
    const textSpan = document.createElement('span');
    textSpan.className = `message-${level}`;
    textSpan.textContent = text;
    
    msgDiv.appendChild(timeSpan);
    msgDiv.appendChild(textSpan);
    
    messagesLogEl.appendChild(msgDiv);
    messagesLogEl.scrollTop = messagesLogEl.scrollHeight;
    
    // Keep only last 50 messages
    while (messagesLogEl.children.length > 50) {
        messagesLogEl.removeChild(messagesLogEl.firstChild);
    }
}

// Start the app
init();
