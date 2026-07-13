document.addEventListener('DOMContentLoaded', function () {
	const roleCards   = document.querySelectorAll('.role-card');
	const roleSearch  = document.getElementById('roleSearch');
	const roleCounter = document.getElementById('roleSelectedCount');

	function refreshRoleCounter() {
		const total = document.querySelectorAll('.role-checkbox:checked').length;
		roleCounter.textContent = total + ' rôle(s) sélectionné(s)';
	}

	function refreshCardState() {
		roleCards.forEach(function (card) {
			const cb = card.querySelector('.role-checkbox');
			card.classList.toggle('checked', cb.checked);
		});
	}

	roleSearch.addEventListener('input', function () {
		const q = this.value.trim().toLowerCase();
		roleCards.forEach(function (card) {
			const name = card.dataset.roleName || '';
			card.classList.toggle('d-none', q.length > 0 && !name.includes(q));
		});
	});

	roleCards.forEach(function (card) {
		const cb = card.querySelector('.role-checkbox');
		cb.addEventListener('change', function () {
			refreshCardState();
			refreshRoleCounter();
		});
	});

	refreshCardState();
	refreshRoleCounter();
});