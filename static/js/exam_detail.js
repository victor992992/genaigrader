// Función para obtener el token CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Configuración de DataTables
$(document).ready(function() {
    $('#evaluationsTable').DataTable({
        dom: 'Bfrtip',
        buttons: [
            {
                extend: 'csv',
                text: 'Exportar CSV',
                filename: 'evaluaciones_' + new Date().toISOString().split('T')[0],
                exportOptions: {
                    columns: [0, 1, 2, 3, 4], // Excluir columna de acciones
                    format: {
                        body: function(data, row, column, node) {
                            return data.replace(/<[^>]*>/g, '').replace(/�/g, '✓');
                        }
                    }
                },
                customize: function(csv) {
                    return 'Fecha,Modelo,Prompt,Nota,Tiempo\n' + csv;
                }
            },
            {
                extend: 'pdf',
                text: 'Exportar PDF',
                filename: 'evaluaciones_' + new Date().toISOString().split('T')[0],
                exportOptions: {
                    columns: [0, 1, 2, 3, 4], // Excluir columna de acciones
                    stripHtml: true
                },
                customize: function(doc) {
                    doc.pageOrientation = 'landscape';
                    doc.content[1].table.widths = ['15%', '20%', '35%', '15%', '15%'];
                    doc.styles.tableHeader = {
                        fillColor: '#3498db',
                        color: '#ffffff',
                        alignment: 'left'
                    };
                    doc.defaultStyle.fontSize = 10;
                    doc.content[0].text = 'Historial de Evaluaciones - ' + document.querySelector('.course-name').textContent;
                    doc.content[0].alignment = 'center';
                    doc.content[0].margin = [0, 0, 0, 15];
                    doc.content[1].layout = {
                        hLineWidth: function(i, node) { return (i === 0 || i === node.table.body.length) ? 2 : 1; },
                        vLineWidth: function(i, node) { return 0; },
                        hLineColor: function(i) { return '#3498db'; },
                        paddingLeft: function(i) { return 5; },
                        paddingRight: function(i) { return 5; }
                    };
                }
            }
        ],
        order: [[0, 'desc']],
        columnDefs: [
            { orderable: true, targets: [0,1,2,3] },
            { orderable: false, targets: [4] },
            { width: '15%', targets: [0,3,4] },
            { className: 'dt-body-center', targets: [3,4] }
        ],
        language: {
            url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json',
            buttons: {
                csv: 'Exportar CSV',
                pdf: 'Exportar PDF'
            }
        }
    });

    if(document.getElementById('modelAveragesChart')) {
            initializeChart();
    }
});

function deleteEvaluation(button) {
    const row = $(button).closest('tr');
    const evalId = row.data('eval-id');
    const table = $('#evaluationsTable').DataTable();

    if (confirm('¿Borrar esta evaluación?')) {
        fetch(`/evaluation/delete/${evalId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        }).then(response => {
            if(response.ok) {
                table.row(row).remove().draw(false);
            } else {
                alert('Error al eliminar');
            }
        });
    }
}
