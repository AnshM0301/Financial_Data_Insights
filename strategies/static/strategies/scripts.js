$(document).ready(function() {
    function numberWithCommas(x) {
        return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    function fetchData(timeRange = '5y') {
        let companyName = $('#company-name').val() || 'GOOG';
        let timeframe = $('#timeframe').val() || '1d';

        console.log('Fetching data with company name:', companyName, 'and time range:', timeRange);

        $.ajax({
            url: '/strategies/search/',
            data: {
                'company_name': companyName,
                'timeframe': timeframe,
                'time_range': timeRange,
            },
            dataType: 'json',
            success: function(data) {
                console.log('Data fetched successfully:', data);
                $('#company-name-title').text(data.financial_details["Name"]);
                $('#latest-price').text(`Latest Price: $${data.latest_price}`);
                $('#key-stats-details').empty();
                $('#about-company-details').empty();

                let keyStats = ['Market Capitalization', 'Dividend Yield', 'PE Ratio', 'EPS', 'Net Income', 'Revenue', 'Shares Float', 'Beta'];
                let aboutCompany = ['Sector', 'Industry', 'Headquarters', 'Total Employees', 'Website', 'Summary'];

                keyStats.forEach(key => {
                    let value = data.financial_details[key];
                    if (typeof value === 'number') {
                        value = numberWithCommas(value);
                    }
                    $('#key-stats-details').append(`<p><strong>${key}:</strong> ${value}</p>`);
                });

                aboutCompany.forEach(key => {
                    let value = data.financial_details[key];
                    if (key === 'Website' && value !== 'N/A') {
                        value = `<a href="${value}" target="_blank">${value}</a>`;
                    } else if (key === 'Total Employees' && typeof value === 'number') {
                        value = numberWithCommas(value);
                    }
                    if (key === 'Summary') {
                        let summaryText = value.length > 100 ? value.substring(0, 100) + '...' : value;
                        let showMoreLink = value.length > 100 ? `<a href="#" class="show-more">Show more</a>` : '';
                        $('#about-company-details').append(`<p><strong>${key}:</strong> <span class="summary-text">${summaryText}</span> ${showMoreLink}</p>`);
                    } else {
                        $('#about-company-details').append(`<p><strong>${key}:</strong> ${value}</p>`);
                    }
                });

                $('#about-company-name').text(data.financial_details["Name"]);

                $('.show-more').click(function(e) {
                    e.preventDefault();
                    let fullText = data.financial_details['Summary'];
                    $(this).siblings('.summary-text').text(fullText);
                    $(this).remove();
                });

                $('#candlestick-chart').html(data.graph_div);
                $('#chart-performance').html(data.charts.performance);
                $('#chart-debt').html(data.charts.debt);
                $('#chart-conversion').html(data.charts.conversion);
                $('#chart-roe_roa').html(data.charts.roe_roa);
                $('#technical-chart').html(data.technical_chart);
                fetchTechnicalAnalysis(companyName);
                fetchCompanyNews(companyName);
            },
            error: function(error) {
                console.log('Error fetching data:', error);
                alert('Error fetching company data');
            }
        });
    }

    function fetchTechnicalAnalysis(companyName) {
        let selectedIndicators = $('#indicator-select').val() || ['vwap'];

        console.log('Fetching technical analysis for:', companyName, 'with indicators:', selectedIndicators);

        $.ajax({
            url: `/strategies/${encodeURIComponent(companyName)}/technical_analysis/`,
            data: {
                'indicators': selectedIndicators
            },
            traditional: true,
            dataType: 'json',
            success: function(data) {
                console.log('Technical analysis data fetched successfully:', data);
                $('#technical-chart').html(data.technical_chart);
                $('#trend-status').text(data.trend_status);
                $('#indicator-summary').html(data.indicator_description);
            },
            error: function(error) {
                console.log('Error fetching technical analysis data:', error);
                alert('Error fetching technical analysis data');
            }
        });
    }

    function fetchCompanyNews(companyName) {
        console.log('Fetching news for company:', companyName);

        $.ajax({
            url: `/strategies/news/`,
            data: {
                'company_name': companyName
            },
            dataType: 'json',
            success: function(data) {
                console.log('Company news fetched successfully:', data);
                $('#news-cards').empty();
                $('#full-company-name').text(data.full_company_name);
                $.each(data.news_articles, function(index, article) {
                    let newsCard = `
                        <div class="news-card">
                            <img src="${article.urlToImage}" class="card-img-top" alt="News Image"><br>
                            <h3>${article.title}</h3>
                            <p>${article.description}</p>
                            <span>${article.source.name} - ${new Date(article.publishedAt).toLocaleDateString()}</span>
                            <a href="${article.url}" target="_blank">Read more </a>
                        </div>
                    `;
                    $('#news-cards').append(newsCard);
                });
            },
            error: function(error) {
                console.log('Error fetching company news:', error);
                alert('Error fetching company news');
            }
        });
    }

    $('#search-button').click(function() {
        console.log('Search button clicked');
        fetchData();
    });

    $('#timeframe').change(function() {
        console.log('Timeframe changed');
        fetchData();
    });

    $('.btn-time-range').click(function() {
        let timeRange = $(this).data('range');
        console.log('Time range button clicked:', timeRange);
        fetchData(timeRange);
    });

    $('#update-chart').click(function() {
        console.log('Update chart button clicked');
        fetchTechnicalAnalysis();
    });

    $('#buy-button').click(function() {
        console.log('Buy button clicked');
        $('#buyModal').modal('show');
    });

    $('#quantity').on('input', function() {
        let quantity = $(this).val();
        let currentPrice = parseFloat($('#latest-price').text().replace('Latest Price: $', ''));
        let totalPrice = (quantity * currentPrice).toFixed(2);
        $('#total-price').text(totalPrice);
    });

    $('#confirm-buy-button').click(function() {
        let quantity = $('#quantity').val();
        let currentPrice = parseFloat($('#latest-price').text().replace('Latest Price: $', ''));
        let ticker = $('#company-name').val();
        let csrfToken = $('input[name="csrfmiddlewaretoken"]').val();

        console.log('Confirm buy button clicked');
        console.log(`Sending request with ticker: ${ticker}, quantity: ${quantity}, price: ${currentPrice}`);

        $.ajax({
            url: `/dashboard/buy_stock/`,
            method: 'POST',
            data: {
                'ticker': ticker,
                'quantity': quantity,
                'price': currentPrice,
                'csrfmiddlewaretoken': csrfToken
            },
            success: function(response) {
                console.log('AJAX request successful:', response);
                $('#buyModal').modal('hide');
                alert('Stock purchased successfully');
                // Optionally, refresh the dashboard or update the holdings table
            },
            error: function(error) {
                console.log('AJAX request failed:', error);
                alert('Error purchasing stock');
            }
        });
    });

    fetchData();
});
