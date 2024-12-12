class NotificationManager {
    constructor() {
        this.container = document.createElement('div');
        this.container.className = 'fixed top-4 right-4 z-50 space-y-2';
        document.body.appendChild(this.container);
    }

    show(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `
            notification p-4 rounded shadow-lg transform translate-x-full transition-transform duration-300
            ${this.getTypeClass(type)}
        `;
        notification.textContent = message;

        this.container.appendChild(notification);
        
        // Trigger animation
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 10);

        // Remove notification
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                this.container.removeChild(notification);
            }, 300);
        }, duration);
    }

    getTypeClass(type) {
        switch (type) {
            case 'success':
                return 'bg-green-500 text-white';
            case 'error':
                return 'bg-red-500 text-white';
            case 'warning':
                return 'bg-yellow-500 text-white';
            default:
                return 'bg-blue-500 text-white';
        }
    }
}

const notifications = new NotificationManager();

// Export for use in other files
window.notifications = notifications;