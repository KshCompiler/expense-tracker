(function (window) {
    var ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
    var MAX_BYTES = 5 * 1024 * 1024;

    window.initBillUpload = function (formHelpers, options) {
        options = options || {};
        var endpoint     = options.endpoint || '/expenses/extract-bill';
        var fieldKey     = options.fieldKey || 'category';
        var scanningText = options.scanningText || 'Reading…';
        var emptyMessage = options.emptyMessage ||
            "Nothing could be read from that image — make sure it's clear, or enter the details manually.";
        var successMessage = options.successMessage ||
            'Filled in from your upload — check it over before saving.';

        var dropZone  = document.getElementById('bill-drop');
        if (!dropZone) return;

        var fileInput  = document.getElementById('bill-file-input');
        var statusEl   = document.getElementById('bill-drop-status');
        var idleText   = statusEl ? statusEl.textContent : '';
        var amountEl   = document.getElementById('amount');
        var descEl     = document.getElementById('description');
        var dpTrigger  = document.getElementById('dp-trigger');
        var csrfInput  = document.querySelector('#expense-form [name="csrf_token"]');
        var csrfToken  = csrfInput ? csrfInput.value : '';

        function flash(el) {
            if (!el) return;
            el.classList.remove('bill-filled');
            /* Force reflow so the animation restarts if the same field fills twice in a row. */
            void el.offsetWidth;
            el.classList.add('bill-filled');
            setTimeout(function () { el.classList.remove('bill-filled'); }, 1200);
        }

        function setScanning(isScanning) {
            dropZone.classList.toggle('scanning', isScanning);
            dropZone.setAttribute('aria-busy', isScanning ? 'true' : 'false');
            statusEl.textContent = isScanning ? scanningText : idleText;
        }

        function applyExtraction(data) {
            var filled  = [];
            var missing = [];

            if (data.amount != null) {
                amountEl.value = data.amount;
                flash(amountEl.closest('.amount-slip'));
                filled.push('amount');
            } else {
                missing.push('amount');
            }

            var fieldValue = data[fieldKey];
            if (fieldValue) {
                formHelpers.selectCategory(fieldValue);
                flash(document.querySelector('.cat-item[data-value="' + fieldValue + '"]'));
                filled.push(fieldKey);
            } else {
                missing.push(fieldKey);
            }

            if (data.date) {
                var parts = data.date.split('-');
                var d = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
                formHelpers.selectDate(d);
                flash(dpTrigger);
                filled.push('date');
            } else {
                missing.push('date');
            }

            if (data.description) {
                descEl.value = data.description;
                flash(descEl);
            }

            if (filled.length === 0) {
                showToast(emptyMessage, 'error');
            } else if (missing.length > 0) {
                showToast('Filled in ' + filled.join(', ') + ' — please check ' + missing.join(', ') + ' yourself.', 'warning');
            } else {
                showToast(successMessage, 'success');
            }
        }

        function handleFile(file) {
            if (!file) return;

            if (ALLOWED_TYPES.indexOf(file.type) === -1) {
                showToast('Please upload a JPG, PNG, or WEBP image.', 'error');
                return;
            }
            if (file.size > MAX_BYTES) {
                showToast('That image is too large — please use a photo under 5MB.', 'error');
                return;
            }

            setScanning(true);

            var formData = new FormData();
            formData.append('bill_image', file);
            formData.append('csrf_token', csrfToken);

            fetch(endpoint, { method: 'POST', body: formData })
                .then(function (res) {
                    return res.json().then(function (data) {
                        return { ok: res.ok, data: data };
                    });
                })
                .then(function (result) {
                    setScanning(false);
                    if (!result.ok) {
                        showToast((result.data && result.data.error) || "Couldn't read that image.", 'error');
                        return;
                    }
                    applyExtraction(result.data);
                })
                .catch(function () {
                    setScanning(false);
                    showToast("Couldn't reach the server — please enter the details manually.", 'error');
                });
        }

        dropZone.addEventListener('click', function () {
            if (!dropZone.classList.contains('scanning')) fileInput.click();
        });

        dropZone.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                if (!dropZone.classList.contains('scanning')) fileInput.click();
            }
        });

        fileInput.addEventListener('change', function () {
            handleFile(fileInput.files[0]);
            fileInput.value = '';
        });

        ['dragenter', 'dragover'].forEach(function (evt) {
            dropZone.addEventListener(evt, function (e) {
                e.preventDefault();
                dropZone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(function (evt) {
            dropZone.addEventListener(evt, function (e) {
                e.preventDefault();
                dropZone.classList.remove('dragover');
            });
        });

        dropZone.addEventListener('drop', function (e) {
            var file = e.dataTransfer.files && e.dataTransfer.files[0];
            handleFile(file);
        });
    };
})(window);
