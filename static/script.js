document.addEventListener('DOMContentLoaded', function() {
    const pages = [
        '.reservas-page', 
        '.manutencao-page', 
        '.feedback-page', 
        '.correspondencias-page', 
        '.estacionamento-page', 
        '.emergencias-page', 
        '.admin-page',
        '.cadastro-moradores-page'  // Nova página adicionada
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
});