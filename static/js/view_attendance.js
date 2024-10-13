const table = new DataTable('#view_attendance', {
    columnDefs: [
        {
            searchable: false,
            orderable: false,
            targets: 0
        }
    ],
    order: [[0, 'desc']]
});

