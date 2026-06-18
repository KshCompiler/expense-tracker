// main.js — students will add JavaScript here as features are built

document.addEventListener('DOMContentLoaded', function() {
    // Check for flash messages and show success modal if applicable
    const flashMessages = document.querySelectorAll('.flash-message');

    flashMessages.forEach(function(message) {
        const category = message.getAttribute('data-category');
        const text = message.getAttribute('data-message');

        // Show success modal for success messages
        if (category === 'success') {
            showSuccessModal(text);
        }

        // Remove flash message after 5 seconds
        setTimeout(function() {
            message.style.animation = 'slideOut 0.3s ease-out';
            message.addEventListener('animationend', function() {
                message.remove();
            });
        }, 5000);
    });

    function showSuccessModal(description) {
        const modal = document.getElementById('successModal');
        const modalDescription = modal.querySelector('.modal-description');
        const progressBar = modal.querySelector('.progress-bar');

        // Set the description
        modalDescription.textContent = description;

        // Show the modal
        modal.style.display = 'block';

        // Animate the progress bar
        setTimeout(function() {
            progressBar.style.width = '100%';
        }, 100);

        // Auto-dismiss modal after 4 seconds (within 3-5 second spec range)
        setTimeout(function() {
            modal.style.display = 'none';
            // Optional: reset progress bar for next use
            progressBar.style.width = '0%';
        }, 4000);

        // Redirect after 4.5 seconds (slightly after modal starts dismissing)
        setTimeout(function() {
            window.location.href = '/'; // Redirect to home page
        }, 4500);
    }

    // Close modal if clicked outside
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('successModal');
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
});
