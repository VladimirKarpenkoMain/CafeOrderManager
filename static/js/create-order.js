// Когда пользователь ставит/снимает галочку, показываем/скрываем .quantity-controller
document.addEventListener('DOMContentLoaded', function() {
  const checkboxes = document.querySelectorAll('.dish-checkbox');

  checkboxes.forEach(checkbox => {
    const quantityController = checkbox.closest('.dish-row').querySelector('.quantity-controller');

    if (checkbox.checked) {
      quantityController.style.display = 'inline-flex';
    } else {
      quantityController.style.display = 'none';
    }

    // При клике переключаем
    checkbox.addEventListener('change', () => {
      if (checkbox.checked) {
        quantityController.style.display = 'inline-flex';
      } else {
        quantityController.style.display = 'none';
      }
    });
  });
});

// Логика минус/плюс
document.addEventListener('click', function(e) {
  if (e.target.classList.contains('btn-minus')) {
    const input = e.target.parentNode.querySelector('input[type="number"]');
    if (!input) return;
    let currentVal = parseInt(input.value) || 1;
    const minVal = parseInt(input.min) || 1;

    if (currentVal > minVal) {
      input.value = currentVal - 1;
    }
  }

  if (e.target.classList.contains('btn-plus')) {
    const input = e.target.parentNode.querySelector('input[type="number"]');
    if (!input) return;
    let currentVal = parseInt(input.value) || 1;
    input.value = currentVal + 1;
  }
});