document.addEventListener("DOMContentLoaded", function () {
  const inputCorreo = document.getElementById("busquedaCorreo");
  const sugerencias = document.getElementById("sugerencias");
  const tableBody = document.querySelector("#tablaMiembros tbody");

  // Variable para identificar la fuente del drag ("suggestion" o "row")
  let dragSourceType = null;
  let draggedRow = null;

  // Inicializa los eventos de drag & drop en cada fila precreada
  Array.from(tableBody.children).forEach(row => {
    addRowDnDEvents(row);
  });

  // EVENTO: Autocomplete. Al escribir se traen las sugerencias
  inputCorreo.addEventListener("input", function () {
    const term = inputCorreo.value.trim();
    if (term.length < 2) {
      sugerencias.innerHTML = "";
      sugerencias.style.display = "none";
      return;
    }
    fetch(`/buscar_usuario?term=${encodeURIComponent(term)}`)
      .then(response => response.json())
      .then(data => {
        populateSuggestions(data);
      })
      .catch(error => {
        console.error("Error fetching suggestions:", error);
        sugerencias.innerHTML = "";
        sugerencias.style.display = "none";
      });
  });

  // Rellena el contenedor de sugerencias con los datos obtenidos
  function populateSuggestions(suggestionsData) {
    sugerencias.innerHTML = "";
    if (suggestionsData.length === 0) {
      sugerencias.style.display = "none";
      return;
    }
    suggestionsData.forEach(item => {
      const li = document.createElement("li");
      li.className = "list-group-item";
      li.textContent = `${item.value} - ${item.nombre} ${item.apellido}`;
      li.dataset.item = JSON.stringify(item);
      li.setAttribute("draggable", "true");

      // Al hacer click se intenta asignar el integrante al primer slot vacío
      li.addEventListener("click", function () {
        const data = JSON.parse(this.dataset.item);
        if (!existsInTable(data)) {
          addItemToFirstEmptyRow(data);
          inputCorreo.value = "";
          sugerencias.innerHTML = "";
          sugerencias.style.display = "none";
        } else {
          alert("Esta persona ya ha sido asignada");
        }
      });

      // Configura el drag para la sugerencia
      li.addEventListener("dragstart", function (e) {
        dragSourceType = "suggestion";
        e.dataTransfer.setData("application/json", this.dataset.item);
        e.dataTransfer.effectAllowed = "copy"; // Indica que es una operación de copia
        // Oculta las sugerencias después de iniciar el drag
        setTimeout(() => {
          sugerencias.innerHTML = "";
          sugerencias.style.display = "none";
        }, 0);
      });

      li.addEventListener("dragend", function () {
        // Resetea el tipo de fuente al finalizar el drag
        dragSourceType = null;
      });

      sugerencias.appendChild(li);
    });
    sugerencias.style.display = "block";
  }

  // Verifica si un integrante (según su "value") ya está en la tabla
  function existsInTable(item) {
    return Array.from(tableBody.children).some(row => {
      if (row.getAttribute("data-filled") === "true") {
        const data = JSON.parse(row.dataset.member);
        return data.value === item.value;
      }
      return false;
    });
  }

  // Inserta el integrante en el primer slot vacío
  function addItemToFirstEmptyRow(item) {
    const emptyRow = Array.from(tableBody.children).find(row =>
      row.getAttribute("data-filled") !== "true"
    );
    if (!emptyRow) {
      alert("No hay más espacios disponibles.");
      return;
    }
    fillRow(emptyRow, item);
    updateRoles();
  }

  // Rellena el slot (fila) con los datos del integrante y lo hace draggable
  function fillRow(row, item) {
    row.setAttribute("data-filled", "true");
    row.setAttribute("draggable", "true");
    row.dataset.member = JSON.stringify(item);
    row.innerHTML = `
      <td>${item.value}</td>
      <td>${item.nombre}</td>
      <td>${item.apellido}</td>
      <td class="role"></td>
      <td>
        <button class="btn btn-danger btn-sm">Eliminar</button>
      </td>
    `;
    row.querySelector("button").addEventListener("click", function () {
      clearRow(row);
      updateRoles();
    });
    // Vuelve a asignar los eventos de drag & drop a la fila
    addRowDnDEvents(row);
  }

  // Vuelve la fila a su estado vacío
  function clearRow(row) {
    row.removeAttribute("data-filled");
    row.removeAttribute("draggable");
    delete row.dataset.member;
    row.innerHTML = `<td colspan="5" class="text-center text-muted">Arrastra un integrante aquí</td>`;
    // Remueve los eventos de drag & drop para evitar conflictos
    row.removeEventListener("dragstart", handleDragStart);
    row.removeEventListener("dragend", handleDragEnd);
    row.removeEventListener("dragover", handleDragOver);
    row.removeEventListener("drop", handleDrop);
  }

  // Funciones para manejar los eventos de drag & drop (para evitar duplicación)
  function handleDragStart(e) {
    if (this.getAttribute("data-filled") === "true") {
      dragSourceType = "row";
      draggedRow = this;
      e.dataTransfer.setData("application/json", this.dataset.member);
      e.dataTransfer.effectAllowed = "move";
      this.classList.add("dragging");
    } else {
      e.preventDefault();
    }
  }

  function handleDragEnd(e) {
    this.classList.remove("dragging");
    draggedRow = null;
    dragSourceType = null;
  }

  function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = dragSourceType === "suggestion" ? "copy" : "move";
  }

  function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();

    // Si el arrastre proviene de las sugerencias (autocomplete)
    if (dragSourceType === "suggestion") {
      const item = JSON.parse(e.dataTransfer.getData("application/json"));
      if (existsInTable(item)) {
        alert("Esta persona ya ha sido asignada");
        dragSourceType = null;
        return;
      }
      // Sólo asigna si el slot está vacío
      if (this.getAttribute("data-filled") !== "true") {
        fillRow(this, item);
        updateRoles();
      } else {
        alert("Este espacio ya está ocupado. Usa un espacio vacío.");
      }
    }
    // Si se está reordenando a partir de un arrastre de fila (swap)
    else if (dragSourceType === "row") {
      if (draggedRow && draggedRow !== this) {
        swapRows(draggedRow, this);
        updateRoles();
      }
    }
    draggedRow = null;
    dragSourceType = null;
  }

  // Función encargada de asignar los eventos de drag & drop a cada fila (slot)
  function addRowDnDEvents(row) {
    row.addEventListener("dragstart", handleDragStart);
    row.addEventListener("dragend", handleDragEnd);
    row.addEventListener("dragover", handleDragOver);
    row.addEventListener("drop", handleDrop);
  }

  // Intercambia el contenido de dos filas
  function swapRows(row1, row2) {
    const data1 = row1.dataset.member;
    const data2 = row2.dataset.member;
    if (data1 && data2) {
      fillRow(row1, JSON.parse(data2));
      fillRow(row2, JSON.parse(data1));
    }
  }

  // Actualiza los roles: el primer slot lleno se convierte en "Capitán" y el resto en "Integrante"
  function updateRoles() {
    const filledRows = Array.from(tableBody.children).filter(row => row.getAttribute("data-filled") === "true");
    filledRows.forEach((row, index) => {
      const roleCell = row.querySelector(".role");
      if (roleCell) {
        roleCell.textContent = index === 0 ? "Capitán" : "Integrante";
      }
    });
  }
});