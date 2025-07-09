const button_1 = document.getElementById('button_1');
const button_2 = document.getElementById('button_2');
const add_course = document.getElementById('add_course');
const modal = document.getElementById('crud-modal');
const close_modal = document.getElementById('close-menu');


const mobile_menu = document.getElementById('mobile-menu');
const sandwich = document.getElementById('sandwich');

button_1.addEventListener('click', () => {
    mobile_menu.classList.toggle('hidden');
})

button_2.addEventListener('click', () => {
    sandwich.classList.toggle('hidden');
})

add_course.addEventListener('click', () => {
    modal.classList.toggle('hidden');
})

close_modal.addEventListener('click', () => {
    modal.classList.add('hidden');
})