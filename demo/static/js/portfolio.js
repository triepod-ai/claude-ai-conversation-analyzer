// AI Conversation Analyzer Portfolio JavaScript

class PortfolioApp {
    constructor() {
        this.initializeComponents();
        this.setupEventListeners();
        this.startRealTimeUpdates();
    }

    initializeComponents() {
        // Initialize charts if elements exist
        if (document.getElementById('performanceChart')) {
            this.initializePerformanceChart();
        }
        
        // Initialize real-time stats
        this.setupStatsUpdates();
        
        // Initialize animations
        this.setupAnimations();
    }

    setupEventListeners() {
        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });

        // Feature card interactions
        document.querySelectorAll('.feature-card, .tech-card, .highlight-card').forEach(card => {
            this.addCardInteractions(card);
        });

        // Demo button interactions
        document.querySelectorAll('.demo-query').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.highlightDemoButton(e.target);
            });
        });
    }

    addCardInteractions(card) {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-8px)';
            card.style.transition = 'all 0.3s ease';
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0)';
        });

        // Add click ripple effect
        card.addEventListener('click', (e) => {
            this.createRippleEffect(e, card);
        });
    }

    createRippleEffect(event, element) {
        const ripple = document.createElement('span');
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;

        ripple.style.cssText = `
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.6);
            transform: scale(0);
            left: ${x}px;
            top: ${y}px;
            width: ${size}px;
            height: ${size}px;
            pointer-events: none;
            animation: ripple-animation 0.6s ease-out;
        `;

        // Add ripple styles to head if not already present
        if (!document.getElementById('ripple-styles')) {
            const style = document.createElement('style');
            style.id = 'ripple-styles';
            style.textContent = `
                @keyframes ripple-animation {
                    to {
                        transform: scale(2);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
        }

        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(ripple);

        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    highlightDemoButton(button) {
        // Remove active class from all demo buttons
        document.querySelectorAll('.demo-query').forEach(btn => {
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-outline-secondary');
        });

        // Add active class to clicked button
        button.classList.remove('btn-outline-secondary');
        button.classList.add('btn-primary');

        // Reset after 2 seconds
        setTimeout(() => {
            button.classList.remove('btn-primary');
            button.classList.add('btn-outline-secondary');
        }, 2000);
    }

    initializePerformanceChart() {
        const ctx = document.getElementById('performanceChart');
        if (!ctx) return;

        // Generate sample performance data
        const labels = [];
        const processingData = [];
        const responseData = [];

        for (let i = 30; i >= 0; i--) {
            labels.push(`${i}m ago`);
            processingData.push(395 + Math.random() * 8); // 395-403 range
            responseData.push(200 + Math.random() * 100); // 200-300ms range
        }

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Conversations/Second',
                    data: processingData,
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Response Time (ms)',
                    data: responseData,
                    borderColor: '#198754',
                    backgroundColor: 'rgba(25, 135, 84, 0.1)',
                    fill: false,
                    tension: 0.4,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Conversations/Second'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Response Time (ms)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }

    setupStatsUpdates() {
        // Simulate real-time stats updates
        this.statsUpdateInterval = setInterval(() => {
            this.updateRealtimeStats();
        }, 5000); // Update every 5 seconds
    }

    updateRealtimeStats() {
        // Update system status indicators
        const statusElements = document.querySelectorAll('[data-realtime-stat]');
        
        statusElements.forEach(element => {
            const statType = element.getAttribute('data-realtime-stat');
            
            switch (statType) {
                case 'uptime':
                    // Simulate uptime increase
                    const currentUptime = element.textContent;
                    if (currentUptime.includes('days')) {
                        const days = parseInt(currentUptime);
                        if (!isNaN(days)) {
                            element.textContent = `${days} days`;
                        }
                    }
                    break;
                    
                case 'memory':
                    // Simulate memory usage fluctuation
                    const memUsage = 150 + Math.floor(Math.random() * 100);
                    element.textContent = `${memUsage}MB`;
                    break;
                    
                case 'cpu':
                    // Simulate CPU usage
                    const cpuUsage = 5 + Math.floor(Math.random() * 20);
                    element.textContent = `${cpuUsage}%`;
                    break;
            }
        });

        // Update last updated timestamp
        const timestampElements = document.querySelectorAll('[data-timestamp]');
        timestampElements.forEach(element => {
            element.textContent = new Date().toLocaleTimeString();
        });
    }

    setupAnimations() {
        // Intersection Observer for scroll animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                    
                    // Animate counters
                    if (entry.target.classList.contains('metric-value')) {
                        this.animateCounter(entry.target);
                    }
                }
            });
        }, observerOptions);

        // Observe elements for animation
        document.querySelectorAll('.feature-card, .tech-card, .metric-card, .highlight-card').forEach(el => {
            observer.observe(el);
        });

        // Observe metric values for counter animation
        document.querySelectorAll('.metric-value').forEach(el => {
            observer.observe(el);
        });
    }

    animateCounter(element) {
        const target = element.textContent;
        const isNumeric = /^\d+(\.\d+)?$/.test(target);
        
        if (!isNumeric) return;

        const targetValue = parseFloat(target);
        const duration = 2000; // 2 seconds
        const steps = 60;
        const stepValue = targetValue / steps;
        const stepDuration = duration / steps;
        
        let current = 0;
        element.textContent = '0';

        const timer = setInterval(() => {
            current += stepValue;
            if (current >= targetValue) {
                element.textContent = target; // Restore original formatting
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(current).toString();
            }
        }, stepDuration);
    }

    startRealTimeUpdates() {
        // Simulate API calls for real-time data
        this.fetchSystemHealth();
        
        // Set up periodic health checks
        setInterval(() => {
            this.fetchSystemHealth();
        }, 30000); // Every 30 seconds
    }

    async fetchSystemHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            
            this.updateSystemStatus(data);
        } catch (error) {
            console.log('Health check simulation - using mock data');
            this.updateSystemStatus({
                status: 'healthy',
                system: 'operational',
                performance: 'excellent'
            });
        }
    }

    updateSystemStatus(healthData) {
        // Update status badges
        const statusBadges = document.querySelectorAll('.badge');
        statusBadges.forEach(badge => {
            if (badge.textContent.includes('System')) {
                badge.className = healthData.status === 'healthy' ? 
                    'badge bg-success fs-6' : 'badge bg-warning fs-6';
            }
        });

        // Update health indicators
        const healthIndicators = document.querySelectorAll('.health-item .badge');
        healthIndicators.forEach(indicator => {
            if (indicator.textContent === 'Active' || indicator.textContent === 'Connected') {
                indicator.className = 'badge bg-success';
            }
        });
    }

    // Utility method for formatting numbers
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    // Method to handle demo mode toggles
    toggleDemoMode() {
        const body = document.body;
        body.classList.toggle('demo-mode');
        
        if (body.classList.contains('demo-mode')) {
            this.showDemoNotification('Demo mode activated - showing enhanced metrics');
        } else {
            this.showDemoNotification('Demo mode deactivated');
        }
    }

    showDemoNotification(message) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'alert alert-info alert-dismissible fade show position-fixed';
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }

    // Cleanup method
    destroy() {
        if (this.statsUpdateInterval) {
            clearInterval(this.statsUpdateInterval);
        }
    }
}

// Initialize portfolio app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.portfolioApp = new PortfolioApp();
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.portfolioApp) {
        window.portfolioApp.destroy();
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PortfolioApp;
}