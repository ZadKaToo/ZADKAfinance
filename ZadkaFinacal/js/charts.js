function initCharts() {
    initIncomeExpenseChart();
    initCategoryChart();
    initTrendsChart();
    initProgressChart();
}

function initIncomeExpenseChart(data) {
    const ctx = document.getElementById('income-expense-chart');
    if (!ctx) return;

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'รายรับ',
                    data: data.income,
                    borderColor: 'rgb(34, 197, 94)',
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    tension: 0.3
                },
                {
                    label: 'รายจ่าย',
                    data: data.expense,
                    borderColor: 'rgb(239, 68, 68)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => '฿' + value.toLocaleString()
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: context => {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += '฿' + context.parsed.y.toLocaleString();
                            return label;
                        }
                    }
                }
            }
        }
    });
}

function initCategoryChart(data) {
    const ctx = document.getElementById('category-chart');
    if (!ctx) return;

    const backgroundColors = [
        'rgb(59, 130, 246)',
        'rgb(16, 185, 129)',
        'rgb(245, 158, 11)',
        'rgb(239, 68, 68)',
        'rgb(168, 85, 247)',
        'rgb(236, 72, 153)'
    ];

    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.categories,
            datasets: [{
                data: data.amounts,
                backgroundColor: backgroundColors,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: context => {
                            const value = context.raw;
                            const percentage = ((value / data.amounts.reduce((a, b) => a + b)) * 100).toFixed(1);
                            return `฿${value.toLocaleString()} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}
