import os

import cv2
import numpy as np
import pytesseract

from PIL import Image


# ==========================================================
# TESSERACT INSTALLATION
# ==========================================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# ==========================================================
# IMAGE PREPROCESSING
# ==========================================================

# All preprocessing variants are upscaled by this factor to help
# Tesseract. Word boxes must be divided by it to map back to the
# original image coordinates (otherwise rows/overlays misalign).
UPSCALE_FACTOR = 2

# Original image size of the last processed file. Used to let the
# frontend scale overlay boxes correctly.
_LAST_IMAGE_SIZE = {"width": None, "height": None}


def preprocess_variants(image):
    """
    Create multiple OCR versions of the same image.

    The different variants help OCR work with:
    - normal documents
    - low contrast documents
    - noisy documents
    - scanned documents
    """

    # Remember original size *before* converting to numpy so word
    # boxes can be mapped back to the original image coordinates.
    try:
        orig_w, orig_h = image.size
        _LAST_IMAGE_SIZE["width"] = orig_w
        _LAST_IMAGE_SIZE["height"] = orig_h
    except Exception:
        pass

    image = np.array(
        image.convert("RGB")
    )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_RGB2GRAY
    )

    # ------------------------------------------------------
    # UPSCALE
    # ------------------------------------------------------

    height, width = gray.shape

    gray = cv2.resize(
        gray,
        (
            width * UPSCALE_FACTOR,
            height * UPSCALE_FACTOR
        ),
        interpolation=cv2.INTER_CUBIC
    )

    # ------------------------------------------------------
    # LIGHT DENOISE
    # ------------------------------------------------------

    denoised = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )

    # ------------------------------------------------------
    # CONTRAST
    # ------------------------------------------------------

    contrast = cv2.normalize(
        denoised,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    )

    # ------------------------------------------------------
    # BINARY
    # ------------------------------------------------------

    binary = cv2.threshold(
        contrast,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    # ------------------------------------------------------
    # ADAPTIVE THRESHOLD
    # ------------------------------------------------------

    adaptive = cv2.adaptiveThreshold(
        contrast,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )

    return [
        gray,
        contrast,
        binary,
        adaptive
    ]


# ==========================================================
# OCR CONFIGURATION
# ==========================================================

OCR_CONFIGS = [
    "--oem 3 --psm 3",
    "--oem 3 --psm 4",
    "--oem 3 --psm 6",
    "--oem 3 --psm 11",
]


# ==========================================================
# OCR TEXT
# ==========================================================

def extract_text_from_image(file_path):
    """
    Extract OCR text while trying multiple
    preprocessing variants and OCR configurations.

    Selection is by valid word count then character length,
    not just raw length, so a noisy long string does not beat
    a shorter high-confidence result. This preserves alignment.
    """

    image = Image.open(file_path)

    variants = preprocess_variants(image)

    best_text = ""
    best_score = -1

    for processed_image in variants:

        for config in OCR_CONFIGS:

            text = pytesseract.image_to_string(
                processed_image,
                config=config
            )

            stripped = text.strip()

            if not stripped:
                continue

            tokens = stripped.split()
            valid_tokens = [
                t for t in tokens
                if any(c.isalnum() for c in t)
            ]
            score = len(valid_tokens)

            if score > best_score or (
                score == best_score and len(stripped) > len(best_text)
            ):
                best_text = stripped
                best_score = score

    return best_text


# ==========================================================
# MAIN OCR TEXT FUNCTION
# ==========================================================

def extract_text(file_path):
    """
    Universal OCR entry point.

    Currently supports image documents.
    """

    extension = os.path.splitext(
        file_path
    )[1].lower()

    image_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".bmp",
        ".tiff",
        ".tif"
    }

    if extension in image_extensions:

        return extract_text_from_image(
            file_path
        )

    raise ValueError(
        f"Unsupported file type: {extension}"
    )


# ==========================================================
# OCR WORD DATA
# ==========================================================

def extract_word_data(file_path):
    """
    Extract individual OCR words with:
        text
        x
        y
        width
        height
        center_x
        center_y
        confidence
    """

    image = Image.open(file_path)

    variants = preprocess_variants(image)

    best_data = None

    best_count = 0

    for processed_image in variants:

        for config in OCR_CONFIGS:

            data = pytesseract.image_to_data(
                processed_image,
                config=config,
                output_type=pytesseract.Output.DICT
            )

            valid_count = 0

            for text, conf in zip(
                data["text"],
                data["conf"]
            ):

                text = text.strip()

                try:
                    confidence = float(conf)

                except (
                    ValueError,
                    TypeError
                ):

                    confidence = -1

                if text and confidence >= 0:
                    valid_count += 1

            if valid_count > best_count:

                best_count = valid_count

                best_data = data

    if best_data is None:
        return []

    words = []

    for index in range(
        len(best_data["text"])
    ):

        text = best_data["text"][index].strip()

        try:

            confidence = float(
                best_data["conf"][index]
            )

        except (
            ValueError,
            TypeError
        ):

            confidence = -1

        if not text:
            continue

        if confidence < 0:
            continue

        # Tesseract coordinates are in the upscaled space.
        # Map back to the original image so rows, gaps,
        # overlays and aligned-text reconstruction are correct.
        x = int(
            best_data["left"][index] / UPSCALE_FACTOR
        )

        y = int(
            best_data["top"][index] / UPSCALE_FACTOR
        )

        width = int(
            best_data["width"][index] / UPSCALE_FACTOR
        )

        height = int(
            best_data["height"][index] / UPSCALE_FACTOR
        )

        words.append({
            "text": text,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "center_x": x + width / 2,
            "center_y": y + height / 2,
            "confidence": confidence
        })

    return words


# ==========================================================
# ROW HELPERS
# ==========================================================

def _word_center_y(word):
    """
    Return vertical center of an OCR word.
    """

    return (
        word["y"]
        + word["height"] / 2
    )


def _same_row(
    word_a,
    word_b,
    tolerance
):
    """
    Check whether two OCR words belong
    to the same horizontal row.
    """

    center_a = _word_center_y(
        word_a
    )

    center_b = _word_center_y(
        word_b
    )

    return abs(
        center_a - center_b
    ) <= tolerance


# ==========================================================
# BUILD ROWS
# ==========================================================

def _build_rows(words):
    """
    Build rows from OCR words.

    IMPORTANT:

    Row processing happens BEFORE hierarchy
    processing.

    A word from one row can never be paired
    with a word from another row.
    """

    if not words:
        return []

    # Median height gives a stable tolerance across font sizes
    # (small print vs large headers) instead of per-word jitter.
    heights = sorted(w["height"] for w in words if w.get("height"))
    median_h = heights[len(heights) // 2] if heights else 10
    base_tolerance = max(10, median_h * 0.6)

    # ------------------------------------------------------
    # Sort top -> bottom
    # then left -> right
    # ------------------------------------------------------

    words = sorted(
        words,
        key=lambda word: (
            word["y"],
            word["x"]
        )
    )

    rows = []

    for word in words:

        placed = False

        word_center = _word_center_y(
            word
        )

        for row in rows:

            row_center = row["y"]

            # Use median-aware tolerance: adaptive but never too tight
            # for large headers nor too loose for small print.
            tolerance = max(
                base_tolerance,
                min(
                    word["height"],
                    row["height"]
                ) * 0.6
            )

            if abs(
                word_center - row_center
            ) <= tolerance:

                row["words"].append(
                    word
                )

                # Update row center
                centers = [
                    _word_center_y(item)
                    for item in row["words"]
                ]

                row["y"] = (
                    sum(centers)
                    / len(centers)
                )

                row["height"] = max(
                    item["height"]
                    for item in row["words"]
                )

                placed = True

                break

        if not placed:

            rows.append({
                "y": word_center,
                "height": word["height"],
                "words": [word]
            })

    # ------------------------------------------------------
    # Sort each row left -> right
    # ------------------------------------------------------

    for row in rows:

        row["words"].sort(
            key=lambda word: word["x"]
        )

    # ------------------------------------------------------
    # Sort rows top -> bottom
    # ------------------------------------------------------

    rows.sort(
        key=lambda row: row["y"]
    )

    return rows


# ==========================================================
# CALCULATE GAPS
# ==========================================================

def _calculate_gaps(words):
    """
    Calculate horizontal gap between consecutive words.
    """

    result = []

    for index, word in enumerate(words):

        item = dict(word)

        if index == 0:

            item[
                "gap_from_previous"
            ] = None

        else:

            previous = words[
                index - 1
            ]

            previous_right = (
                previous["x"]
                + previous["width"]
            )

            gap = (
                word["x"]
                - previous_right
            )

            item[
                "gap_from_previous"
            ] = max(
                0,
                gap
            )

        result.append(item)

    return result


# ==========================================================
# CALCULATE GAP THRESHOLD
# ==========================================================

def _calculate_gap_threshold(words):
    """
    Determine the normal/close spacing for one row.

    No medical field names are used.

    The threshold is calculated from the actual
    spacing distribution of the row.
    """

    gaps = [
        word["gap_from_previous"]
        for word in words
        if word["gap_from_previous"]
        is not None
    ]

    if not gaps:
        return None

    if len(gaps) == 1:

        return max(
            gaps[0] * 2,
            gaps[0] + 8
        )

    sorted_gaps = sorted(gaps)

    # ------------------------------------------------------
    # Find the largest separation between
    # two clusters of gaps.
    # ------------------------------------------------------

    largest_jump = 0

    threshold = None

    for index in range(
        1,
        len(sorted_gaps)
    ):

        previous = sorted_gaps[
            index - 1
        ]

        current = sorted_gaps[
            index
        ]

        jump = current - previous

        if jump > largest_jump:

            largest_jump = jump

            threshold = (
                previous + current
            ) / 2

    # ------------------------------------------------------
    # If no useful cluster separation exists,
    # use the median.
    # ------------------------------------------------------

    if threshold is None:

        middle = len(
            sorted_gaps
        ) // 2

        if len(sorted_gaps) % 2 == 0:

            median = (
                sorted_gaps[middle - 1]
                + sorted_gaps[middle]
            ) / 2

        else:

            median = sorted_gaps[
                middle
            ]

        threshold = max(
            median * 1.5,
            median + 8
        )

    return threshold


# ==========================================================
# BASIC TEXT NODE
# ==========================================================

def _make_text_node(word):
    """
    Convert one OCR word into a hierarchy node.
    """

    return {
        "type": "text",
        "text": word["text"],
        "x": word["x"],
        "y": word["y"],
        "width": word["width"],
        "height": word["height"],
        "children": []
    }


# ==========================================================
# GROUP NODE
# ==========================================================

def _make_group(children):
    """
    Create a hierarchy group.

    A group can contain:
        text nodes
        other groups
        combinations of both
    """

    if not children:
        return {
            "type": "group",
            "text": "",
            "x": None,
            "width": None,
            "children": []
        }

    first = children[0]

    last = children[-1]

    first_x = first.get(
        "x"
    )

    last_x = last.get(
        "x"
    )

    last_width = last.get(
        "width",
        0
    )

    if first_x is not None and last_x is not None:

        width = (
            last_x
            + last_width
            - first_x
        )

    else:

        width = None

    return {
        "type": "group",
        "text": _node_to_text(
            children
        ),
        "x": first_x,
        "width": width,
        "children": children
    }


# ==========================================================
# NODE TEXT
# ==========================================================

def _node_to_text(node):
    """
    Convert a hierarchy node into readable text.
    """

    if isinstance(node, list):

        return " ".join(
            _node_to_text(item)
            for item in node
        )

    if node.get("children"):

        return " ".join(
            _node_to_text(child)
            for child in node["children"]
        )

    return node.get(
        "text",
        ""
    )


# ==========================================================
# FIRST LEVEL GROUPS
# ==========================================================

def _group_row_words(words):
    """
    Build first-level spatial groups.

    Processing ALWAYS happens from LEFT to RIGHT.

    We never search for the closest pair in the
    middle and use that as the starting point.
    """

    if not words:
        return []

    threshold = _calculate_gap_threshold(
        words
    )

    if threshold is None:

        return [
            _make_text_node(word)
            for word in words
        ]

    groups = []

    current = []

    for word in words:

        # --------------------------------------------------
        # FIRST WORD
        # --------------------------------------------------

        if not current:

            current.append(word)

            continue

        gap = word[
            "gap_from_previous"
        ]

        # --------------------------------------------------
        # CLOSE
        # --------------------------------------------------

        if gap <= threshold:

            current.append(word)

        # --------------------------------------------------
        # LARGE GAP
        # --------------------------------------------------

        else:

            if len(current) == 1:

                groups.append(
                    _make_text_node(
                        current[0]
                    )
                )

            else:

                children = [
                    _make_text_node(item)
                    for item in current
                ]

                groups.append(
                    _make_group(
                        children
                    )
                )

            current = [word]

    # ------------------------------------------------------
    # FINAL GROUP
    # ------------------------------------------------------

    if current:

        if len(current) == 1:

            groups.append(
                _make_text_node(
                    current[0]
                )
            )

        else:

            children = [
                _make_text_node(item)
                for item in current
            ]

            groups.append(
                _make_group(
                    children
                )
            )

    return groups


# ==========================================================
# BUILD HIERARCHICAL LAYOUT
# ==========================================================

def _build_hierarchical_layout(words):
    """
    Build an expandable hierarchy from one OCR row.

    RULES:

    1. Always begin at the LEFTMOST item.

    2. Never search the middle first.

    3. Close consecutive items become a pair.

    4. Once a pair exists, it becomes ONE UNIT.

    5. Existing units can themselves become a pair.

    6. This can continue for multiple levels.

    7. Every parent keeps its children.

    Example:

        A B C D

    First level:

        AB    CD

    Second level:

        AB
         \
          CD

    Result:

        A B C D
          |
        A B     C D
        | |     | |
        A B     C D

    The actual number of levels is determined
    by the spatial gaps.
    """

    if not words:
        return []

    # ------------------------------------------------------
    # STEP 1:
    # Make basic text nodes
    # ------------------------------------------------------

    current_units = [
        _make_text_node(word)
        for word in words
    ]

    # ------------------------------------------------------
    # STEP 2:
    # Calculate original gaps
    # ------------------------------------------------------

    gaps = []

    for index in range(
        1,
        len(words)
    ):

        previous = words[
            index - 1
        ]

        current = words[
            index
        ]

        previous_right = (
            previous["x"]
            + previous["width"]
        )

        gap = (
            current["x"]
            - previous_right
        )

        gaps.append(
            max(0, gap)
        )

    if not gaps:
        return current_units

    # ------------------------------------------------------
    # Determine close spacing
    # ------------------------------------------------------

    sorted_gaps = sorted(gaps)

    middle = len(
        sorted_gaps
    ) // 2

    if len(sorted_gaps) % 2 == 0:

        normal_gap = (
            sorted_gaps[middle - 1]
            + sorted_gaps[middle]
        ) / 2

    else:

        normal_gap = sorted_gaps[
            middle
        ]

    close_threshold = max(
        normal_gap * 1.5,
        normal_gap + 8
    )

    # ------------------------------------------------------
    # IMPORTANT
    #
    # We repeatedly create pairs.
    #
    # Level 1:
    #
    # A B C D E F
    #
    # becomes:
    #
    # AB CD EF
    #
    # Level 2:
    #
    # AB CD EF
    #
    # can become:
    #
    # ABCD EF
    #
    # Level 3:
    #
    # ABCD EF
    #
    # can become:
    #
    # ABCDEF
    #
    # Every level starts from the LEFT.
    # ------------------------------------------------------

    current_gaps = gaps

    while (
        len(current_units) > 1
        and current_gaps
    ):

        new_units = []

        new_gaps = []

        index = 0

        made_pair = False

        while index < len(
            current_units
        ):

            # ------------------------------------------------
            # Last unit
            # ------------------------------------------------

            if index == len(
                current_units
            ) - 1:

                new_units.append(
                    current_units[index]
                )

                break

            gap = current_gaps[
                index
            ]

            # ------------------------------------------------
            # CLOSE:
            #
            # Pair CURRENT + NEXT
            #
            # This is the critical rule.
            #
            # We do NOT skip forward looking for
            # a closer pair.
            # ------------------------------------------------

            if gap <= close_threshold:

                left = current_units[
                    index
                ]

                right = current_units[
                    index + 1
                ]

                parent = {
                    "type": "group",
                    "text": (
                        _node_to_text(left)
                        + " "
                        + _node_to_text(right)
                    ),
                    "x": left.get(
                        "x"
                    ),
                    "width": (
                        right.get("x")
                        + right.get("width", 0)
                        - left.get("x")
                    ),
                    "children": [
                        left,
                        right
                    ]
                }

                new_units.append(
                    parent
                )

                made_pair = True

                # ------------------------------------------------
                # The newly-created parent is now ONE UNIT.
                # ------------------------------------------------

                index += 2

                # ------------------------------------------------
                # Gap to the next unit will be calculated
                # after this level.
                # ------------------------------------------------

            else:

                new_units.append(
                    current_units[index]
                )

                index += 1

        # ------------------------------------------------------
        # If nothing was paired at this level,
        # hierarchy cannot grow anymore.
        # ------------------------------------------------------

        if not made_pair:

            break

        # ------------------------------------------------------
        # Calculate gaps BETWEEN NEW UNITS.
        #
        # This is what allows:
        #
        # A B
        # C D
        #
        # to become:
        #
        # A B C D
        #
        # with AB and CD remaining as children.
        # ------------------------------------------------------

        for index in range(
            1,
            len(new_units)
        ):

            previous = new_units[
                index - 1
            ]

            current = new_units[
                index
            ]

            previous_right = (
                previous.get("x")
                + previous.get(
                    "width",
                    0
                )
            )

            gap = (
                current.get("x")
                - previous_right
            )

            new_gaps.append(
                max(0, gap)
            )

        current_units = new_units

        current_gaps = new_gaps

    return current_units


# ==========================================================
# COMPATIBILITY ALIAS
# ==========================================================

def build_hierarchical_layout(
    layout_rows
):
    """
    Build hierarchy for a complete document.

    This function exists so older code that calls
    build_hierarchical_layout() does not crash.

    It processes each row separately.
    """

    result = []

    for row in layout_rows:

        words = row.get(
            "words",
            row.get(
                "items",
                []
            )
        )

        hierarchy = _build_hierarchical_layout(
            words
        )

        result.append({
            "row_number": row.get(
                "row_number"
            ),
            "y": row.get(
                "y"
            ),
            "hierarchy": hierarchy
        })

    return result


# ==========================================================
# TEXT FROM GROUP
# ==========================================================

def _group_to_text(node):
    """
    Convert a hierarchy node back into readable text.
    """

    if not node:
        return ""

    if isinstance(node, list):

        return " ".join(
            _group_to_text(item)
            for item in node
        )

    children = node.get(
        "children",
        []
    )

    if children:

        return " ".join(
            _group_to_text(child)
            for child in children
        )

    return node.get(
        "text",
        ""
    )


# ==========================================================
# LAYOUT -> INFORMATION
# ==========================================================

def _layout_to_information(layout):
    """
    Convert spatial layout into human-readable
    row information.

    This function does NOT assume fields such as:
        Patient
        Medicine
        Age
        Dosage
        etc.

    It only reports the spatially detected groups.
    """

    output = []

    for row in layout.get(
        "rows",
        []
    ):

        row_data = []

        # --------------------------------------------------
        # Use hierarchy when available
        # --------------------------------------------------

        hierarchy = row.get(
            "hierarchy",
            []
        )

        if hierarchy:

            for node in hierarchy:

                text = _group_to_text(
                    node
                )

                if text:

                    row_data.append(
                        text
                    )

        # --------------------------------------------------
        # Fallback to first-level groups
        # --------------------------------------------------

        else:

            for group in row.get(
                "groups",
                []
            ):

                text = _group_to_text(
                    group
                )

                if text:

                    row_data.append(
                        text
                    )

        if row_data:

            output.append(
                " | ".join(row_data)
            )

    return "\n".join(
        output
    )


# ==========================================================
# ARRANGE DOCUMENT
# ==========================================================

def arrange_document(words):
    """
    Convert raw OCR words into:

        words
        rows
        groups
        hierarchy
    """

    rows = _build_rows(
        words
    )

    arranged_rows = []

    for row_number, row in enumerate(
        rows,
        start=1
    ):

        words_with_gaps = _calculate_gaps(
            row["words"]
        )

        groups = _group_row_words(
            words_with_gaps
        )

        hierarchy = _build_hierarchical_layout(
            words_with_gaps
        )

        arranged_rows.append({
            "row_number": row_number,
            "y": int(row["y"]),
            "items": words_with_gaps,
            "words": words_with_gaps,
            "groups": groups,
            "hierarchy": hierarchy
        })

    return arranged_rows


# ==========================================================
# RECONSTRUCT ALIGNED TEXT FROM SPATIAL LAYOUT
# ==========================================================

def _reconstruct_aligned_text(layout_rows):
    """
    Build human-readable text from spatial rows.

    Uses gap thresholds per row so columns (e.g. lab tables)
    keep a wider gap (4 spaces) vs normal word gaps (1 space).
    This fixes the collapsed-column misalignment seen when
    OCR was dumped as a single tesseract string.
    """
    lines = []
    for row in layout_rows:
        words = row.get("words", []) or row.get("items", [])
        if not words:
            continue
        threshold = _calculate_gap_threshold(words)
        # Height-based floor ensures table columns (all gaps ~30-200)
        # are not merged just because per-row distribution is wide.
        median_h = 10
        try:
            hs = sorted(w.get("height", 10) for w in words)
            median_h = hs[len(hs) // 2] if hs else 10
        except Exception:
            pass
        height_floor = max(12, int(median_h * 1.1))
        # Cap the per-row threshold so wide table distributions do not
        # swallow column gaps: any gap larger than ~2× character height
        # is treated as a column break.
        if threshold is not None:
            effective = min(threshold, height_floor * 2)
        else:
            effective = height_floor * 2
        line = words[0]["text"]
        for word in words[1:]:
            gap = word.get("gap_from_previous")
            if gap is not None and gap > effective:
                line += "    " + word["text"]
            else:
                line += " " + word["text"]
        lines.append(line)
    return "\n".join(lines)


# ==========================================================
# MAIN DOCUMENT EXTRACTION
# ==========================================================

def extract_document_data(file_path):
    """
    Complete OCR document extraction.

    Returns:

        text
        lines
        segments
        layout
        hierarchical_layout
        information
    """

    # ======================================================
    # STEP 1:
    # ORIGINAL OCR TEXT
    # ======================================================

    text = extract_text(
        file_path
    )

    # ======================================================
    # STEP 2:
    # OCR WORD BOXES
    # ======================================================

    words = extract_word_data(
        file_path
    )

    # ======================================================
    # STEP 3:
    # ROWS
    # ======================================================

    raw_rows = _build_rows(
        words
    )

    layout_rows = []

    # ======================================================
    # STEP 4:
    # GAPS + GROUPS + HIERARCHY
    # ======================================================

    for row_number, row in enumerate(
        raw_rows,
        start=1
    ):

        words_with_gaps = _calculate_gaps(
            row["words"]
        )

        groups = _group_row_words(
            words_with_gaps
        )

        hierarchy = _build_hierarchical_layout(
            words_with_gaps
        )

        layout_rows.append({
            "row_number": row_number,
            "y": int(row["y"]),
            "words": words_with_gaps,
            "groups": groups,
            "hierarchy": hierarchy
        })

    # ======================================================
    # LAYOUT
    # ======================================================

    layout = {
        "rows": layout_rows,
        "image_width": _LAST_IMAGE_SIZE.get("width"),
        "image_height": _LAST_IMAGE_SIZE.get("height"),
    }

    # ======================================================
    # COMPLETE HIERARCHICAL LAYOUT
    # ======================================================

    hierarchical_layout = (
        build_hierarchical_layout(
            layout_rows
        )
    )

    # ======================================================
    # INFORMATION OUTPUT
    # ======================================================

    information = _layout_to_information(
        layout
    )

    # ======================================================
    # ALIGNED TEXT (spatially correct)
    # ======================================================

    aligned_text = _reconstruct_aligned_text(layout_rows)

    # Prefer spatially reconstructed text so columns stay aligned;
    # fall back to raw tesseract string only if reconstruction is empty.
    final_text = aligned_text.strip() if aligned_text.strip() else (text or "")

    # ======================================================
    # ORIGINAL OCR LINES (from aligned text)
    # ======================================================

    lines = [
        line.strip()
        for line in final_text.splitlines()
        if line.strip()
    ]

    # ======================================================
    # SEGMENTS
    # ======================================================

    segments = []

    for index, line in enumerate(
        lines
    ):

        segments.append({
            "line_number": index + 1,
            "text": line
        })

    # ======================================================
    # FINAL RESULT
    # ======================================================

    return {
        # Spatially aligned (use this for display/storage)
        "text": final_text,
        "aligned_text": aligned_text,
        # Raw tesseract dump kept for debugging
        "raw_text": text,

        "lines": lines,

        "segments": segments,

        "layout": layout,

        "hierarchical_layout": (
            hierarchical_layout
        ),

        "information": information,

        "image_width": _LAST_IMAGE_SIZE.get("width"),
        "image_height": _LAST_IMAGE_SIZE.get("height"),
    }