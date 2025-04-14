function togglePasswordVisibility(inputId, iconId) {
    const input = document.getElementById(inputId);
    const icon = document.getElementById(iconId);

    if (input.type === "password") {
        input.type = "text"; // Change the input field type to 'text'
        icon.classList.remove("bi-eye-slash"); // Remove 'eye-slash' icon
        icon.classList.add("bi-eye"); // Add 'eye' icon
    } else {
        input.type = "password"; // Change the input field type back to 'password'
        icon.classList.remove("bi-eye"); // Remove 'eye' icon
        icon.classList.add("bi-eye-slash"); // Add 'eye-slash' icon
    }
}
