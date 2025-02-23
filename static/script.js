document.addEventListener('DOMContentLoaded', function() {
    // Animações de texto para as páginas
    const pages = [
        '.reservas-page', 
        '.manutencao-page', 
        '.feedback-page', 
        '.correspondencias-page', 
        '.estacionamento-page', 
        '.emergencias-page', 
        '.admin-page',
        '.cadastro-moradores-page'
    ];

    pages.forEach(pageClass => {
        const text = document.querySelector(`${pageClass} .hero h1`);
        if (text) {
            text.innerHTML = text.textContent.replace(/\S/g, "<span class='letter'>$&</span>");
            anime.timeline({loop: true})
            .add({
                targets: `${pageClass} .hero h1 .letter`,
                translateX: [40,0],
                translateZ: 0,
                opacity: [0,1],
                easing: "easeOutExpo",
                duration: 1200,
                delay: (el, i) => 500 + 30 * i
            }).add({
                targets: `${pageClass} .hero h1 .letter`,
                translateX: [0,-30],
                opacity: [1,0],
                easing: "easeInExpo",
                duration: 1100,
                delay: (el, i) => 100 + 30 * i
            });
        }
    });

    // Verifica se estamos na página inicial para registrar notificações push
    if (document.querySelector('.hero h1.animate-text')) { // Identifica a página inicial
        // Inicializar Firebase (movido do inline HTML)
        const firebaseConfig = {
            apiKey: "sua_api_key",
            authDomain: "seu_projeto.firebaseapp.com",
            projectId: "seu_projeto",
            storageBucket: "seu_projeto.appspot.com",
            messagingSenderId: "seu_sender_id",
            appId: "seu_app_id"
        };

        firebase.initializeApp(firebaseConfig);
        const messaging = firebase.messaging();

        // Função para registrar o token FCM
        function registerPush() {
            messaging.requestPermission().then(() => {
                return messaging.getToken({ vapidKey: 'SEU_VAPID_KEY_AQUI' }); // Adicione a chave VAPID se necessário
            }).then((token) => {
                fetch('/register_token', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token: token })
                }).then(response => console.log('Token registrado:', response));
            }).catch((err) => {
                console.error('Erro ao registrar push:', err);
            });
        }

        // Receber notificações em foreground
        messaging.onMessage((payload) => {
            console.log('Notificação recebida:', payload);
            alert(payload.notification.body); // Exemplo simples de exibição
        });

        // Registrar o Service Worker
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/sw.js')
                .then((reg) => {
                    console.log('Service Worker registrado', reg);
                    registerPush(); // Registrar o token após o Service Worker estar pronto
                })
                .catch((err) => console.error('Erro ao registrar Service Worker', err));
        }
    }
});
