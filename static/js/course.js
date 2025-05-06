function createCourse() {
    const nameInput = document.getElementById('new-course-name');
    const name = nameInput.value.trim();
    
    if (!name) {
        alert('Por favor ingresa un nombre válido');
        return;
    }

    fetch('/course/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: `course_name=${encodeURIComponent(name)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            nameInput.value = '';
            location.reload(); // Recargar para mostrar el nuevo curso
        } else {
            alert(`Error: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al crear la asignatura');
    });
}

function editCourse(button) {
    const courseItem = button.closest('.course-item');
    const courseId = courseItem.dataset.courseId;
    const nameSpan = courseItem.querySelector('.course-name');
    const currentName = nameSpan.textContent;
    
    // Crear elementos de edición
    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentName;
    input.className = 'edit-input';
    
    const saveBtn = document.createElement('button');
    saveBtn.textContent = 'Guardar';
    saveBtn.className = 'save-btn';
    
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Cancelar';
    cancelBtn.className = 'cancel-btn';
    
    // Reemplazar elemento
    const editContainer = document.createElement('div');
    editContainer.className = 'edit-container';
    editContainer.appendChild(input);
    editContainer.appendChild(saveBtn);
    editContainer.appendChild(cancelBtn);
    
    nameSpan.replaceWith(editContainer);
    input.focus();
    
    // Manejar guardado
    saveBtn.onclick = () => {
        const newName = input.value.trim();
        if (!newName) return;
        
        fetch(`/course/update/${courseId}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: `name=${encodeURIComponent(newName)}`
        }).then(response => {
            if (response.ok) {
                nameSpan.textContent = newName;
                editContainer.replaceWith(nameSpan);
            }
        });
    };
    
    // Manejar cancelación
    cancelBtn.onclick = () => {
        editContainer.replaceWith(nameSpan);
    };
}

function deleteCourse(button) { // Recibir el botón como parámetro
    const courseItem = button.closest('.course-item');
    const courseId = courseItem.dataset.courseId;
    
    // Crear elementos de confirmación
    const confirmationDiv = document.createElement('div');
    confirmationDiv.className = 'confirmation-box';
    
    const confirmText = document.createElement('span');
    confirmText.textContent = '¿Eliminar asignatura?';
    
    const confirmBtn = document.createElement('button');
    confirmBtn.textContent = '✓';
    confirmBtn.className = 'confirm-delete-btn';
    
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = '✕';
    cancelBtn.className = 'cancel-delete-btn';
    
    // Insertar elementos
    confirmationDiv.appendChild(confirmText);
    confirmationDiv.appendChild(confirmBtn);
    confirmationDiv.appendChild(cancelBtn);
    
    // Reemplazar botones originales
    const actionsDiv = courseItem.querySelector('.course-actions');
    actionsDiv.replaceWith(confirmationDiv);
    
    // Manejar confirmación
    confirmBtn.onclick = () => {
        fetch(`/course/delete/${courseId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        }).then(response => {
            if (response.ok) {
                courseItem.remove(); // Eliminar elemento del DOM sin recargar
            } else {
                location.reload(); // Recargar si hay error
            }
        });
    };
    
    // Manejar cancelación
    cancelBtn.onclick = () => {
        confirmationDiv.replaceWith(actionsDiv); // Restaurar botones originales
    };
}

// Función para obtener el token CSRF (sin cambios)
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

function editExam(button) {
    const examItem = button.closest('.exam-item');
    const examId = examItem.dataset.examId;
    const examContent = examItem.querySelector('.exam-content');
    const examLink = examContent.querySelector('.exam-link');
    const originalUrl = examLink.dataset.url; // URL desde data-url
    const currentDescription = examContent.querySelector('.exam-description').textContent;

    // Crear elementos de edición
    const editContainer = document.createElement('div');
    editContainer.className = 'exam-edit-container';

    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentDescription;
    input.className = 'exam-edit-input';

    const saveBtn = document.createElement('button');
    saveBtn.textContent = 'Guardar';
    saveBtn.className = 'exam-save-btn';

    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Cancelar';
    cancelBtn.className = 'exam-cancel-btn';

    // Reemplazar contenido
    examContent.replaceWith(editContainer);
    editContainer.append(input, saveBtn, cancelBtn);
    input.focus();

    // Función para restaurar el contenido
    const restoreContent = (description) => {
        const newExamContent = document.createElement('div');
        newExamContent.className = 'exam-content';

        const newLink = document.createElement('a');
        newLink.className = 'exam-link';
        newLink.href = originalUrl; // Usamos la URL guardada
        newLink.dataset.url = originalUrl;

        const newDescription = document.createElement('span');
        newDescription.className = 'exam-description';
        newDescription.textContent = description;

        const newActions = document.createElement('div');
        newActions.className = 'exam-actions';

        const newEditBtn = document.createElement('button');
        newEditBtn.className = 'edit-btn';
        newEditBtn.textContent = '✏️';
        newEditBtn.onclick = () => editExam(newEditBtn); // Reconectar evento

        const newDeleteBtn = document.createElement('button');
        newDeleteBtn.className = 'delete-btn';
        newDeleteBtn.textContent = '🗑️';
        newDeleteBtn.onclick = () => deleteExam(newDeleteBtn); // Reconectar evento

        // Construir estructura
        newLink.appendChild(newDescription);
        newActions.append(newEditBtn, newDeleteBtn);
        newExamContent.append(newLink, newActions);
        
        // Reemplazar en el DOM
        editContainer.replaceWith(newExamContent);
    };

    // Manejador de Guardar
    saveBtn.onclick = async (e) => {
        e.stopPropagation(); // Importante!
        const newDescription = input.value.trim();
        
        if (!newDescription) return;

        try {
            const response = await fetch(`/course/exam/update/${examId}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: `description=${encodeURIComponent(newDescription)}`
            });
            
            if (response.ok) {
                restoreContent(newDescription);
            }
        } catch (error) {
            console.error('Error:', error);
        }
    };

    // Manejador de Cancelar
    cancelBtn.onclick = (e) => {
        e.stopPropagation();
        restoreContent(currentDescription);
    };
}
function deleteExam(button) {
    const examItem = button.closest('li');
    const examId = examItem.dataset.examId;
    
    if (confirm('¿Eliminar este examen?')) {
        fetch(`/course/exam/delete/${examId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        }).then(response => {
            if (response.ok) {
                examItem.remove(); // Eliminar del DOM sin recargar
            }
        });
    }
}