# Spec: Ocr Billing

## Overview

Right now, adding an expense means typing the amount, category, date, and
description by hand every time. This step adds a shortcut on the Add
Expense page: the user can upload (or drag-and-drop) a photo of a paper
bill/receipt, and the backend reads it and pre-fills the amount, category,
date, and a short description into the *existing* Add Expense form. The
user still reviews and clicks "Save Expense" themselves — nothing is
written to the database until they confirm — so OCR mistakes never
silently corrupt their ledger. This reuses the same Groq-via-OpenAI-client
pattern already wired up for Sage (`/api/chat`), pointed at a
vision-capable model instead of a text one, so no new pip dependency or
API key is introduced.
if from image any field is not cleared keep it empty and inform the user that this field is not 
clear by the image please fill it.
also,if image contains other than bill,e.g if from image nothing is cleared tell the user nothing is cleared from the image may be wrong image type it mannually.

Scope note: this step does **not** persist the uploaded receipt image
anywhere. The image is read into memory, sent once to the extraction
model, and discarded. Only the resulting expense record (amount,
category, date, description) is ever stored — through the existing
`add_expense()` flow, unchanged. Storing receipt images for later
reference would be a reasonable future step, but is out of scope here.

## Design

* **Palette**
  * Idle drop-zone border/background → `var(--border)` / `var(--paper)` (quiet, matches other inputs at rest)
  * Drag-over / focus state → `var(--accent)` border, `var(--accent-light)` background (same "active" language as `.cat-item:hover`)
  * "Reading your bill…" scanning state → `var(--accent-2)` (Spendly's established AI/insight color — same hue as Sage's ✦ mark and the AI showcase section, so this reads as "AI is doing something" consistently with the rest of the app)
  * Auto-filled field confirmation flash → `var(--accent-light)` background fading out (a quiet "this got filled for you" signal, not a loud animation)
  * Error state → `var(--danger)` text on `var(--danger-light)` background (same tokens as `.auth-error` elsewhere)

* **Typography**
  * Drop-zone label/instructions → `var(--font-body)`, same size/weight as existing `.form-group label`
  * Status text ("Reading your bill…", error messages) → `var(--font-body)`, small caption size (`0.8rem`), `var(--ink-muted)` / `var(--danger)`
  * No new display-serif headline is introduced here — this is a utility control sitting inside an existing form, not a new hero moment. Restraint: the signature is behavioral, not typographic.

* **Layout** — a dashed receipt-slot sits above the existing amount field, like a slot you'd feed a paper receipt into before writing the ledger line by hand; once read, the extracted figures drop into the amount/category/date/description fields already on the page.

  ```
  ┌─────────────────────────────────────────┐
  │  Expense Entry ▾  (existing badge)       │
  │  Add Expense                             │
  │ ───────────────────────────────────────  │
  │  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄  │
  │  ┊   🧾  Drop a bill photo here,       ┊  │
  │  ┊       or click to choose one         ┊  │
  │  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄  │
  │        (state swaps to "Reading…"        │
  │         then to a dismissible result)    │
  │                                           │
  │  Amount   ₹ [ 1,240.00 ]  ← auto-filled   │
  │  Category [Food ✓] [Transport] [Bills]…  │
  │  Date     [ 3 July 2026 ]                │
  │  Note     [ D-Mart — groceries ]         │
  │                                           │
  │  [ Save Expense ]   Cancel                │
  └─────────────────────────────────────────┘
  ```

* **Signature** — the drop-zone doesn't look like a generic file-input widget; it reads as a slot in the ledger itself. On a successful read, each field it touched briefly flashes the same accent-light highlight used for "selected" category tiles, so the page visibly shows *"the ledger just wrote itself"* rather than silently swapping values. This keeps the moment consistent with Spendly's passbook identity instead of introducing a disconnected upload-widget aesthetic.

## Depends on

* Step 03 — Add Expenses (this reuses the Add Expense form, its category tiles, its date picker, and the `add_expense()` POST flow unchanged)
* Step 07 — AI Smart Spending (establishes the Groq-via-OpenAI-client pattern and `GROQ_API_KEY` this step reuses for vision extraction)

## Routes

* `POST /expenses/extract-bill` — accepts a single uploaded image (`multipart/form-data`, field name `bill_image`) from the logged-in user, sends it to the vision model, and returns a JSON object with best-effort extracted fields. Does **not** write to the database. — Logged-in

Request: `multipart/form-data` with `bill_image` (file) and `csrf_token` (form field, checked the same way as every other POST in this app).

Success response (`200`):
```json
{
  "amount": 1240.0,
  "category": "Food",
  "date": "2026-07-03",
  "description": "D-Mart — groceries"
}
```
Any field the model couldn't confidently read comes back as `null` so the frontend leaves that form field untouched for the user to fill in manually.

Error response (`400`/`422`/`500`):
```json
{ "error": "Human-readable reason" }
```

No other new routes. `POST /expenses/add` (existing) is unchanged and remains the only route that actually inserts a row into `expenses`.

## Database changes

No database changes. The extracted fields are only ever submitted through the existing Add Expense form and existing `add_expense(user_id, amount, category, date, description)` helper in `database/db.py` — no new table, column, or write path is introduced.

## Templates

### Create

None.

### Modify

* `templates/add_expense.html` — add a drop-zone block above the "Amount" field group: a labelled dashed drop area (click-to-browse `<input type="file" accept="image/jpeg,image/png,image/webp" hidden>` plus drag-and-drop), a status line under it (idle / "Reading your bill…" / success summary / error message), and wiring to call the new route and pre-fill `#amount`, the matching `.cat-item`, the date picker, and `#description`.

## Files to change

* `app.py`
  * Add `ALLOWED_BILL_IMAGE_TYPES` / a small size guard (e.g. 5 MB) and a helper to validate the upload.
  * Add `_build_bill_extraction_prompt(valid_categories)` alongside the existing `_build_chat_system_prompt`, instructing the model to return **strict JSON only** with keys `amount` (number or null), `category` (must be one of `VALID_CATEGORIES` or null), `date` (`YYYY-MM-DD` or null), `description` (short string or null).
  * Add `POST /expenses/extract-bill`: check login, check CSRF, validate the uploaded file (present, correct type, under the size limit), base64-encode it, call the Groq vision model via the existing `OpenAI(api_key=..., base_url="https://api.groq.com/openai/v1")` client (reusing `GROQ_API_KEY`), parse the model's JSON response defensively (`json.loads` inside try/except — a malformed reply must degrade to an error response, never a 500 crash), validate `category` against `VALID_CATEGORIES` (drop it to `null` if it doesn't match exactly), validate `date` parses with `datetime.strptime(..., "%Y-%m-%d")` (drop to `null` otherwise), and return the JSON described above.
  * **Model name flag:** use a module-level constant, e.g. `BILL_OCR_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"`, for the vision-capable Groq model. Verify this model id is still current on the account's Groq dashboard before shipping — Groq's model lineup changes; if it's been retired, swap in whatever vision-capable chat-completions model is currently available and update this constant.

* `static/js/expense-form.js`
  * Change `initExpenseForm` to `return { selectCategory: selectCategory, selectDate: selectDate };` at the end, so a category/date can be set programmatically from outside without duplicating the tile-toggling and calendar-display logic.
  * No other behavior changes — `add_income.html` and `edit_expense.html` call `initExpenseForm({})` today and ignore the return value, so this is backward compatible.

* `static/css/style.css`
  * Add drop-zone styles (`.bill-drop`, `.bill-drop.dragover`, `.bill-drop-icon`, `.bill-drop-text`, `.bill-status`, `.bill-status.scanning`, `.bill-status.error`) and a brief `@keyframes bill-fill-flash` used on auto-filled fields, all built from existing CSS variables — no new hex values.

## Files to create

* `static/js/bill-upload.js` — new, small, isolated module exposing `window.initBillUpload(formHelpers)`. Owns: click-to-browse, drag-and-drop, client-side type/size validation, the `fetch('/expenses/extract-bill', { method: 'POST', body: formData })` call, the scanning/success/error status states, and populating `#amount`, `#description`, the date picker (via `formHelpers.selectDate`), and the category tiles (via `formHelpers.selectCategory`). Kept out of `expense-form.js` because it's only ever wired up on the Add Expense page, not Add Income or Edit Expense.

## New dependencies

No new dependencies. Reuses the `openai` package and `GROQ_API_KEY` environment variable already present from Step 07 (AI Smart Spending).

## Rules for implementation

Claude **must always** follow these rules:

### Backend

* No SQLAlchemy or any ORM.
* Use SQLite with parameterised queries only.
* Passwords must always be hashed using `werkzeug.security`.
* Reuse existing helper functions whenever possible — the extraction route must **not** duplicate `add_expense()`'s insert logic; it only ever returns data for the existing form to submit normally.
* Never trust the model's output as final: validate `category` against `VALID_CATEGORIES` and `date` against `%Y-%m-%d` server-side before returning it to the client, and let the existing `add_expense` POST handler's own validation be the final gate before anything is written.
* Keep code modular and maintainable.

### Frontend

* **Whenever implementation of this spec is requested and it touches any template or UI, always invoke the built-in `frontend-design` skill before writing template/CSS code.** This applies every time — not just once per spec. Use it to refine the Design section above and to guide the actual markup/CSS.
* All templates must extend `base.html`.
* Use CSS variables only. Never hardcode hex color values.
* Build every page as production-ready, not as a prototype.
* Follow modern SaaS dashboard design principles inspired by products like Stripe, Notion, GitHub, Vercel, and Linear.
* Every page must have a clean, attractive, responsive, and professional UI.
* Maintain consistent spacing, typography, colors, border radius, shadows, and component styling throughout the application.
* Use reusable UI components whenever possible.

### Layout & Responsiveness

* Every page must remain visually appealing regardless of how much content is displayed.
* Design layouts to scale for future growth.
* Assume pages may eventually contain hundreds or thousands of records.
* Never place large amounts of content directly onto the page without proper structure.
* Use responsive containers, cards, grids, sections, and spacing.
* Tables must be responsive and support scrolling or pagination where appropriate.
* Long lists should remain readable and well-organized.
* Forms should have proper spacing and alignment.
* Ensure all pages work well on desktop, tablet, and mobile devices.

### User Experience

* Use modern UI patterns where appropriate:
  * Cards
  * Dashboards
  * Search bars
  * Filters
  * Pagination
  * Empty states
  * Loading states
  * Confirmation dialogs
  * Success/error notifications
  * Responsive tables
  * Well-designed forms
* Forms should include clear validation messages.
* Avoid cluttered interfaces.
* Prioritize readability, accessibility, and usability.
* If a page displays data, design it so future additions do not require redesigning the layout.
* Every new page should feel polished and production-ready.
* Specific to this feature: never block manual entry. If extraction fails for any reason (bad image, model error, missing API key), the user must still be able to fill in the Add Expense form exactly as they could before this step existed.

## Definition of done

* [ ] On the Add Expense page, a drop-zone appears above the Amount field with instructions to drop or click to upload a bill photo.
* [ ] Clicking the drop-zone opens a file picker restricted to image files; dragging an image over it shows a visible hover/dragover state.
* [ ] Uploading a clear photo of a receipt shows a "Reading your bill…" status, then fills in Amount, selects the matching Category tile, sets the Date, and fills the Note field — each newly-filled field briefly highlights.
* [ ] Any field the model could not confidently extract is left blank/unselected instead of guessing something misleading.
* [ ] The user can still edit any pre-filled field before saving — nothing is written to the database until "Save Expense" is clicked, and that click goes through the existing, unchanged `add_expense` POST route.
* [ ] Uploading a non-image file, an oversized file, or a completely unreadable image shows a clear inline error message and never crashes the page or blocks manual entry.
* [ ] If `GROQ_API_KEY` is not configured, uploading a bill shows a clear inline error ("Bill scanning isn't available right now — enter the details manually.") instead of a 500 error, and manual entry still works.
* [ ] Add Income and Edit Expense pages are unaffected — they still load and submit exactly as before.
* [ ] The feature works on mobile viewport widths (drop-zone remains usable via tap-to-browse; camera capture works on devices that support it).
* [ ] No new pip dependency was added to `requirements.txt`.
