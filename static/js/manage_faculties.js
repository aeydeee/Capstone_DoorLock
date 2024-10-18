document.addEventListener('DOMContentLoaded', function () {


    const csrfToken = document.getElementById('csrf_token').value;

    function format(d) {
        let courses = d.courses.map(subj => `<li>${subj.code}: ${subj.name}</li>`).join('');
        return ('<dl>' + '<dt>Full name:</dt>' + '<dd>' + d.full_name + '</dd>' + '<dt>Designation:</dt>' + '<dd>' + d.designation + '</dd>' + '<dt>Department:</dt>' + '<dd>' + d.faculty_department + '</dd>' + '<dt>Email:</dt>' + '<dd>' + d.email + '</dd>' + '<dt>Current Courses Handled:</dt>' + '<dd><ul>' + courses + '</ul></dd>' + '</dl>');
    }

    const table = new DataTable('#manage_faculties', {
        ajax: {
            url: '/faculties/api/faculty_data',
            dataSrc: 'data'
        },
        columns: [
            {className: 'dt-control', orderable: false, data: null, defaultContent: '', searchable: false},
            {
                data: null, orderable: false, searchable: false, render: function (data, type, row, meta) {
                    return meta.row + meta.settings._iDisplayStart + 1;
                }
            },
            {data: 'profile'}, // Profile column
            {data: 'faculty_number'},
            {data: 'l_name'},
            {data: 'f_name'},
            {data: 'm_name'},
            {
                data: 'gender', render: function (data, type, row) {
                    return data === 'female' ? 'F' : data === 'male' ? 'M' : data;
                }
            },
            {
                data: null, orderable: false, render: function (data, type, row) {
                    return `
                    <a href="/schedules/view_schedule/${data.id}" class="btn btn-sm view-button" data-tooltip="View Schedules">
                        <img src="/static/images/icons/view.png" alt="Eye Icon" class="icon-small">
                    </a>
                    <a href="/faculties/edit/${data.id}" class="btn btn-sm btn-info">
                        <img src="/static/images/icons/pencil-fill.svg" alt="Pencil Icon">
                    </a>
                    <a href="#" class="btn btn-sm btn-danger" data-bs-toggle="modal" data-bs-target="#deleteModal${data.id}">
                        <img src="/static/images/icons/trash-fill.svg" alt="Trash Icon">
                    </a>
                    <div class="modal fade" id="deleteModal${data.id}" tabindex="-1" aria-labelledby="deleteModalLabel${data.id}" aria-hidden="true">
                        <div class="modal-dialog">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title" id="deleteModalLabel${data.id}">Confirm Delete</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                </div>
                                <div class="modal-body">
                                    Are you sure you want to delete ${data.full_name}?
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                    <form method="POST" action="/faculties/delete/${data.id}">
                                        <input type="hidden" name="csrf_token" value="${csrfToken}">
                                        <button type="submit" class="btn btn-danger">Delete</button>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                }
            }
        ],
        order: [[2, 'asc']],
        rowCallback: function (row, data, index) {
            const pageInfo = table.page.info();
            $('td:eq(1)', row).html(pageInfo.start + index + 1);
        }
    });


    $('#manage_faculties tbody').on('click', 'td.dt-control', function () {
        let tr = $(this).closest('tr');
        let row = table.row(tr);

        if (row.child.isShown()) {
            row.child.hide();
            tr.removeClass('shown');
        } else {
            row.child(format(row.data())).show();
            tr.addClass('shown');
        }
    });


});

