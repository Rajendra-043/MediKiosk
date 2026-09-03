/* =================================
   MEDIKIOSK JAVASCRIPT
================================= */


/* =================================
   PASSWORD TOGGLE
================================= */

function togglePassword(inputId) {

    const input = document.getElementById(inputId);

    if (!input) return;

    if (input.type === "password") {
        input.type = "text";
    } else {
        input.type = "password";
    }
}


/* =================================
   PATIENT LOGIN - FRONTEND DEMO
================================= */

function handleLogin(event) {

    event.preventDefault();

    const patientId =
        document.getElementById("patientId").value;

    if (!patientId) {
        alert("Please enter your Patient ID.");
        return;
    }

    /*
       TEMPORARY FRONTEND REDIRECT

       Later Django authentication will
       handle this.
    */

    window.location.href = "/patient/dashboard/";
}


/* =================================
   DOCTOR LOGIN - FRONTEND DEMO
================================= */

function handleDoctorLogin(event) {

    event.preventDefault();

    /*
       Temporary redirect.
       Django authentication will replace this.
    */

    window.location.href = "/doctor/dashboard/";
}


/* =================================
   PATIENT REGISTRATION
================================= */

function handleRegistration(event) {

    event.preventDefault();

    const password =
        document.getElementById("registerPassword").value;

    const confirmPassword =
        document.getElementById("confirmPassword").value;

    if (password !== confirmPassword) {

        alert("Passwords do not match.");

        return;
    }

    alert(
        "Registration form submitted successfully.\n\n" +
        "Django database connection will be added next."
    );
}


/* =================================
   DOCTOR REGISTRATION
================================= */

function handleDoctorRegistration(event) {

    event.preventDefault();

    const password =
        document.getElementById(
            "doctorRegisterPassword"
        ).value;

    const confirmPassword =
        document.getElementById(
            "doctorConfirmPassword"
        ).value;

    if (password !== confirmPassword) {

        alert("Passwords do not match.");

        return;
    }

    alert(
        "Doctor registration submitted successfully."
    );
}


/* =================================
   SIDEBAR
================================= */

function toggleSidebar() {

    const sidebar =
        document.getElementById("sidebar");

    if (!sidebar) return;

    sidebar.classList.toggle("-translate-x-full");
}


/* =================================
   COPY PATIENT ID
================================= */

function copyPatientId() {

    const patientId = "MKP-2026-00001";

    navigator.clipboard.writeText(patientId)
        .then(() => {

            alert("Patient ID copied!");

        })
        .catch(() => {

            alert("Unable to copy Patient ID.");

        });
}


/* =================================
   LOGOUT
================================= */

function logout() {

    const confirmLogout =
        confirm("Are you sure you want to logout?");

    if (confirmLogout) {

        window.location.href = "/patient/login/";

    }
}


/* =================================
   ABOUT
================================= */

function showInfo() {

    alert(
        "MediKiosk\n\n" +
        "A digital healthcare platform for " +
        "organizing patient medical information " +
        "and assisting doctors with clinical records."
    );
}