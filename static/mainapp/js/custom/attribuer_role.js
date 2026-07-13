$(document).ready(function () {
     document.addEventListener('DOMContentLoaded', function () {
	const userSelect   = document.getElementById('userSelect');
	const userPreview  = document.getElementById('userPreview');
	const previewName  = document.getElementById('userPreviewName');
	const previewEmail = document.getElementById('userPreviewEmail');
	const previewAvatar= document.getElementById('userAvatarInitials');

	const roleCards    = document.querySelectorAll('.role-card');
	const roleSearch   = document.getElementById('roleSearch');
	const roleCounter  = document.getElementById('roleSelectedCount');

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

	function updateUserPreview() {
		const opt = userSelect.options[userSelect.selectedIndex];
		if (!opt || !opt.value) {
			userPreview.style.display = 'none';
			return;
		}
		const label = opt.textContent.trim();
		const email = opt.dataset.email || '';
		previewName.textContent = label;
		previewEmail.textContent = email;
		previewAvatar.textContent = label.substring(0, 2).toUpperCase();
		userPreview.style.display = 'flex';
	}

	// Recherche de rôle
	roleSearch.addEventListener('input', function () {
		const q = this.value.trim().toLowerCase();
		roleCards.forEach(function (card) {
			const name = card.dataset.roleName || '';
			card.classList.toggle('d-none', q.length > 0 && !name.includes(q));
		});
	});

	// Cocher/décocher une carte de rôle en cliquant n'importe où sur la carte
	roleCards.forEach(function (card) {
		const cb = card.querySelector('.role-checkbox');
		cb.addEventListener('change', function () {
			refreshCardState();
			refreshRoleCounter();
		});
	});

	userSelect.addEventListener('change', updateUserPreview);

	updateUserPreview();
	refreshCardState();
	refreshRoleCounter();
});

});