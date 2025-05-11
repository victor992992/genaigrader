document.addEventListener("DOMContentLoaded", () => {
    const getCookie = (name) => {
        const cookies = document.cookie.split(';');
        for(let cookie of cookies) {
            const [key, value] = cookie.trim().split('=');
            if(key === name) return decodeURIComponent(value);
        }
        return null;
    };

    // Mostrar formulario
    document.getElementById('show-form').addEventListener('click', () => {
        document.getElementById('creation-form').style.display = 'block';
    });

    // Crear nuevo modelo
    document.getElementById('create-btn').addEventListener('click', createModel);

    // Manejador principal para la tabla
    document.getElementById('model-table').addEventListener('click', async (e) => {
        const target = e.target;
        const row = target.closest('tr');
        if (!row) return;
        
        const modelId = row.dataset.id;

        // Eliminar
        if (target.classList.contains('delete-btn')) {
            if (confirm('¿Borrar este modelo?')) {
                try {
                    const response = await fetch(`/model/delete/${modelId}/`, {
                        method: 'DELETE',
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken')
                        }
                    });
                    
                    if (response.ok) {
                        row.remove();
                    } else {
                        const data = await response.json();
                        throw new Error(data.message || 'Error al borrar');
                    }
                } catch(error) {
                    alert(error.message);
                }
            }
        }
        
        // Editar
        if (target.classList.contains('edit-btn')) {
            enterEditMode(row);
        }
        
        // Guardar cambios
        if (target.classList.contains('save-btn')) {
            await saveChanges(row, modelId);
        }
        
        // Cancelar edición
        if (target.classList.contains('cancel-btn')) {
            cancelEdit(row);
        }
    });

    // Función para crear modelo
    async function createModel() {
        const desc = document.getElementById('desc').value.trim();
        const url = document.getElementById('url').value.trim();
        const key = document.getElementById('key').value.trim();

        if (!desc || !url || !key) {
            alert('Todos los campos son obligatorios');
            return;
        }

        try {
            const response = await fetch('/model/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: new URLSearchParams({description: desc, api_url: url, api_key: key})
            });
            
            const data = await response.json();
            
            if (response.ok) {
                const newRow = `
                    <tr data-id="${data.model.id}">
                        <td data-full-value="${data.model.description}">${data.model.description}</td>
                        <td data-full-value="${data.model.api_url}">${data.model.api_url}</td>
                        <td data-full-value="${data.model.api_key}">${data.model.api_key.substring(0,10)}...</td>
                        <td>
                            <button class="edit-btn">Editar</button>
                            <button class="delete-btn">Borrar</button>
                        </td>
                    </tr>
                `;
                document.querySelector('#model-table tbody').insertAdjacentHTML('afterbegin', newRow);
                
                document.getElementById('creation-form').style.display = 'none';
                document.getElementById('desc').value = '';
                document.getElementById('url').value = '';
                document.getElementById('key').value = '';
            } else {
                throw new Error(data.message || 'Error del servidor');
            }
        } catch(error) {
            console.error('Error:', error);
            alert('Error al crear modelo: ' + error.message);
        }
    }

    // Modo edición
    function enterEditMode(row) {
        const cells = row.querySelectorAll('td');
        const [descCell, urlCell, keyCell, actionsCell] = cells;
        
        row.originalContent = {
            description: descCell.dataset.fullValue,
            url: urlCell.dataset.fullValue,
            key: keyCell.dataset.fullValue,
            html: actionsCell.innerHTML
        };

        descCell.innerHTML = `<input type="text" value="${row.originalContent.description}" class="edit-input">`;
        urlCell.innerHTML = `<input type="text" value="${row.originalContent.url}" class="edit-input">`;
        keyCell.innerHTML = `<input type="text" value="${row.originalContent.key}" class="edit-input">`;

        actionsCell.innerHTML = `
            <button class="save-btn">Guardar</button>
            <button class="cancel-btn">Cancelar</button>
        `;
    }

    // Guardar cambios
    async function saveChanges(row, modelId) {
        const inputs = row.querySelectorAll('.edit-input');
        const newData = {
            description: inputs[0].value,
            api_url: inputs[1].value,
            api_key: inputs[2].value
        };

        try {
            const response = await fetch(`/model/update/${modelId}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: new URLSearchParams(newData)
            });

            if (response.ok) {
                const cells = row.querySelectorAll('td');
                cells[0].dataset.fullValue = newData.description;
                cells[1].dataset.fullValue = newData.api_url;
                cells[2].dataset.fullValue = newData.api_key;
                
                cells[0].textContent = newData.description;
                cells[1].textContent = newData.api_url;
                cells[2].textContent = newData.api_key.length > 10 
                    ? newData.api_key.substring(0, 7) + '...' 
                    : newData.api_key;
                
                cells[3].innerHTML = row.originalContent.html;
            } else {
                const data = await response.json();
                throw new Error(data.message || 'Error al guardar');
            }
        } catch(error) {
            alert(error.message);
            cancelEdit(row);
        }
    }

    // Cancelar edición
    function cancelEdit(row) {
        const cells = row.querySelectorAll('td');
        cells[0].textContent = row.originalContent.description;
        cells[1].textContent = row.originalContent.url;
        cells[2].textContent = row.originalContent.key.length > 10 
            ? row.originalContent.key.substring(0, 7) + '...' 
            : row.originalContent.key;
        cells[3].innerHTML = row.originalContent.html;
    }

    document.getElementById('download-form').addEventListener('submit', function (e) {
        e.preventDefault();

        const modelName = document.getElementById('model-name').value;
        const messageBox = document.getElementById('message');

        fetch('/model/pull/', {
            method: 'POST',
            headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'), // Usar getCookie existente
            },
            body: JSON.stringify({ model: modelName })
        })
        .then(response => response.json())
        .then(data => {
            messageBox.style.display = 'block';
            if (data.status === 'success') {
            messageBox.textContent = data.message;
            messageBox.className = 'message success';
            // Actualizar la tabla si es necesario
            location.reload();
            } else {
            messageBox.textContent = data.message;
            messageBox.className = 'message error';
            }
    })
    .catch(error => {
        messageBox.style.display = 'block';
        messageBox.textContent = 'Error al conectar con el servidor.';
        messageBox.className = 'message error';
    });
    });

});