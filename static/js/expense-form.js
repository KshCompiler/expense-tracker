(function (window) {
    window.initExpenseForm = function (opts) {
        opts = opts || {};
        var preselectedCategory = opts.preselectedCategory || null;
        var preselectedDate     = opts.preselectedDate     || null;

        /* ── Category selection ── */
        var catInput = document.getElementById('category');
        var catItems = document.querySelectorAll('.cat-item');

        function selectCategory(value) {
            catItems.forEach(function (item) {
                item.classList.toggle('selected', item.dataset.value === value);
            });
            catInput.value = value;
        }

        catItems.forEach(function (item) {
            item.addEventListener('click', function () {
                selectCategory(item.dataset.value);
            });
        });

        if (preselectedCategory) {
            selectCategory(preselectedCategory.trim());
        }

        /* ── Calendar ── */
        var dateInput = document.getElementById('date');
        var dpTrigger = document.getElementById('dp-trigger');
        var dpDisplay = document.getElementById('dp-display');
        var calPopup  = document.getElementById('cal-popup');
        var calGrid   = document.getElementById('cal-grid');
        var calLabel  = document.getElementById('cal-month-label');
        var prevBtn   = document.getElementById('cal-prev');
        var nextBtn   = document.getElementById('cal-next');
        var todayBtn  = document.getElementById('cal-today-btn');

        var MONTHS = ['January','February','March','April','May','June',
                      'July','August','September','October','November','December'];

        var cursor   = new Date();
        var selected = null;

        function localToday() {
            var t = new Date();
            return new Date(t.getFullYear(), t.getMonth(), t.getDate());
        }

        function toValue(d) {
            var y  = d.getFullYear();
            var m  = String(d.getMonth() + 1).padStart(2, '0');
            var dd = String(d.getDate()).padStart(2, '0');
            return y + '-' + m + '-' + dd;
        }

        function toDisplay(d) {
            return d.getDate() + ' ' + MONTHS[d.getMonth()] + ' ' + d.getFullYear();
        }

        function renderCalendar() {
            var year  = cursor.getFullYear();
            var month = cursor.getMonth();
            calLabel.textContent = MONTHS[month] + ' ' + year;

            var firstWeekday = new Date(year, month, 1).getDay();
            var daysInMonth  = new Date(year, month + 1, 0).getDate();
            var today        = localToday();

            calGrid.innerHTML = '';

            for (var i = 0; i < firstWeekday; i++) {
                var empty = document.createElement('div');
                empty.className = 'cal-day empty';
                calGrid.appendChild(empty);
            }

            for (var d = 1; d <= daysInMonth; d++) {
                var btn  = document.createElement('button');
                btn.type = 'button';
                btn.className = 'cal-day';
                btn.textContent = d;

                var thisDate = new Date(year, month, d);

                if (thisDate.getTime() === today.getTime()) {
                    btn.classList.add('today');
                }
                if (selected && thisDate.getTime() === selected.getTime()) {
                    btn.classList.add('selected');
                }

                btn.addEventListener('click', (function (date) {
                    return function () { selectDate(date); };
                })(thisDate));

                calGrid.appendChild(btn);
            }
        }

        function selectDate(date) {
            selected = date;
            dateInput.value = toValue(date);
            dpDisplay.textContent = toDisplay(date);
            dpDisplay.classList.remove('dp-placeholder');
            closeCalendar();
        }

        function openCalendar() {
            calPopup.hidden = false;
            dpTrigger.setAttribute('aria-expanded', 'true');
            renderCalendar();
        }

        function closeCalendar() {
            calPopup.hidden = true;
            dpTrigger.setAttribute('aria-expanded', 'false');
        }

        dpTrigger.addEventListener('click', function () {
            calPopup.hidden ? openCalendar() : closeCalendar();
        });

        prevBtn.addEventListener('click', function () {
            cursor = new Date(cursor.getFullYear(), cursor.getMonth() - 1, 1);
            renderCalendar();
        });

        nextBtn.addEventListener('click', function () {
            cursor = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1);
            renderCalendar();
        });

        todayBtn.addEventListener('click', function () {
            cursor = localToday();
            selectDate(localToday());
        });

        document.addEventListener('click', function (e) {
            if (!calPopup.hidden &&
                !calPopup.contains(e.target) &&
                e.target !== dpTrigger &&
                !dpTrigger.contains(e.target)) {
                closeCalendar();
            }
        });

        /* Pre-select date (YYYY-MM-DD) or default to today */
        if (preselectedDate) {
            var parts   = preselectedDate.split('-');
            var preDate = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
            cursor = new Date(preDate.getFullYear(), preDate.getMonth(), 1);
            selectDate(preDate);
        } else {
            selectDate(localToday());
        }

        /* Validate on submit */
        document.getElementById('expense-form').addEventListener('submit', function (e) {
            if (!catInput.value) {
                e.preventDefault();
                alert('Please select a category.');
                return;
            }
            if (!dateInput.value) {
                e.preventDefault();
                alert('Please select a date.');
                return;
            }
        });
    };
})(window);
