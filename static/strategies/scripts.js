    $(document).ready(function() {
        fetchData();

        $('#search-button').click(function() {
            fetchData();
        });

        $('#timeframe').change(function() {
            fetchData();
        });

        $('.btn-time-range').click(function() {
            let timeRange = $(this).data('range');
            fetchData(timeRange);
        });

        $('#update-chart').click(function() {
            fetchTechnicalAnalysis();
        });

        function fetchData(timeRange = '5y') {
            let companyName = $('#company-name').val() || 'GOOG';
            let timeframe = $('#timeframe').val() || '1d';

            console.log("Fetching data with company name:", companyName, "and time range:", timeRange );  // Debug statement

            $.ajax({
                url: '/strategies/search/',
                data: {
                    'company_name': companyName,
                    'timeframe': timeframe,
                    'time_range': timeRange,
                },
                dataType: 'json',
                success: function(data) {
                    $('#company-name-title').text(data.financial_details["Name"]);
                    $('#latest-price').text(`Latest Price: $${data.latest_price}`);
                    $('#financial-details').empty();
                    $.each(data.financial_details, function(key, value) {
                        $('#financial-details').append(`<p><strong>${key}:</strong> ${value}</p>`);
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
                    console.log(error);
                    alert('Error fetching company data');
                }
            });
        }

        function fetchTechnicalAnalysis() {
            let ticker = $('#company-name').val() || 'GOOG';
            let selectedIndicators = $('#indicator-select').val() || [] || 'vwap';

            console.log("Fetching technical analysis with indicators:", selectedIndicators);  // Debug statement

            $.ajax({
                url: `/strategies/${encodeURIComponent(ticker)}/technical_analysis/`,
                data: {
                    'indicators': selectedIndicators
                },
                traditional: true, // Important for correctly serializing the array
                dataType: 'json',
                success: function(data) {
                    $('#technical-chart').html(data.technical_chart);
                    $('#trend-status').text(data.trend_status);
                    $('#indicator-summary').html(data.indicator_description);
                },
                error: function(error) {
                    console.log(error);
                    alert('Error fetching technical analysis data');
                }
            });
        }

        function fetchCompanyNews(companyName) {
            console.log("Fetching news for company:", companyName);  // Debug statement
    
            $.ajax({
                url: `/strategies/news/`,
                data: {
                    'company_name': companyName
                },
                traditional: true,
                dataType: 'json',
                success: function(data) {
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
                    console.log(error);
                    alert('Error fetching company news');
                }
            });
        }
    });

