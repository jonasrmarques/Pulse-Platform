function getCSRFToken() {
    const name = "csrftoken=";
    const decodedCookie = decodeURIComponent(document.cookie);
    const cookies = decodedCookie.split(";");

    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name)) {
            return cookie.substring(name.length);
        }
    }
    return null;
}
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('toggleSidebar');
    const content = document.querySelector('.content');
    
    // Adicionar title aos links para tooltip
    const sidebarLinks = sidebar.querySelectorAll('nav a');
    sidebarLinks.forEach(link => {
        const text = link.querySelector('.link-text').textContent;
        link.setAttribute('title', text);
    });
    
    // Verificar estado salvo no localStorage
    const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    
    if (isCollapsed) {
        sidebar.classList.add('collapsed');
    } else {
        sidebar.classList.remove('collapsed');
    }
    
    toggleBtn.addEventListener('click', function() {
        const isNowCollapsed = !sidebar.classList.contains('collapsed');
        sidebar.classList.toggle('collapsed');
        
        localStorage.setItem('sidebarCollapsed', isNowCollapsed);
        
        // Remover tooltip se estiver visível
        const activeTooltip = document.querySelector('nav a:hover::after');
        if (activeTooltip) {
            activeTooltip.style.display = 'none';
        }
    });
    
    // Ajustar para mobile
    function handleResponsive() {
        if (window.innerWidth < 768) {
            if (!sidebar.classList.contains('collapsed')) {
                sidebar.classList.add('collapsed');
                localStorage.setItem('sidebarCollapsed', 'true');
            }
        }
    }
    
    // Verificar na inicialização
    handleResponsive();
    
    // Ajustar ao redimensionar (com debounce)
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(handleResponsive, 250);
    });

    initializeChatbot();
});

async function handleLogout(event) {
    event.preventDefault();

    console.log("clicou no logout"); // 👈 DEBUG

    const refresh = localStorage.getItem("refresh_token");

    try {
        await fetch("/api/logout/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + localStorage.getItem("access_token"),
                "X-CSRFToken": getCSRFToken()
            },
            body: JSON.stringify({ refresh })
        });
    } catch (e) {
        console.error("Erro no logout", e);
    } finally {
        localStorage.clear();
        window.location.replace("/");
    }
}



function initializeChatbot() {
    const toggleBtn = document.getElementById('chatbotToggleBtn');
    const closeBtn = document.getElementById('chatbotCloseBtn');
    const chatWindow = document.getElementById('chatbotWindow');
    const chatInput = document.getElementById('chatInput');

    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleChat);
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', toggleChat);
    }

    // Fechar ao clicar fora (opcional)
    document.addEventListener('click', function(event) {
        if (chatWindow && chatWindow.classList.contains('open')) {
            if (!chatWindow.contains(event.target) && !toggleBtn.contains(event.target)) {
                chatWindow.classList.remove('open');
            }
        }
    });

    // Enviar com Enter
    if (chatInput) {
        chatInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                sendMessage();
            }
        });
    }

    // Adicionar mensagem de boas-vindas se não houver mensagens
    const messagesContainer = document.getElementById('chatMessages');
    if (messagesContainer && messagesContainer.children.length === 0) {
        addBotMessage("Olá! Sou o assistente da Pulse. Como posso ajudar você hoje?");
    }
}

function toggleChat() {
    const chatWindow = document.getElementById('chatbotWindow');
    const chatInput = document.getElementById('chatInput');
    
    chatWindow.classList.toggle('open');
    
    if (chatWindow.classList.contains('open')) {
        chatInput.focus();
    }
}

// Função para adicionar mensagem do bot
function addBotMessage(text) {
    const messages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message bot';
    messageDiv.innerHTML = `
        <div class="sender-name">Assistente Pulse</div>
        <div class="message-content">
            <i class="fas fa-robot me-2"></i>
            <span>${text}</span>
        </div>
    `;
    messages.appendChild(messageDiv);
    messages.scrollTop = messages.scrollHeight;
}

// Função para adicionar mensagem do usuário
function addUserMessage(text) {
    const messages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message user';
    messageDiv.innerHTML = `
        <div class="sender-name">Você</div>
        <div class="message-content">${text}</div>
    `;
    messages.appendChild(messageDiv);
    messages.scrollTop = messages.scrollHeight;
}

// Mostrar indicador de digitação
function showTypingIndicator() {
    const messages = document.getElementById('chatMessages');
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.id = 'typingIndicator';
    indicator.innerHTML = '<span></span><span></span><span></span>';
    messages.appendChild(indicator);
    messages.scrollTop = messages.scrollHeight;
}

// Remover indicador de digitação
function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

// Sua função sendMessage atualizada
window.sendMessage = async function () {
    const input = document.getElementById("chatInput");
    const messages = document.getElementById("chatMessages");

    const text = input.value.trim();
    if (!text) return;

    // Adiciona mensagem do usuário com o novo estilo
    addUserMessage(text);
    input.value = "";

    // Mostra indicador de digitação
    showTypingIndicator();

    try {
        const response = await fetch("/api/chatbot/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({ message: text })
        });

        const data = await response.json();
        
        // Remove indicador de digitação
        removeTypingIndicator();
        
        // Adiciona resposta do bot com o novo estilo
        addBotMessage(data.reply);
        
    } catch (error) {
        removeTypingIndicator();
        addBotMessage("Desculpe, tive um problema ao processar sua mensagem. Pode tentar novamente?");
        console.error("Erro no chat:", error);
    }
};

// Mantenha sua função getCookie existente
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}