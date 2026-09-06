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

            const formData = new FormData();

            formData.append(
                "document",
                file
            );


            /* -------------------------
               Get CSRF Token
            ------------------------- */

            const csrfToken =
                uploadForm.querySelector(
                    "[name=csrfmiddlewaretoken]"
                ).value;


            try {

                /* -------------------------
                   Send to OCR Backend
                ------------------------- */

                const response = await fetch(
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
                   Handle Error
                ------------------------- */

                if (!response.ok || !data.success) {

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


                // alert(
                //     "Document processed successfully.\n\n" +
                //     "Extracted Text:\n\n" +
                //     data.text
                // );




                if (ocrResult && ocrResultText) {

                    ocrResultText.textContent =
                        data.text;

                    ocrReportText.textContent =
                        data.report;

                    ocrResult.hidden = false;

                }





                /* -------------------------
                Add Document To List
                ------------------------- */

                const documentsList =
                    document.getElementById("documentsList");

                const documentCount =
                    document.getElementById("documentCount");


                if (documentsList && data.document_id) {

                    const emptyMessage =
                        documentsList.querySelector(".document-info h3");

                    if (
                        emptyMessage &&
                        emptyMessage.textContent.includes(
                            "No documents uploaded"
                        )
                    ) {
                        documentsList.innerHTML = "";
                    }


                    const documentItem =
                        document.createElement("div");

                    documentItem.className =
                        "document-item";


                    documentItem.innerHTML = `
                        <div class="document-file-icon">
                            FILE
                        </div>

                        <div class="document-info">
                            <h3>${data.filename}</h3>

                            <p>
                                Uploaded just now
                            </p>
                        </div>

                        <div class="document-actions">

                            <a
                                href="/patient/documents/"
                                class="view-document-button"
                            >
                                View
                            </a>

                            <button
                                type="button"
                                class="delete-document-button"
                                disabled
                            >
                                Delete
                            </button>

                        </div>
                    `;


                    documentsList.prepend(
                        documentItem
                    );


                    /* -------------------------
                    Update Document Count
                    ------------------------- */

                    if (documentCount) {

                        const currentCount =
                            documentsList.querySelectorAll(
                                ".document-item"
                            ).length;

                        documentCount.textContent =
                            currentCount +
                            (
                                currentCount === 1
                                    ? " Document"
                                    : " Documents"
                            );
                    }

                }











                /* -------------------------
                   Close Modal
                ------------------------- */

                uploadModal.classList.remove("active");


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

});