document.addEventListener("DOMContentLoaded", function () {
    const courseSelect = document.getElementById('course');
    const yearLevelSelect = document.getElementById('year_level');
    const semesterSelect = document.getElementById('semester');

    courseSelect.addEventListener('change', function () {
        fetchOptions('/get_year_levels', {course_id: this.value}, yearLevelSelect);
    });

    yearLevelSelect.addEventListener('change', function () {
        fetchOptions('/get_semesters', {year_level_id: this.value}, semesterSelect);
    });

    function fetchOptions(url, params, selectElement) {
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        })
            .then(response => response.json())
            .then(data => {
                selectElement.innerHTML = '';
                data.forEach(item => {
                    const option = document.createElement('option');
                    option.value = item.id;
                    option.textContent = item.name;
                    selectElement.appendChild(option);
                });
            });
    }
});
