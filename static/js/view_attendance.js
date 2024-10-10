const table = new DataTable('#view_attendance', {
    columnDefs: [
        {
            searchable: false,
            orderable: false,
            targets: 0
        }
    ],
    order: [[3, 'desc']]
});

table
    .on('order.dt search.dt', function () {
        let i = 1;

        table
            .cells(null, 0, {search: 'applied', order: 'applied'})
            .every(function (cell) {
                this.data(i++);
            });
    })
    .draw();