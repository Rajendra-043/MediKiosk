
/* =========================
   PATIENT SEARCH
========================= */

const searchInput = document.getElementById("patientSearch");

if (searchInput) {

    searchInput.addEventListener("keyup", function () {

        const searchValue =
            this.value.toLowerCase().trim();

        const patients =
            document.querySelectorAll(".patient-row");


        patients.forEach(function (patient) {

            const patientText =
                patient.innerText.toLowerCase();


            if (patientText.includes(searchValue)) {

                patient.style.display = "grid";

            } else {

                patient.style.display = "none";

            }

        });

    });

}


/* =========================
   LOGOUT
========================= */

const logoutButton =
    document.getElementById("logoutButton");

if (logoutButton) {

    logoutButton.addEventListener("click", function () {

        const confirmLogout =
            confirm("Are you sure you want to logout?");

        if (confirmLogout) {

            /*
             * Replace this with your actual
             * Django logout URL later.
             */

            window.location.href = "/logout/";

        }

    });

}

