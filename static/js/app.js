const toast = document.querySelector('#coming-soon');
document.querySelectorAll('[data-coming-soon]').forEach((button) => {
  button.addEventListener('click', () => {
    toast.classList.add('show');
    window.clearTimeout(window.mercagoToast);
    window.mercagoToast = window.setTimeout(() => toast.classList.remove('show'), 2400);
  });
});
document.querySelectorAll('[data-step]').forEach((button) => {
  button.addEventListener('click', () => {
    const input = button.parentElement.querySelector('input');
    input.value = Math.max(Number(input.min || .25), Number(input.value || 1) + Number(button.dataset.step));
  });
});
