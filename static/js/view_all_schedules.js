let groupColumn = 3;
let table = $('#view_all_schedules').DataTable({
    columnDefs: [{visible: false, targets: groupColumn}],
    order: [[groupColumn, 'asc']],
    displayLength: 25,
    drawCallback: function (settings) {
        let api = this.api();
        let rows = api.rows({page: 'current'}).nodes();
        let last = null;

        api.column(groupColumn, {page: 'current'})
            .data()
            .each(function (group, i) {
                if (last !== group) {
                    $(rows)
                        .eq(i)
                        .before(
                            '<tr class="group"><td colspan="5">' +
                            group +
                            '</td></tr>'
                        );

                    last = group;
                }
            });
    }
});

// Order by the grouping
$('#view_all_schedules tbody').on('click', 'tr.group', function () {
    let currentOrder = table.order()[0];
    if (currentOrder[0] === groupColumn && currentOrder[1] === 'asc') {
        table.order([groupColumn, 'desc']).draw();
    } else {
        table.order([groupColumn, 'asc']).draw();
    }
});