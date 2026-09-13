document.addEventListener("DOMContentLoaded", function () {

    /* =====================================
       ELEMENT REFERENCES
    ===================================== */

    const viewButton =
        document.getElementById("viewDocumentsButton");

    const documentsSection =
        document.getElementById("documentsListSection");

    const openUploadModal =
        document.getElementById("openUploadModal");

    const uploadModal =
        document.getElementById("uploadModal");

    const closeUploadModal =
        document.getElementById("closeUploadModal");

    const modalDocumentInput =
        document.getElementById("modalDocumentInput");

    const selectedFile =
        document.getElementById("selectedFile");

    const uploadForm =
        document.getElementById("documentUploadForm");

    const ocrResult =
        document.getElementById("ocrResult");

    const ocrResultText =
        document.getElementById("ocrResultText");

    const ocrReportText =
        document.getElementById("ocrReportText");

    const documentsList =
        document.getElementById("documentsList");

    const documentCount =
        document.getElementById("documentCount");


    /* =====================================
       DETAILED OCR RESULT ELEMENTS
    ===================================== */

    const documentType =
        document.getElementById("documentType");

    const patientName =
        document.getElementById("patientName");

    const patientId =
        document.getElementById("patientId");

    const patientAge =
        document.getElementById("patientAge");

    const patientGender =
        document.getElementById("patientGender");

    const medicine =
        document.getElementById("medicine");

    const dosage =
        document.getElementById("dosage");

    const frequency =
        document.getElementById("frequency");

    const doctor =
        document.getElementById("doctor");

    const diagnosis =
        document.getElementById("diagnosis");

    const reportId =
        document.getElementById("reportId");

    const collectionDate =
        document.getElementById("collectionDate");

    const reportDate =
        document.getElementById("reportDate");

    const rawOcrText =
        document.getElementById("rawOcrText");

    const labResultsCard =
        document.getElementById("labResultsCard");

    const labResultsBody =
        document.getElementById("labResultsBody");


    /* =====================================
       VIEW DOCUMENTS
    ===================================== */

    if (viewButton && documentsSection) {

        viewButton.addEventListener("click", function () {

            documentsSection.scrollIntoView({
                behavior: "smooth"
            });

        });

    }


    /* =====================================
       OPEN UPLOAD MODAL
    ===================================== */

    if (openUploadModal && uploadModal) {

        openUploadModal.addEventListener("click", function () {

            uploadModal.classList.add("active");

        });

    }


    /* =====================================
       SHOW SELECTED FILE
    ===================================== */

    if (modalDocumentInput && selectedFile) {

        modalDocumentInput.addEventListener(
            "change",
            function () {

                if (modalDocumentInput.files.length > 0) {

                    selectedFile.textContent =
                        modalDocumentInput.files[0].name;

                } else {

                    selectedFile.textContent =
                        "No file selected";

                }

            }
        );

    }


    /* =====================================
       CLOSE UPLOAD MODAL
    ===================================== */

    if (closeUploadModal && uploadModal) {

        closeUploadModal.addEventListener("click", function () {

            uploadModal.classList.remove("active");

        });

    }


    /* =====================================
       CLOSE MODAL OUTSIDE
    ===================================== */

    if (uploadModal) {

        uploadModal.addEventListener(
            "click",
            function (event) {

                if (event.target === uploadModal) {

                    uploadModal.classList.remove("active");

                }

            }
        );

    }


    /* =====================================
       OCR DOCUMENT UPLOAD
    ===================================== */

    if (uploadForm) {

        uploadForm.addEventListener(
            "submit",
            async function (event) {

                event.preventDefault();


                /* -------------------------
                   CHECK FILE
                ------------------------- */

                if (
                    !modalDocumentInput ||
                    !modalDocumentInput.files.length
                ) {

                    alert(
                        "Please select a document."
                    );

                    return;

                }


                const file =
                    modalDocumentInput.files[0];


                /* -------------------------
                   VALIDATE FILE TYPE
                ------------------------- */

                const allowedTypes = [

                    "image/jpeg",
                    "image/png",
                    "image/webp",
                    "image/bmp",
                    "image/tiff"

                ];


                if (!allowedTypes.includes(file.type)) {

                    alert(
                        "Please upload a JPG, PNG, WEBP, BMP or TIFF image."
                    );

                    return;

                }


                /* -------------------------
                   PREPARE FORM DATA
                ------------------------- */

                const formData =
                    new FormData();

                formData.append(
                    "document",
                    file
                );


                /* -------------------------
                   DOCUMENT NAME
                ------------------------- */

                const documentNameInput =
                    uploadForm.querySelector(
                        '[name="document_name"]'
                    );


                if (documentNameInput) {

                    formData.append(
                        "document_name",
                        documentNameInput.value.trim()
                    );

                }


                /* -------------------------
                   CSRF TOKEN
                ------------------------- */

                const csrfInput =
                    uploadForm.querySelector(
                        '[name="csrfmiddlewaretoken"]'
                    );


                if (!csrfInput) {

                    alert(
                        "CSRF token not found."
                    );

                    return;

                }


                const csrfToken =
                    csrfInput.value;


                try {

                    /* =================================
                       SEND DOCUMENT TO DJANGO
                    ================================= */

                    const response =
                        await fetch(
                            uploadForm.action,
                            {
                                method: "POST",

                                headers: {
                                    "X-CSRFToken":
                                        csrfToken
                                },

                                body: formData
                            }
                        );


                    /* -------------------------
                       READ JSON RESPONSE
                    ------------------------- */

                    const data =
                        await response.json();


                    /* -------------------------
                       BACKEND ERROR
                    ------------------------- */

                    if (
                        !response.ok ||
                        !data.success
                    ) {

                        alert(
                            data.error ||
                            "OCR processing failed."
                        );

                        return;

                    }


                    /* =================================
                       DISPLAY COMPLETE OCR RESULT
                    ================================= */

                    console.log(
                        "OCR RESULT:",
                        data
                    );

                    displayOCRResult(data);


                    /* =================================
                       UPDATE DOCUMENT LIST
                    ================================= */

                    if (documentsList) {

                        /*
                           Remove empty message
                        */

                        const emptyMessage =
                            documentsList.querySelector(
                                ".document-empty"
                            );


                        if (emptyMessage) {

                            emptyMessage.remove();

                        }


                        /*
                           Create document item
                        */

                        const documentItem =
                            document.createElement("div");

                        documentItem.className =
                            "document-item";


                        /*
                           Use Django response
                        */

                        documentItem.innerHTML = `

                            <div class="document-file-icon">
                                FILE
                            </div>

                            <div class="document-info">

                                <h3>
                                    ${escapeHtml(
                            data.filename ||
                            "Uploaded Document"
                        )}
                                </h3>

                                <p>
                                    Uploaded just now
                                </p>

                            </div>

                            <div class="document-actions">

                                <a
                                    href="/patient/documents/${data.document_id}/"
                                    class="view-document-button"
                                >
                                    View
                                </a>

                            </div>

                        `;


                        /*
                           Newest document first
                        */

                        documentsList.prepend(
                            documentItem
                        );


                        /*
                           Update count
                        */

                        updateDocumentCount();

                    }


                    /* =================================
                       RESET FORM
                    ================================= */

                    uploadForm.reset();


                    if (selectedFile) {

                        selectedFile.textContent =
                            "No file selected";

                    }


                    /* =================================
                       CLOSE MODAL
                    ================================= */

                    if (uploadModal) {

                        uploadModal.classList.remove(
                            "active"
                        );

                    }


                } catch (error) {

                    console.error(
                        "OCR upload error:",
                        error
                    );

                    alert(
                        "Unable to connect to the OCR server."
                    );

                }

            }
        );

    }





    // =====================================
    // HTML ESCAPE HELPER
    // =====================================

    function escapeHTML(value) {
        const div = document.createElement("div");
        div.textContent = value ?? "";
        return div.innerHTML;
    }







    /* =====================================
       DISPLAY COMPLETE OCR RESULT
    ===================================== */
    function displayOCRResult(response) {

        const data = response.medical_data || {};

        document.getElementById("ocrResult").style.display = "block";


        /* =====================================
           BASIC INFORMATION
        ===================================== */

        document.getElementById("documentType").textContent =
            data.document_type || "Unknown";

        document.getElementById("patientName").textContent =
            data.patient_name || "—";

        document.getElementById("patientId").textContent =
            data.patient_id || "—";

        document.getElementById("patientAge").textContent =
            data.age || "—";

        document.getElementById("patientGender").textContent =
            data.gender || "—";

        document.getElementById("doctor").textContent =
            data.doctor || "—";

        document.getElementById("diagnosis").textContent =
            data.diagnosis || "—";

        document.getElementById("medicine").textContent =
            data.medicine || "—";

        document.getElementById("dosage").textContent =
            data.dosage || "—";

        document.getElementById("frequency").textContent =
            data.frequency || "—";

        document.getElementById("reportId").textContent =
            data.report_id || "—";

        document.getElementById("collectionDate").textContent =
            data.collection_date || "—";

        document.getElementById("reportDate").textContent =
            data.report_date || "—";

        document.getElementById("rawOcrText").textContent =
            data.raw_text || response.text || "No text extracted.";


        /* =====================================
           PRESCRIPTION CARD
        ===================================== */

        const prescriptionCard =
            document.getElementById("prescriptionCard");

        if (data.document_type === "Prescription") {

            prescriptionCard.style.display = "block";

        } else {

            prescriptionCard.style.display = "none";
        }


        /* =====================================
           LAB RESULTS
        ===================================== */

        const labCard =
            document.getElementById("labResultsCard");

        const labBody =
            document.getElementById("labResultsBody");

        labBody.innerHTML = "";

        if (
            Array.isArray(data.tests) &&
            data.tests.length > 0
        ) {

            labCard.style.display = "block";

            data.tests.forEach(test => {

                const row =
                    document.createElement("tr");

                row.innerHTML = `
                <td>${escapeHTML(test.test || "—")}</td>
                <td>${escapeHTML(test.result || "—")}</td>
                <td>${escapeHTML(test.reference || "—")}</td>
                <td>${escapeHTML(test.unit || "—")}</td>
            `;

                labBody.appendChild(row);
            });

        } else {

            labCard.style.display = "none";
        }


        /* =====================================
           DOCUMENT SEGMENTS
        ===================================== */

        const segmentsCard =
            document.getElementById("segmentsCard");

        const segmentsBody =
            document.getElementById("segmentsBody");

        segmentsBody.innerHTML = "";

        if (
            Array.isArray(data.segments) &&
            data.segments.length > 0
        ) {

            segmentsCard.style.display = "block";

            data.segments.forEach(segment => {

                const section =
                    document.createElement("div");

                section.className =
                    "document-segment";

                const heading =
                    document.createElement("h4");

                heading.textContent =
                    segment.heading || "Section";

                section.appendChild(heading);


                if (Array.isArray(segment.content)) {

                    segment.content.forEach(content => {

                        const paragraph =
                            document.createElement("p");

                        paragraph.textContent =
                            content;

                        section.appendChild(paragraph);
                    });
                }

                segmentsBody.appendChild(section);
            });

        } else {

            segmentsCard.style.display = "none";
        }
    }


    /* =====================================
       SAFE TEXT SETTER
    ===================================== */

    function setText(
        element,
        value,
        fallback
    ) {

        if (!element) {

            return;

        }


        if (
            value !== undefined &&
            value !== null &&
            String(value).trim() !== ""
        ) {

            element.textContent =
                value;

        } else {

            element.textContent =
                fallback;

        }

    }


    /* =====================================
       UPDATE DOCUMENT COUNT
    ===================================== */

    function updateDocumentCount() {

        if (
            !documentsList ||
            !documentCount
        ) {

            return;

        }


        const items =
            documentsList.querySelectorAll(
                ".document-item"
            );


        const count =
            items.length;


        documentCount.textContent =
            count === 1
                ? "1 Document"
                : `${count} Documents`;

    }


    /* =====================================
       ESCAPE HTML
    ===================================== */

    function escapeHtml(value) {

        const div =
            document.createElement("div");


        div.textContent =
            value || "";


        return div.innerHTML;

    }

});