document.addEventListener('DOMContentLoaded', function () {
    const themeToggle = document.getElementById('theme-toggle');

    // Function to change font color based on the body class
    function updateFontColor() {
        const contentBlock = document.querySelector('.content main');
        if (document.body.classList.contains('dark')) {
            contentBlock.style.color = 'white'; // or 'cream'
        } else {
            contentBlock.style.color = ''; // Reset to default
        }
    }

    // Function to apply the dark mode class based on local storage
    function applyDarkModePreference() {
        const darkMode = localStorage.getItem('darkMode');
        if (darkMode === 'enabled') {
            document.body.classList.add('dark');
            themeToggle.checked = true;
        } else {
            document.body.classList.remove('dark');
            themeToggle.checked = false;
        }
        updateFontColor();
    }

    // Apply the preference on page load
    applyDarkModePreference();

    // Event listener for the theme toggle
    themeToggle.addEventListener('change', function () {
        if (this.checked) {
            document.body.classList.add('dark');
            localStorage.setItem('darkMode', 'enabled');
        } else {
            document.body.classList.remove('dark');
            localStorage.setItem('darkMode', 'disabled');
        }
        updateFontColor();
    });

    // Observe changes to the class attribute of the body element
    const observer = new MutationObserver(updateFontColor);
    observer.observe(document.body, {attributes: true, attributeFilter: ['class']});
});
