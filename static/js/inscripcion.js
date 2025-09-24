document.addEventListener("DOMContentLoaded", function() {
  const input_correo = document.getElementById("busquedaCorreo");
  const sugerencias = document.getElementById("sugerencias");
  const tablaMiembrosTbody = document.querySelector("#tablaMiembros tbody");
  let sugerencias_actuales = [];
  let draggedRow = null;

  const filas = tablaMiembrosTbody.querySelectorAll("tr");
  filas.forEach(row => {
    attachRowEvents(row);
  });

  // Búsqueda para las sugerencias
  input_correo.addEventListener("input", function() {
    const term = this.value.trim();
    if (term.length < 4) {
      sugerencias.style.display = "none";
      return;
    }

    fetch(`/inscripcion/buscar_usuario?term=${encodeURIComponent(term)}`)
      .then(response => response.json())
      .then(data => {
        sugerencias_actuales = data;
        populateSuggestions(sugerencias_actuales);
      })
      .catch(error => {
        console.error("Error en la búsqueda:", error);
        sugerencias.style.display = "none";
      });
  });

  // Cerrar sugerencias al hacer clic fuera
  document.addEventListener("click", function(e) {
    if (!sugerencias.contains(e.target) && e.target !== input_correo) {
      sugerencias.style.display = "none";
    }
  });

  // Rellena el menú de sugerencias
  function populateSuggestions(suggestionsList) {
    sugerencias.innerHTML = "";
    if (suggestionsList.length === 0) {
      const li = document.createElement("li");
      li.className = "suggestion-item disabled";
      li.textContent = "No se encontraron usuarios.";
      sugerencias.appendChild(li);
      sugerencias.style.display = "block";
      return;
    }

    suggestionsList.forEach(item => {
      const li = document.createElement("li");
      li.className = "suggestion-item";

      // ✅ Muestra solo el correo visualmente
      li.textContent = item.correo;

      // ✅ Guarda toda la info como dataset
      li.dataset.item = JSON.stringify(item);
      li.setAttribute("draggable", "true");

      li.addEventListener("click", function() {
        const itemData = JSON.parse(this.dataset.item);
        if (!existeMiembro(itemData)) {
          agregarMiembroEnCasilla(itemData);
          input_correo.value = "";
          sugerencias.style.display = "none";
        } else {
          alert("Esta persona ya ha sido asignada.");
        }
      });

      li.addEventListener("dragstart", function(e) {
        e.dataTransfer.setData("application/json", this.dataset.item);
        li.classList.add("dragging");
      });

      li.addEventListener("dragend", function() {
        li.classList.remove("dragging");
      });

      sugerencias.appendChild(li);
    });

    sugerencias.style.display = "block";
  }

  function existeMiembro(item) {
    const rows = tablaMiembrosTbody.querySelectorAll("tr[data-filled='true']");
    for (let row of rows) {
      let data = JSON.parse(row.dataset.member);
      if (data.correo === item.correo) {
        return true;
      }
    }
    return false;
  }

  function agregarMiembroEnCasilla(item) {
    const row = obtenerFilaVacia();
    if (!row) {
      alert("El equipo ya tiene 3 integrantes asignados.");
      return;
    }
    updateRow(row, item);
    actualizarRoles();
  }

  function obtenerFilaVacia() {
    const rows = tablaMiembrosTbody.querySelectorAll("tr");
    for (let row of rows) {
      if (row.getAttribute("data-filled") !== "true") {
        return row;
      }
    }
    return null;
  }

  function updateRow(row, item) {
    const newRow = row.cloneNode(false);
    newRow.setAttribute("data-filled", "true");
    newRow.dataset.member = JSON.stringify(item);
    newRow.innerHTML = `
      <td>${item.correo}<input type="hidden" name="correos[]" value="${item.correo}"></td>
      <td>${item.nombre}</td>
      <td>${item.apellido}</td>
      <td class="role"></td>
      <td><button class="delete-btn">Eliminar</button></td>
    `;
    row.replaceWith(newRow);
    newRow.querySelector(".delete-btn").addEventListener("click", function() {
      resetRow(newRow);
      actualizarRoles();
    });
    attachRowEvents(newRow);
  }

  function resetRow(row) {
    const newRow = row.cloneNode(false);
    newRow.removeAttribute("data-filled");
    delete newRow.dataset.member;
    newRow.setAttribute("draggable", "false");
    newRow.innerHTML = `<td colspan="5" class="table-placeholder">Arrastra un integrante aquí</td>`;
    row.replaceWith(newRow);
    attachRowEvents(newRow);
  }

  function swapRows(row1, row2) {
    const data1 = row1.dataset.member ? JSON.parse(row1.dataset.member) : null;
    const data2 = row2.dataset.member ? JSON.parse(row2.dataset.member) : null;

    if (data1 && data2) {
      updateRowCells(row1, data2);
      updateRowCells(row2, data1);
    } else if (data1 && !data2) {
      updateRow(row2, data1);
      resetRow(row1);
    } else if (!data1 && data2) {
      updateRow(row1, data2);
      resetRow(row2);
    }

    actualizarRoles();
  }

  function updateRowCells(row, item) {
    const cells = row.querySelectorAll("td");
    cells[0].textContent = item.correo;
    cells[1].textContent = item.nombre;
    cells[2].textContent = item.apellido;
    const roleCell = row.querySelector(".role");
    roleCell.textContent = '';
    row.dataset.member = JSON.stringify(item);
  }

  function attachRowEvents(row) {
    if (row.getAttribute("data-filled") === "true") {
      row.setAttribute("draggable", "true");
    } else {
      row.removeAttribute("draggable");
    }

    row.addEventListener("dragover", function(e) {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
    });

    row.addEventListener("drop", function(e) {
      e.preventDefault();
      e.stopPropagation();

      const dataFromSuggestion = e.dataTransfer.getData("application/json");

      if (!draggedRow && dataFromSuggestion) {
        if (row.getAttribute("data-filled") !== "true") {
          const itemData = JSON.parse(dataFromSuggestion);
          if (!existeMiembro(itemData)) {
            updateRow(row, itemData);
            actualizarRoles();
          } else {
            alert("Esta persona ya ha sido asignada.");
          }
        } else {
          alert("Esta casilla ya está ocupada. Arrastra sobre una casilla vacía para asignar un integrante.");
        }
      } else if (draggedRow && draggedRow !== row) {
        swapRows(draggedRow, row);
      }

      draggedRow = null;
    });

    row.addEventListener("dragstart", function(e) {
      if (row.getAttribute("data-filled") === "true") {
        draggedRow = row;
        row.classList.add("row-dragging");
        e.dataTransfer.effectAllowed = "move";
        e.dataTransfer.setData("application/json", row.dataset.member);
      } else {
        e.preventDefault();
      }
    });

    row.addEventListener("dragend", function() {
      row.classList.remove("row-dragging");
      draggedRow = null;
    });
  }

  function actualizarRoles() {
    let filledCount = 0;
    const rows = tablaMiembrosTbody.querySelectorAll("tr");
    rows.forEach(row => {
      const roleCell = row.querySelector(".role");
      if (row.getAttribute("data-filled") === "true") {
        roleCell.textContent = filledCount === 0 ? "Capitán" : "Integrante";
        filledCount++;
      } else if (roleCell) {
        roleCell.textContent = "";
      }
    });
  }
});