import { downloadExcel, getStudents } from './api.js';

export function readFilterValues(form) {
    return Object.fromEntries(new FormData(form).entries());
}

export async function loadStudents(form) {
    return getStudents(readFilterValues(form));
}

export async function exportStudents(form) {
    return downloadExcel(readFilterValues(form));
}

function updateSelect(select, values, allLabel, selectedValue) {
    select.replaceChildren(new Option(allLabel, 'all'));
    values.forEach((value) => select.appendChild(new Option(value, value)));
    select.value = values.includes(selectedValue) ? selectedValue : 'all';
}

export function renderFilterOptions(options, form) {
    const selectedClass = form.elements.class.value;
    const selectedGrade = form.elements.grade.value;
    const selectedAge = form.elements.age.value;

    updateSelect(form.elements.class, options.classes, 'All classes', selectedClass);
    updateSelect(form.elements.grade, options.grades, 'All grades', selectedGrade);
    updateSelect(form.elements.age, options.ages.map(String), 'All ages', selectedAge);
}