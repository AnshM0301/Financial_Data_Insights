document.addEventListener('DOMContentLoaded', function () {
    const tickerButtons = document.querySelectorAll('.ticker-button');
    const tickerDataContainer = document.getElementById('ticker-data');

    tickerButtons.forEach(button => {
        button.addEventListener('click', function () {
            const ticker = this.getAttribute('data-ticker');
            console.log('Button clicked for ticker:', ticker);

            fetch(`/get_ticker_data/${ticker}/`)
                .then(response => response.json())
                .then(data => updateDashboard(data))
                .catch(error => console.error('Error fetching ticker data:', error));
        });
    });

    function updateDashboard(data) {
        const { ticker, name, close, change, pct_change, country, last_close, high_52wk, low_52wk, chart_html } = data;

        tickerDataContainer.innerHTML = `
            <h1 class="text-center">Market Overview</h1>
            <div class="row p-3">
                <div class="col-3">
                    <h5 class="text-warning">${ticker}</h5>
                    <p class="text-warning">${name}</p>
                </div>
                <div class="col-3">
                    ${change.includes('-') ? `
                    <h5 class="text-danger">${close}</h5>
                    <p class="text-danger fw-bold">${change}&nbsp;&nbsp;&nbsp;&nbsp;${pct_change}</p>
                    ` : `
                    <h5 class="text-success">${close}</h5>
                    <p class="text-success fw-bold">+${change}&nbsp;&nbsp;&nbsp;&nbsp;${pct_change}</p>
                    `}
                </div>
                <div class="col-3">
                    <h5 class="text-warning">Country</h5>
                    <p class="text-warning">${country}</p>
                </div>
                <div class="col-3">
                    <h5 class="text-warning">Last Close</h5>
                    <p class="text-warning">${last_close}</p>
                </div>
                <div class="col-3">
                    <h5 class="text-warning">52-Week High</h5>
                    <p class="text-warning">${high_52wk}</p>
                </div>
                <div class="col-3">
                    <h5 class="text-warning">52-Week Low</h5>
                    <p class="text-warning">${low_52wk}</p>
                </div>

            <div class="card shadow-lg">
                <div class="card-header text-center">${ticker} Overview Chart</div>
                <div class="card-body">
                    ${chart_html}
                </div>
            </div>
        `;
    }
});
