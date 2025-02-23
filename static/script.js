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
        // Configuração do Firebase para appcondominio-2fcac
        const firebaseConfig = {
            apiKey: "AIzaSyBao-CekS4U-YyEKF8sZqzWbq1m9NqRK1s", // Obtenha no Firebase Console
            authDomain: "appcondominio-2fcac.firebaseapp.com",
            projectId: "appcondominio-2fcac",
            storageBucket: "appcondominio-2fcac.firebasestorage.app",
            messagingSenderId: "454281232654", // Aproximado do client_id, verifique no Firebase Console
            appId: "1:454281232654:web:647583086f3d4ed730175f" // Obtenha no Firebase Console
        };

        // Inicializar Firebase
        firebase.initializeApp(firebaseConfig);
        const messaging = firebase.messaging();

        // Função para registrar o token FCM
        function registerPush() {
            messaging.requestPermission()
                .then(() => {
                    return messaging.getToken({ vapidKey: "SUBSTITUA_PELO_VAPID_KEY" }); // Substitua pela chave VAPID
                })
                .then((token) => {
                    console.log('Token FCM gerado:', token);
                    fetch('/register_token', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ token: token })
                    })
                    .then(response => response.text())
                    .then(text => console.log('Resposta do backend:', text))
                    .catch(err => console.error('Erro ao enviar token ao backend:', err));
                })
                .catch((err) => {
                    console.error('Erro ao obter permissão ou token FCM:', err);
                });
        }

        // Receber notificações em foreground
        messaging.onMessage((payload) => {
            console.log('Notificação recebida em foreground:', payload);
            alert(payload.notification.body); // Exemplo simples de exibição
        });

        // Registrar o Service Worker
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/sw.js')
                .then((reg) => {
                    console.log('Service Worker registrado com sucesso:', reg);
                    registerPush(); // Registrar o token após o Service Worker estar pronto
                })
                .catch((err) => {
                    console.error('Erro ao registrar Service Worker:', err);
                });
        } else {
            console.error('Service Workers não são suportados neste navegador.');
        }
    }
});
