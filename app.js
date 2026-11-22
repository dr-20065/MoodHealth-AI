document.querySelectorAll('[data-menu-toggle]').forEach((button) => {
  button.addEventListener('click', () => document.querySelector('[data-menu]')?.classList.toggle('open'));
});

document.querySelectorAll('form[data-confirm]').forEach((form) => {
  form.addEventListener('submit', (event) => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
  });
});
