// static/js/script.js
document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('.view-toggle .button');
    buttons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            window.location.href = button.href;
        });
    });

    // Smooth scrolling for pagination links
    const paginationLinks = document.querySelectorAll('.pagination a');
    paginationLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            if (!this.classList.contains('disabled')) {
                event.preventDefault();
                window.scrollTo({ top: 0, behavior: 'smooth' });
                window.location.href = link.href;
            }
        });
    });
});