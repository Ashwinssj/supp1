// static/js/dashboard.js

// Initialize cursor trail
const cursorTrail = document.createElement('div');
cursorTrail.className = 'cursor-trail';
document.body.appendChild(cursorTrail);

let mouseX = 0, mouseY = 0;
let trailX = 0, trailY = 0;

// Cursor animation frame
const animate = () => {
  trailX += (mouseX - trailX) * 0.2;
  trailY += (mouseY - trailY) * 0.2;
  cursorTrail.style.transform = `translate(${trailX}px, ${trailY}px)`;
  requestAnimationFrame(animate);
};

animate();

document.addEventListener('mousemove', (e) => {
  mouseX = e.clientX - 5;
  mouseY = e.clientY - 5;
});

// Enhanced chart interaction handlers
const initChartControls = () => {
  document.querySelectorAll('.chart-container').forEach(container => {
    const chartBody = container.querySelector('.chart-body');
    const expandBtn = container.querySelector('.chart-expand');
    const infoBtn = container.querySelector('.chart-info');

    // Dynamic zoom functionality
    expandBtn.addEventListener('click', () => {
      container.classList.toggle('fullscreen');
      setTimeout(() => {
        Plotly.Plots.resize(chartBody);
      }, 300);
    });

    // Interactive data tooltips
    infoBtn.addEventListener('click', () => {
      const modal = document.getElementById('detailModal');
      modal.classList.add('active');
      // Load dynamic chart metadata here
    });

    // Hover gradient effects
    chartBody.addEventListener('mouseenter', () => {
      container.style.transform = 'perspective(1000px) rotateX(5deg) rotateY(5deg)';
      container.style.boxShadow = '0 40px 80px rgba(0,0,0,0.3)';
    });

    chartBody.addEventListener('mouseleave', () => {
      container.style.transform = 'none';
      container.style.boxShadow = 'var(--shadow)';
    });
  });
};

// Initialize after charts load
setTimeout(initChartControls, 1000);

document.addEventListener('DOMContentLoaded', () => {
    // Initialize charts and map
    loadRouteMap();
    loadAnalyticsCharts();
    
    // Setup AI assistant
    setupAIAssistant();
    
    // Setup chart interactions
    setupChartInteractions();
    
    // Setup modal functionality
    setupModal();
    
    // Setup upload new button
    document.getElementById('uploadNewBtn').addEventListener('click', () => {
        window.location.href = '/';
    });
});

// Load route map
function loadRouteMap() {
    const mapContainer = document.getElementById('routeMap');
    
    // Initialize Leaflet map
    const map = L.map(mapContainer).setView([39.8283, -98.5795], 4); // Center on US
    
    // Add tile layer (map background)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    
    // Fetch route data from server
    fetch('/get_route_map')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                mapContainer.innerHTML = `<div class="error-message">${data.error}</div>`;
                return;
            }
            
            // Add location markers
            if (data.locations && data.locations.length > 0) {
                data.locations.forEach(location => {
                    const marker = L.marker([location.latitude, location.longitude])
                        .addTo(map)
                        .bindPopup(`<b>${location.location}</b>`);
                        
                    // Add click event for detailed view
                    marker.on('click', () => {
                        showLocationDetails(location.location);
                    });
                });
                
                // Create a bounds object to fit all markers
                const bounds = L.latLngBounds(data.locations.map(loc => [loc.latitude, loc.longitude]));
                map.fitBounds(bounds);
            }
            
            // Draw routes
            if (data.routes && data.routes.length > 0) {
                data.routes.forEach(route => {
                    const routeLine = L.polyline([
                        [route.source_lat, route.source_lng],
                        [route.dest_lat, route.dest_lng]
                    ], {
                        color: '#3498db',
                        weight: 3,
                        opacity: 0.7,
                        dashArray: '5, 10'
                    }).addTo(map);
                    
                    // Add route info popup
                    routeLine.bindPopup(`<b>Route:</b> ${route.source} to ${route.destination}`);
                    
                    // Add click event for detailed view
                    routeLine.on('click', () => {
                        const routeId = `${route.source}_to_${route.destination}`;
                        showRouteDetails(routeId);
                    });
                });
            }
        })
        .catch(error => {
            console.error('Error loading route map:', error);
            mapContainer.innerHTML = '<div class="error-message">Failed to load route map. Please try again.</div>';
        });
}

// Load analytics charts
function loadAnalyticsCharts() {
    fetch('/get_analytics_charts')
        .then(response => response.json())
        .then(data => {
            // Render inventory chart
            if (data.inventory_chart && !data.inventory_chart.error) {
                Plotly.newPlot('inventoryChart', data.inventory_chart);
                
                // Add click event
                document.getElementById('inventoryChart').on('plotly_click', (eventData) => {
                    const pointData = eventData.points[0];
                    if (!pointData?.x) return;
    const product = pointData.x;
    showProductDetails(product);
                });
            } else {
                document.getElementById('inventoryChart').innerHTML = '<div class="no-data">No inventory data available</div>';
            }
            
            // Render delivery time chart
            if (data.delivery_time_chart && !data.delivery_time_chart.error) {
                Plotly.newPlot('deliveryTimeChart', data.delivery_time_chart);
                
                // Add click event
                document.getElementById('deliveryTimeChart').on('plotly_click', (eventData) => {
                    const pointData = eventData.points[0];
                    const supplier = pointData.x;
                    showSupplierDetails(supplier);
                });
            } else {
                document.getElementById('deliveryTimeChart').innerHTML = '<div class="no-data">No delivery time data available</div>';
            }
            
            // Render cost analysis chart
            if (data.cost_analysis_chart && !data.cost_analysis_chart.error) {
                Plotly.newPlot('costAnalysisChart', data.cost_analysis_chart);
                
                // Add click event
                document.getElementById('costAnalysisChart').on('plotly_click', (eventData) => {
                    const pointData = eventData.points[0];
                    if (!pointData?.label) return;
    const product = pointData.label;
    showProductDetails(product);
                });
            } else {
                document.getElementById('costAnalysisChart').innerHTML = '<div class="no-data">No cost data available</div>';
            }
            
            // Render supplier performance chart
            if (data.supplier_performance_chart && !data.supplier_performance_chart.error) {
                Plotly.newPlot('supplierPerformanceChart', data.supplier_performance_chart);
                
                // Add click event
                document.getElementById('supplierPerformanceChart').on('plotly_click', (eventData) => {
                    const pointData = eventData.points[0];
                    const supplier = pointData.data.name;
                    showSupplierDetails(supplier);
                });
            } else {
                document.getElementById('supplierPerformanceChart').innerHTML = '<div class="no-data">No supplier performance data available</div>';
            }
        })
        .catch(error => {
            console.error('Error loading analytics charts:', error);
            document.querySelectorAll('.chart-body').forEach(container => {
                container.innerHTML = '<div class="error-message">Failed to load chart. Please try again.</div>';
            });
        });
}

// Setup AI assistant
function setupAIAssistant() {
    const chatMessages = document.getElementById('chatMessages');
    const aiQuery = document.getElementById('aiQuery');
    const aiSubmit = document.getElementById('aiSubmit');
    const suggestions = document.querySelectorAll('.suggestion');
    
    // Handle sending messages to AI
    function sendMessage(query) {
        if (!query.trim()) return;
        
        // Clear input
        aiQuery.value = '';
        
        // Add user message to chat
        chatMessages.innerHTML += `
            <div class="message user">
                <div class="message-content">${query}</div>
            </div>
        `;
        
        // Add loading message
        const loadingMsgId = 'loading-' + Date.now();
        chatMessages.innerHTML += `
            <div class="message system" id="${loadingMsgId}">
                <div class="message-content">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        `;
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Send query to AI
        fetch('/ask_ai', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query })
        })
        .then(response => response.json())
        .then(data => {
            // Remove loading message
            document.getElementById(loadingMsgId).remove();
            
            // Add AI response
            chatMessages.innerHTML += `
                <div class="message system">
                    <div class="message-content">${data.response || 'Sorry, I could not process your request.'}</div>
                </div>
            `;
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        })
        .catch(error => {
            // Remove loading message
            document.getElementById(loadingMsgId).remove();
            
            // Add error message
            chatMessages.innerHTML += `
                <div class="message system">
                    <div class="message-content">Sorry, I encountered an error. Please try again.</div>
                </div>
            `;
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            console.error('AI assistant error:', error);
        });
    }
    
    // Handle submit button click
    aiSubmit.addEventListener('click', () => {
        sendMessage(aiQuery.value);
    });
    
    // Handle enter key press
    aiQuery.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            sendMessage(aiQuery.value);
        }
    });
    
    // Handle suggestion clicks
    suggestions.forEach(suggestion => {
        suggestion.addEventListener('click', () => {
            const query = suggestion.getAttribute('data-query');
            aiQuery.value = query;
            sendMessage(query);
        });
    });
}

// Setup chart interactions
function setupChartInteractions() {
    // Handle chart expansion
    document.querySelectorAll('.chart-expand').forEach(button => {
        button.addEventListener('click', () => {
            const chartContainer = button.closest('.chart-container');
            chartContainer.classList.toggle('expanded');
            
            if (chartContainer.classList.contains('expanded')) {
                // Expand chart
                const chartId = chartContainer.querySelector('.chart-body').id;
                const chart = document.getElementById(chartId);
                
                // Force chart resize
                setTimeout(() => {
                    window.dispatchEvent(new Event('resize'));
                }, 100);
            }
        });
    });
    
    // Handle chart info clicks
    document.querySelectorAll('.chart-info').forEach(button => {
        button.addEventListener('click', () => {
            const chartTitle = button.closest('.chart-header').querySelector('h3').textContent;
            showChartInfo(chartTitle);
        });
    });
}

// Show details for different entities
function showSupplierDetails(supplierId) {
    fetch(`/get_details/supplier/${supplierId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showErrorModal('Error', data.error);
                return;
            }
            
            // Create content for modal
            let content = `
                <div class="detail-header">
                    <h4>${supplierId} Performance</h4>
                </div>
                <div class="detail-section">
                    <h5>Summary</h5>
                    <div class="detail-metrics">
                        <div class="metric">
                            <div class="metric-value">${data.summary.total_orders}</div>
                            <div class="metric-label">Total Orders</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${data.summary.unique_products}</div>
                            <div class="metric-label">Products</div>
                        </div>
                    </div>
                </div>
            `;
            
            // Add performance metrics if available
            if (data.performance) {
                content += `
                    <div class="detail-section">
                        <h5>Performance Metrics</h5>
                        <div class="detail-metrics">
                `;
                
                if (data.performance.on_time_delivery !== undefined) {
                    const onTimePercent = (data.performance.on_time_delivery * 100).toFixed(1);
                    content += `
                        <div class="metric">
                            <div class="metric-value">${onTimePercent}%</div>
                            <div class="metric-label">On-Time Delivery</div>
                        </div>
                    `;
                }
                
                if (data.performance.quality_score !== undefined) {
                    const qualityPercent = (data.performance.quality_score * 100).toFixed(1);
                    content += `
                        <div class="metric">
                            <div class="metric-value">${qualityPercent}%</div>
                            <div class="metric-label">Quality Score</div>
                        </div>
                    `;
                }
                
                if (data.performance.avg_delivery_time !== undefined) {
                    content += `
                        <div class="metric">
                            <div class="metric-value">${data.performance.avg_delivery_time.toFixed(1)}</div>
                            <div class="metric-label">Avg Delivery Days</div>
                        </div>
                    `;
                }
                
                content += `
                        </div>
                    </div>
                `;
            }
            
            // Add product breakdown if available
            if (data.product_breakdown) {
                content += `
                    <div class="detail-section">
                        <h5>Product Breakdown</h5>
                        <div id="productBreakdownChart" style="height: 250px;"></div>
                    </div>
                `;
            }
            
            // Show modal with content
            showModal('Supplier Details', content);
            
            // Render product breakdown chart if available
            if (data.product_breakdown) {
                const chartData = {
                    data: [{
                        x: data.product_breakdown.products,
                        y: data.product_breakdown.quantities,
                        type: 'bar',
                        marker: {
                            color: '#3498db'
                        }
                    }],
                    layout: {
                        margin: { t: 10, b: 50, l: 50, r: 10 },
                        xaxis: {
                            title: 'Product'
                        },
                        yaxis: {
                            title: 'Quantity'
                        }
                    }
                };
                
                Plotly.newPlot('productBreakdownChart', chartData.data, chartData.layout);
            }
        })
        .catch(error => {
            console.error('Error fetching supplier details:', error);
            showErrorModal('Error', 'Failed to load supplier details. Please try again.');
        });
}

function showProductDetails(productId) {
    fetch(`/get_details/product/${productId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showErrorModal('Error', data.error);
                return;
            }
            
            // Create content for modal
            let content = `
                <div class="detail-header">
                    <h4>${productId} Analysis</h4>
                </div>
                <div class="detail-section">
                    <h5>Summary</h5>
                    <div class="detail-metrics">
                        <div class="metric">
                            <div class="metric-value">${data.summary.total_orders}</div>
                            <div class="metric-label">Total Orders</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${data.summary.total_quantity}</div>
                            <div class="metric-label">Total Quantity</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${data.summary.suppliers}</div>
                            <div class="metric-label">Suppliers</div>
                        </div>
                    </div>
                </div>
            `;
            
            // Add cost analysis if available
            if (data.cost) {
                content += `
                    <div class="detail-section">
                        <h5>Cost Analysis</h5>
                        <div class="detail-metrics">
                            <div class="metric">
                                <div class="metric-value">$${data.cost.total_cost.toFixed(2)}</div>
                                <div class="metric-label">Total Cost</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">$${data.cost.average_cost.toFixed(2)}</div>
                                <div class="metric-label">Average Cost</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">$${data.cost.min_cost.toFixed(2)}</div>
                                <div class="metric-label">Min Cost</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">$${data.cost.max_cost.toFixed(2)}</div>
                                <div class="metric-label">Max Cost</div>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            // Add supplier breakdown if available
            if (data.supplier_breakdown) {
                content += `
                    <div class="detail-section">
                        <h5>Supplier Breakdown</h5>
                        <div id="supplierBreakdownChart" style="height: 250px;"></div>
                    </div>
                `;
            }
            
            // Show modal with content
            showModal('Product Details', content);
            
            // Render supplier breakdown chart if available
            if (data.supplier_breakdown) {
                const chartData = {
                    data: [{
                        labels: data.supplier_breakdown.suppliers,
                        values: data.supplier_breakdown.order_counts,
                        type: 'pie',
                        marker: {
                            colors: ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c']
                        }
                    }],
                    layout: {
                        margin: { t: 10, b: 10, l: 10, r: 10 }
                    }
                };
                
                Plotly.newPlot('supplierBreakdownChart', chartData.data, chartData.layout);
            }
        })
        .catch(error => {
            console.error('Error fetching product details:', error);
            showErrorModal('Error', 'Failed to load product details. Please try again.');
        });
}

function showRouteDetails(routeId) {
    fetch(`/get_details/route/${routeId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showErrorModal('Error', data.error);
                return;
            }
            
            // Parse route ID to get source and destination
            const [source, destination] = routeId.split('_to_');
            
            // Create content for modal
            let content = `
                <div class="detail-header">
                    <h4>Route: ${source} to ${destination}</h4>
                </div>
                <div class="detail-section">
                    <h5>Summary</h5>
                    <div class="detail-metrics">
                        <div class="metric">
                            <div class="metric-value">${data.summary.total_shipments}</div>
                            <div class="metric-label">Total Shipments</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${data.summary.products_shipped}</div>
                            <div class="metric-label">Products</div>
                        </div>
                    </div>
                </div>
            `;
            
            // Add distance information if available
            if (data.distance) {
                content += `
                    <div class="detail-section">
                        <h5>Distance Analysis</h5>
                        <div class="detail-metrics">
                            <div class="metric">
                                <div class="metric-value">${data.distance.average_distance.toFixed(1)} km</div>
                                <div class="metric-label">Average Distance</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${data.distance.total_distance.toFixed(1)} km</div>
                                <div class="metric-label">Total Distance</div>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            // Add delivery time information if available
            if (data.delivery_time) {
                content += `
                    <div class="detail-section">
                        <h5>Delivery Time Analysis</h5>
                        <div class="detail-metrics">
                            <div class="metric">
                                <div class="metric-value">${data.delivery_time.average_days.toFixed(1)}</div>
                                <div class="metric-label">Average Days</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${data.delivery_time.min_days}</div>
                                <div class="metric-label">Min Days</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${data.delivery_time.max_days}</div>
                                <div class="metric-label">Max Days</div>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            // Add monthly trend if available
            if (data.monthly_trend) {
                content += `
                    <div class="detail-section">
                        <h5>Monthly Shipment Volume</h5>
                        <div id="monthlyTrendChart" style="height: 250px;"></div>
                    </div>
                `;
            }
            
            // Show modal with content
            showModal('Route Details', content);
            
            // Render monthly trend chart if available
            if (data.monthly_trend) {
                const chartData = {
                    data: [{
                        x: data.monthly_trend.dates,
                        y: data.monthly_trend.values,
                        type: 'scatter',
                        mode: 'lines+markers',
                        line: {
                            color: '#3498db',
                            width: 2
                        },
                        marker: {
                            color: '#2980b9',
                            size: 6
                        }
                    }],
                    layout: {
                        margin: { t: 10, b: 50, l: 50, r: 10 },
                        xaxis: {
                            title: 'Month'
                        },
                        yaxis: {
                            title: 'Shipments'
                        }
                    }
                };
                
                Plotly.newPlot('monthlyTrendChart', chartData.data, chartData.layout);
            }
        })
        .catch(error => {
            console.error('Error fetching route details:', error);
            showErrorModal('Error', 'Failed to load route details. Please try again.');
        });
}

function showLocationDetails(locationId) {
    // Here we would fetch warehouse details if the location is a warehouse
    fetch(`/get_details/warehouse/${locationId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                // If it's not a warehouse, just show basic location info
                showBasicLocationInfo(locationId);
                return;
            }
            
            // Create content for modal
            let content = `
                <div class="detail-header">
                    <h4>${locationId} Warehouse</h4>
                </div>
                <div class="detail-section">
                    <h5>Summary</h5>
                    <div class="detail-metrics">
                        <div class="metric">
                            <div class="metric-value">${data.summary.total_inventory}</div>
                            <div class="metric-label">Total Inventory</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${data.summary.unique_products}</div>
                            <div class="metric-label">Products</div>
                        </div>
                    </div>
                </div>
            `;
            
            // Add location information if available
            if (data.location) {
                content += `
                    <div class="detail-section">
                        <h5>Location Information</h5>
                        <div class="location-details">
                `;
                
                // Add coordinates
                if (data.location.coordinates) {
                    content += `
                            <div class="location-item">
                                <div class="location-label">Coordinates:</div>
                                <div class="location-value">${data.location.coordinates.latitude.toFixed(4)}, ${data.location.coordinates.longitude.toFixed(4)}</div>
                            </div>
                    `;
                }
                
                // Add address if available
                if (data.location.address) {
                    content += `
                            <div class="location-item">
                                <div class="location-label">Address:</div>
                                <div class="location-value">${data.location.address}</div>
                            </div>
                    `;
                }
                
                // Add town/city if available
                if (data.location.town) {
                    content += `
                            <div class="location-item">
                                <div class="location-label">City/Town:</div>
                                <div class="location-value">${data.location.town}</div>
                            </div>
                    `;
                }
                
                // Add country if available
                if (data.location.country) {
                    content += `
                            <div class="location-item">
                                <div class="location-label">Country:</div>
                                <div class="location-value">${data.location.country}</div>
                            </div>
                    `;
                }
                
                content += `
                        </div>
                        <div id="warehouseLocationMap" style="height: 200px; margin-top: 10px;"></div>
                    </div>
                `;
            }
            
            // Add cost analysis if available
            if (data.cost_analysis) {
                content += `
                    <div class="detail-section">
                        <h5>Cost Analysis</h5>
                        <div class="detail-metrics">
                `;
                
                if (data.cost_analysis.total_cost) {
                    content += `
                            <div class="metric">
                                <div class="metric-value">$${data.cost_analysis.total_cost.toFixed(2)}</div>
                                <div class="metric-label">Total Cost</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">$${data.cost_analysis.average_cost_per_product.toFixed(2)}</div>
                                <div class="metric-label">Avg Cost/Product</div>
                            </div>
                    `;
                } else if (data.cost_analysis.total_price) {
                    content += `
                            <div class="metric">
                                <div class="metric-value">$${data.cost_analysis.total_price.toFixed(2)}</div>
                                <div class="metric-label">Total Price</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">$${data.cost_analysis.average_price_per_product.toFixed(2)}</div>
                                <div class="metric-label">Avg Price/Product</div>
                            </div>
                    `;
                }
                
                content += `
                        </div>
                        <div id="warehouseCostChart" style="height: 250px;"></div>
                    </div>
                `;
            }
            
            // Add category analysis if available
            if (data.category_analysis) {
                content += `
                    <div class="detail-section">
                        <h5>Category Analysis</h5>
                        <div id="warehouseCategoryChart" style="height: 250px;"></div>
                    </div>
                `;
            }
            
            // Add product breakdown if available
            if (data.product_breakdown) {
                content += `
                    <div class="detail-section">
                        <h5>Product Inventory</h5>
                        <div id="warehouseProductChart" style="height: 250px;"></div>
                    </div>
                `;
            }
            
            // Add delivery time analysis if available
            if (data.delivery_time) {
                content += `
                    <div class="detail-section">
                        <h5>Delivery Time Analysis</h5>
                        <div class="detail-metrics">
                            <div class="metric">
                                <div class="metric-value">${data.delivery_time.average_days.toFixed(1)}</div>
                                <div class="metric-label">Average Days</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${data.delivery_time.min_days}</div>
                                <div class="metric-label">Min Days</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${data.delivery_time.max_days}</div>
                                <div class="metric-label">Max Days</div>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            // Add flow analysis if available
            if (data.flow_analysis) {
                content += `
                    <div class="detail-section">
                        <h5>Inbound/Outbound Analysis</h5>
                        <div class="detail-metrics">
                            <div class="metric">
                                <div class="metric-value">${data.flow_analysis.inbound_count}</div>
                                <div class="metric-label">Inbound</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${data.flow_analysis.outbound_count}</div>
                                <div class="metric-label">Outbound</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${data.flow_analysis.ratio.toFixed(2)}</div>
                                <div class="metric-label">In/Out Ratio</div>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            // Show modal with content
            showModal('Warehouse Details', content);
            
            // Render location map if coordinates are available
            if (data.location && data.location.coordinates) {
                const lat = data.location.coordinates.latitude;
                const lng = data.location.coordinates.longitude;
                
                setTimeout(() => {
                    const locationMap = L.map('warehouseLocationMap').setView([lat, lng], 10);
                    
                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    }).addTo(locationMap);
                    
                    L.marker([lat, lng])
                        .addTo(locationMap)
                        .bindPopup(`<b>${locationId} Warehouse</b>`)
                        .openPopup();
                }, 300);
            }
            
            // Render cost chart if available
            if (data.cost_analysis) {
                if (data.cost_analysis.product_costs) {
                    const chartData = {
                        data: [{
                            x: data.cost_analysis.product_costs.products,
                            y: data.cost_analysis.product_costs.costs,
                            type: 'bar',
                            marker: {
                                color: '#e74c3c'
                            }
                        }],
                        layout: {
                            margin: { t: 10, b: 50, l: 50, r: 10 },
                            xaxis: {
                                title: 'Product'
                            },
                            yaxis: {
                                title: 'Cost ($)'
                            }
                        }
                    };
                    
                    Plotly.newPlot('warehouseCostChart', chartData.data, chartData.layout);
                } else if (data.cost_analysis.product_prices) {
                    const chartData = {
                        data: [{
                            x: data.cost_analysis.product_prices.products,
                            y: data.cost_analysis.product_prices.prices,
                            type: 'bar',
                            marker: {
                                color: '#e74c3c'
                            }
                        }],
                        layout: {
                            margin: { t: 10, b: 50, l: 50, r: 10 },
                            xaxis: {
                                title: 'Product'
                            },
                            yaxis: {
                                title: 'Price ($)'
                            }
                        }
                    };
                    
                    Plotly.newPlot('warehouseCostChart', chartData.data, chartData.layout);
                }
            }
            
            // Render category chart if available
            if (data.category_analysis) {
                const chartData = {
                    data: [{
                        labels: data.category_analysis.categories,
                        values: data.category_analysis.quantities,
                        type: 'pie',
                        hole: 0.4,
                        marker: {
                            colors: ['#3498db', '#2ecc71', '#9b59b6', '#e74c3c', '#f39c12', '#1abc9c']
                        }
                    }],
                    layout: {
                        margin: { t: 10, b: 10, l: 10, r: 10 },
                        showlegend: true,
                        legend: {
                            orientation: 'h',
                            y: -0.2
                        }
                    }
                };
                
                Plotly.newPlot('warehouseCategoryChart', chartData.data, chartData.layout);
            }
            
            // Render product inventory chart if available
            if (data.product_breakdown) {
                const chartData = {
                    data: [{
                        x: data.product_breakdown.products,
                        y: data.product_breakdown.quantities,
                        type: 'bar',
                        marker: {
                            color: '#2ecc71'
                        }
                    }],
                    layout: {
                        margin: { t: 10, b: 50, l: 50, r: 10 },
                        xaxis: {
                            title: 'Product'
                        },
                        yaxis: {
                            title: 'Quantity'
                        }
                    }
                };
                
                Plotly.newPlot('warehouseProductChart', chartData.data, chartData.layout);
            }
        })
        .catch(error => {
            console.error('Error fetching warehouse details:', error);
            showBasicLocationInfo(locationId);
        });
}

function showBasicLocationInfo(locationId) {
    const content = `
        <div class="detail-header">
            <h4>${locationId}</h4>
        </div>
        <div class="detail-section">
            <p>This is a location in your supply chain network. It may be a supplier, warehouse, distribution center, or customer location.</p>
            <p>For more detailed information, try the AI assistant.</p>
        </div>
    `;
    
    showModal('Location Details', content);
}

function showChartInfo(chartTitle) {
    let content = '';
    
    switch(chartTitle) {
        case 'Inventory Levels':
            content = `
                <p>This chart shows inventory levels by product across different warehouses.</p>
                <ul>
                    <li><b>X-axis:</b> Products</li>
                    <li><b>Y-axis:</b> Quantity</li>
                    <li><b>Color:</b> Warehouse</li>
                </ul>
                <p><b>Usage:</b> Click on any product bar to view detailed product information.</p>
            `;
            break;
        case 'Delivery Time Analysis':
            content = `
                <p>This chart shows the average delivery time in days for each supplier.</p>
                <ul>
                    <li><b>X-axis:</b> Suppliers</li>
                    <li><b>Y-axis:</b> Average days</li>
                </ul>
                <p><b>Usage:</b> Click on any supplier bar to view detailed supplier performance metrics.</p>
            `;
            break;
        case 'Cost Analysis':
            content = `
                <p>This chart shows the distribution of costs or prices across different products and categories.</p>
                <ul>
                    <li><b>Slices/Segments:</b> Products or Categories</li>
                    <li><b>Size:</b> Total cost or price</li>
                    <li><b>Center:</b> Total sum</li>
                </ul>
                <p><b>Usage:</b> Click on any segment to view detailed product cost analysis. Use the warehouse filter to view costs by specific warehouse locations.</p>
                <p><b>Note:</b> Cost data is derived from price information when direct cost data is unavailable.</p>
            `;
            break;
        case 'Supplier Performance':
            content = `
                <p>This radar chart shows supplier performance across key metrics.</p>
                <ul>
                    <li><b>On-time Delivery:</b> Percentage of orders delivered on time</li>
                    <li><b>Quality Score:</b> Product quality rating</li>
                    <li><b>Overall Score:</b> Combined performance score</li>
                </ul>
                <p><b>Usage:</b> Click on any supplier line to view detailed supplier information.</p>
            `;
            break;
        case 'Supply Chain Route Map':
            content = `
                <p>This map shows your supply chain network with locations and routes.</p>
                <ul>
                    <li><b>Markers:</b> Warehouses, suppliers, and destinations</li>
                    <li><b>Lines:</b> Routes between locations</li>
                </ul>
                <p><b>Usage:</b> Click on any marker or route to view detailed information.</p>
                <p><b>Controls:</b> Use mouse to pan and zoom, click markers for location details.</p>
            `;
            break;
        default:
            content = `<p>No additional information available for this chart.</p>`;
    }
    
    showModal(`About: ${chartTitle}`, content);
}

// Modal functions
function setupModal() {
    const modal = document.getElementById('detailModal');
    const closeBtn = document.getElementById('closeDetailModal');
    
    closeBtn.addEventListener('click', () => {
        modal.classList.remove('active');
    });
    
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
}

function showModal(title, content) {
    const modal = document.getElementById('detailModal');
    const modalTitle = document.getElementById('detailTitle');
    const modalContent = document.getElementById('detailContent');
    
    modalTitle.textContent = title;
    modalContent.innerHTML = content;
    
    modal.classList.add('active');
}

function showErrorModal(title, message) {
    const content = `
        <div class="error-message">
            <i class="fas fa-exclamation-circle"></i>
            <p>${message}</p>
        </div>
    `;
    
    showModal(title, content);
}