
/* =========================
   PROFILE FORM
========================= */

const profileForm =
    document.getElementById("profileForm");

const cancelButton =
    document.getElementById("cancelButton");

const logoutButton =
    document.getElementById("logoutButton");


/* =========================
   SAVE PROFILE
========================= */

if (profileForm) {

    profileForm.addEventListener("submit", function(event) {

        event.preventDefault();

        /*
         * Temporary preview behavior.
         *
         * Later this will be replaced with
         * a Django POST request.
         */

        alert("Profile changes saved successfully.");

    });

}


/* =========================
   CANCEL
========================= */

if (cancelButton) {

    cancelButton.addEventListener("click", function() {

        const confirmCancel =
            confirm("Discard your changes?");

        if (confirmCancel) {

            profileForm.reset();

        }

    });

}


/* =========================
   LOGOUT
========================= */

if (logoutButton) {

    logoutButton.addEventListener("click", function() {

        const confirmLogout =
            confirm("Are you sure you want to logout?");

        if (confirmLogout) {

            /*
             * Temporary preview behavior.
             *
             * Replace this with your actual
             * Django logout URL.
             */

            window.location.href = "/logout/";

        }

    });

}
