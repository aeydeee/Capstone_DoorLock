const table = new DataTable('#course_details', {
    columnDefs: [
        {
            searchable: true,
            orderable: false,
            targets: 0
        }
    ],
    order: [[2, 'asc']],
    rowGroup: {
        dataSrc: 5
    }
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

