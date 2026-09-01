document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('operationsChart');
    if (!canvas) return;

    const dataUrl = canvas.dataset.url;

    fetch(dataUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error('Réponse HTTP ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            const ctx = canvas.getContext('2d');

            const chartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [
                        {
                            label: 'Total opérations',
                            data: data.totaux,
                            backgroundColor: 'rgba(0, 16, 81, 0.6)',
                        },
                        {
                            label: 'Transfert de titres',
                            data: data.transferts,
                            backgroundColor: 'rgba(255, 159, 64, 0.6)',
                        },
                        {
                            label: 'Vente de titres',
                            data: data.ventes,
                            backgroundColor: 'rgba(0, 173, 0, 0.6)',
                        },
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true, ticks: { precision: 0 } }
                    },
                    plugins: {
                        legend: { position: 'top' }
                    }
                }
            });

            // Force un recalcul de la taille une fois le layout du thème stabilisé
            // (utile si le parent n'avait pas encore sa largeur finale au premier rendu)
            window.addEventListener('load', () => chartInstance.resize());
            setTimeout(() => chartInstance.resize(), 300);
            window.addEventListener('resize', () => chartInstance.resize());
        })
        .catch(err => console.error('Erreur chargement graphique operations:', err));
});
