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



window.sendMessage = async function () {
    const input = document.getElementById("chatInput");
    const messages = document.getElementById("chatMessages");

    const text = input.value.trim();
    if (!text) return;

    messages.innerHTML += `<div class="mb-2 text-end"><strong>Você:</strong> ${text}</div>`;
    input.value = "";

    const response = await fetch("/api/chatbot/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({ message: text })
    });

    const data = await response.json();

    messages.innerHTML += `<div class="mb-2"><strong>Pulse:</strong> ${data.reply}</div>`;
    messages.scrollTop = messages.scrollHeight;
};


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
