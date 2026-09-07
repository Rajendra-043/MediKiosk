document.addEventListener("DOMContentLoaded", function () {

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


    /* -------------------------
       View Documents
    ------------------------- */

    if (viewButton && documentsSection) {

        viewButton.addEventListener("click", function () {

            documentsSection.scrollIntoView({
                behavior: "smooth"
            });

        });

    }


    /* -------------------------
       Open Upload Modal
    ------------------------- */

    if (openUploadModal && uploadModal) {

        openUploadModal.addEventListener("click", function () {

            uploadModal.classList.add("active");

        });

    }


    /* -------------------------
       Show Selected File
    ------------------------- */

    if (modalDocumentInput && selectedFile) {

        modalDocumentInput.addEventListener("change", function () {

            if (modalDocumentInput.files.length > 0) {

                selectedFile.textContent =
                    modalDocumentInput.files[0].name;

            } else {

                selectedFile.textContent =
                    "No file selected";

            }

        });

    }


    /* -------------------------
       Close Upload Modal
    ------------------------- */

    if (closeUploadModal && uploadModal) {

        closeUploadModal.addEventListener("click", function () {

            uploadModal.classList.remove("active");

        });

    }


    /* -------------------------
       Close Modal Outside
    ------------------------- */

    if (uploadModal) {

        uploadModal.addEventListener("click", function (event) {

            if (event.target === uploadModal) {

                uploadModal.classList.remove("active");

            }

        });

    }


    /* -------------------------
       OCR DOCUMENT UPLOAD
    ------------------------- */

    if (uploadForm) {

        uploadForm.addEventListener("submit", async function (event) {

            event.preventDefault();


            /* -------------------------
               Check File
            ------------------------- */

            if (!modalDocumentInput.files.length) {

                alert("Please select a document.");

                return;

            }


            const file =
                modalDocumentInput.files[0];


            /* -------------------------
               Validate File Type
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
               Prepare Form Data
            ------------------------- */

            const formData =
                new FormData();

            formData.append(
                "document",
                file
            );


            /* -------------------------
               Add Document Name
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
               Get CSRF Token
            ------------------------- */

            const csrfInput =
                uploadForm.querySelector(
                    '[name="csrfmiddlewaretoken"]'
                );


            if (!csrfInput) {

                alert("CSRF token not found.");

                return;

            }


            const csrfToken =
                csrfInput.value;


            try {

                /* -------------------------
                   Send To Django
                ------------------------- */

                const response =
                    await fetch(
                        uploadForm.action,
                        {
                            method: "POST",

                            headers: {
                                "X-CSRFToken": csrfToken
                            },

                            body: formData
                        }
                    );


                const data =
                    await response.json();


                /* -------------------------
                   Handle Backend Error
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


                /* -------------------------
                   Display OCR Result
                ------------------------- */

                console.log(
                    "OCR RESULT:",
                    data.text
                );


                if (
                    ocrResult &&
                    ocrResultText &&
                    ocrReportText
                ) {

                    ocrResultText.textContent =
                        data.text;

                    ocrReportText.textContent =
                        data.report;

                    ocrResult.hidden = false;

                }


                /* -------------------------
                   Update Document List
                ------------------------- */

                if (documentsList) {


                    /*
                       Remove "No documents uploaded"
                       message if it exists.
                    */

                    const emptyMessage =
                        documentsList.querySelector(
                            ".document-empty"
                        );


                    if (emptyMessage) {

                        emptyMessage.remove();

                    }


                    /*
                       Create new document item
                    */

                    const documentItem =
                        document.createElement("div");

                    documentItem.className =
                        "document-item";


                    /*
                       Use document name returned
                       by Django.
                    */

                    documentItem.innerHTML = `

                        <div class="document-file-icon">
                            FILE
                        </div>

                        <div class="document-info">

                            <h3>
                                ${escapeHtml(data.filename)}
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
                       Put newest document first.
                    */

                    documentsList.prepend(
                        documentItem
                    );


                    /* -------------------------
                       Update Count
                    ------------------------- */

                    updateDocumentCount();

                }


                /* -------------------------
                   Reset Form
                ------------------------- */

                uploadForm.reset();


                if (selectedFile) {

                    selectedFile.textContent =
                        "No file selected";

                }


                /*
                   Close modal after successful
                   upload.
                */

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

        });

    }


    /* -------------------------
       Update Document Count
    ------------------------- */

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


    /* -------------------------
       Escape HTML
    ------------------------- */

    function escapeHtml(value) {

        const div =
            document.createElement("div");

        div.textContent =
            value || "";

        return div.innerHTML;

    }

});