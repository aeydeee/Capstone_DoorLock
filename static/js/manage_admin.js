const table = new DataTable('#manage_admin', {
    columnDefs: [
        {
            searchable: false,
            orderable: false,
            targets: 0
        }
    ],
    order: [[1, 'asc']]
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