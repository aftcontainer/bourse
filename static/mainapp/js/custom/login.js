const pw = document.getElementById("password");
  const tog = document.getElementById("pwToggle");
  const icon = tog.querySelector("i");
  tog.addEventListener("click", () => {
    const show = pw.type === "password";
    pw.type = show ? "text" : "password";
    icon.className = show ? "bi bi-eye-slash" : "bi bi-eye";
    tog.setAttribute("aria-label", show ? "Masquer le mot de passe" : "Afficher le mot de passe");
  });
  document.getElementById("loginForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const btn = e.target.querySelector(".btn-afg");
    const original = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Connexion...';
    setTimeout(() => { btn.disabled = false; btn.innerHTML = original; }, 1500);
  });