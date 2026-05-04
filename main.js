// E-Shop JS Enhancements

document.addEventListener('DOMContentLoaded', function() {
    // Confirm deletes
    const deleteLinks = document.querySelectorAll('[onclick*="confirm"]');
    deleteLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (!confirm('Are you sure?')) e.preventDefault();
        });
    });

    // Auto-refresh dashboard logs every 10s
    if (window.location.pathname === '/dashboard') {
        setInterval(() => {
            location.reload();
        }, 10000);
    }

    // Smooth scroll
    document.querySelectorAll('a[href^=\"#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
});

// AJAX for cart updates (future)
function updateCart(productId, qty) {
    fetch(`/cart/add/${productId}`, {method: 'POST'})
        .then(() => location.reload());
}

