self.addEventListener('push', function(event) {
    const data = event.data.json();
    const options = {
        body: data.notification.body,
        icon: '/static/icon.png', // Adicione um ícone se desejar
        vibrate: [200, 100, 200] // Vibração (opcional)
    };
    event.waitUntil(
        self.registration.showNotification(data.notification.title, options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    event.waitUntil(
        clients.openWindow('/') // Abre a página inicial ao clicar na notificação
    );
});