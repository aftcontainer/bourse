document.addEventListener('DOMContentLoaded', function () {
	const rows          = document.querySelectorAll('.perm-row');
	const search         = document.getElementById('permSearch');
	const toggleAll      = document.getElementById('toggleAllPerms');
	const counter         = document.getElementById('permSelectedCount');

	function refreshCounter() {
		const total = document.querySelectorAll('.perm-checkbox:checked').length;
		counter.textContent = total + ' permission(s) sélectionnée(s)';
	}

	// Filtre de recherche par nom de module
	search.addEventListener('input', function () {
		const q = this.value.trim().toLowerCase();
		rows.forEach(function (row) {
			const label = row.dataset.modelLabel || '';
			row.classList.toggle('d-none', q.length > 0 && !label.includes(q));
		});
	});

	// Coche/décoche toute une ligne (module)
	document.querySelectorAll('.model-row-toggle').forEach(function (rowToggle) {
		rowToggle.addEventListener('change', function () {
			const rowIndex = this.dataset.row;
			document.querySelectorAll('.perm-checkbox[data-row="' + rowIndex + '"]')
				.forEach(function (cb) { cb.checked = rowToggle.checked; });
			refreshCounter();
		});
	});

	// Coche/décoche l'ensemble des permissions
	toggleAll.addEventListener('change', function () {
		document.querySelectorAll('.perm-checkbox').forEach(function (cb) { cb.checked = toggleAll.checked; });
		document.querySelectorAll('.model-row-toggle').forEach(function (cb) { cb.checked = toggleAll.checked; });
		refreshCounter();
	});

	// Met à jour le compteur et l'état de la ligne quand une case individuelle change
	document.querySelectorAll('.perm-checkbox').forEach(function (cb) {
		cb.addEventListener('change', function () {
			const rowIndex = this.dataset.row;
			const rowBoxes = document.querySelectorAll('.perm-checkbox[data-row="' + rowIndex + '"]');
			const rowToggle = document.querySelector('.model-row-toggle[data-row="' + rowIndex + '"]');
			if (rowToggle) {
				rowToggle.checked = Array.from(rowBoxes).every(function (b) { return b.checked; });
			}
			refreshCounter();
		});
	});

	refreshCounter();
});
