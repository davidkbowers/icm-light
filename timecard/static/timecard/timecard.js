(function () {
    const dayKeys = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];
    const dayLabels = {
        mon: "Mon",
        tue: "Tue",
        wed: "Wed",
        thu: "Thu",
        fri: "Fri",
        sat: "Sat",
        sun: "Sun",
    };

    const form = document.getElementById("timecard-form");
    if (!form) return;

    const lineItems = document.getElementById("line-items");
    const addLineButton = document.getElementById("add-line-btn");
    const hiddenEntries = document.getElementById("id_entries_json");
    const reviewBox = document.getElementById("review-box");

    const stepButtons = Array.from(document.querySelectorAll(".step"));
    const panels = Array.from(document.querySelectorAll(".step-panel"));
    const nextButtons = Array.from(document.querySelectorAll("[data-next-step]"));
    const prevButtons = Array.from(document.querySelectorAll("[data-prev-step]"));

    const metricStraightTime = document.getElementById("sum-straight-time");
    const metricOvertime = document.getElementById("sum-overtime");
    const metricVacation = document.getElementById("sum-vacation");
    const metricHoliday = document.getElementById("sum-holiday");
    const metricCompTime = document.getElementById("sum-comp-time");
    const metricFuneral = document.getElementById("sum-funeral");
    const metricJury = document.getElementById("sum-jury");
    const metricGrand = document.getElementById("sum-grand");
    const dayMetric = {
        mon: document.getElementById("day-mon"),
        tue: document.getElementById("day-tue"),
        wed: document.getElementById("day-wed"),
        thu: document.getElementById("day-thu"),
        fri: document.getElementById("day-fri"),
        sat: document.getElementById("day-sat"),
        sun: document.getElementById("day-sun"),
    };

    const rows = [];
    let currentStep = 1;

    function toNumber(value) {
        const parsed = Number.parseFloat(value);
        return Number.isFinite(parsed) && parsed >= 0 ? parsed : 0;
    }

    function createLineCard() {
        const wrapper = document.createElement("article");
        wrapper.className = "day-card";
        const lineIndex = rows.length + 1;

        const straightId = `line-${lineIndex}-straight`;
        const overtimeId = `line-${lineIndex}-overtime`;
        const vacationId = `line-${lineIndex}-vacation`;
        const holidayId = `line-${lineIndex}-holiday`;
        const compId = `line-${lineIndex}-comp`;
        const funeralId = `line-${lineIndex}-funeral`;
        const juryId = `line-${lineIndex}-jury`;

        const weekColumns = dayKeys
            .map(
                (day) => `
                <div class="week-col">
                    <h5>${dayLabels[day]}</h5>
                    <label>ST<input type="number" min="0" step="0.25" data-field="${day}_st" value="0"></label>
                    <label>OT<input type="number" min="0" step="0.25" data-field="${day}_ot" value="0"></label>
                </div>`
            )
            .join("");

        wrapper.innerHTML = `
            <div class="day-head">
                <h4>Labor Line ${lineIndex}</h4>
                <span class="day-hours">0.00 hrs</span>
            </div>
            <div class="field-grid line-meta-grid">
                <label>Job Number <input type="text" data-field="job_number" placeholder="000000"></label>
                <label>Phase <input type="text" data-field="phase" placeholder="0000"></label>
                <label>Category <input type="text" data-field="category" placeholder="Labor / Burden / Current Labor"></label>
                <label>Description <input type="text" data-field="description" placeholder="Work performed"></label>
            </div>
            <div class="week-grid">${weekColumns}</div>
            <div class="hours-grid seven">
                <label for="${straightId}">Straight Time
                    <input id="${straightId}" type="number" data-field="straight_time" value="0" readonly>
                </label>
                <label for="${overtimeId}">Overtime
                    <input id="${overtimeId}" type="number" data-field="overtime" value="0" readonly>
                </label>
                <label for="${vacationId}">Vacation
                    <input id="${vacationId}" type="number" min="0" step="0.25" data-field="vacation" value="0">
                </label>
                <label for="${holidayId}">Holiday
                    <input id="${holidayId}" type="number" min="0" step="0.25" data-field="holiday" value="0">
                </label>
                <label for="${compId}">Comp Time
                    <input id="${compId}" type="number" min="0" step="0.25" data-field="comp_time" value="0">
                </label>
                <label for="${funeralId}">Funeral/Bereavement
                    <input id="${funeralId}" type="number" min="0" step="0.25" data-field="funeral_bereavement" value="0">
                </label>
                <label for="${juryId}">Jury Duty
                    <input id="${juryId}" type="number" min="0" step="0.25" data-field="jury_duty" value="0">
                </label>
            </div>
            <div class="panel-actions compact">
                <button type="button" class="btn btn-soft remove-line">Remove Line</button>
            </div>
        `;

        const row = {
            element: wrapper,
            dayTotal: wrapper.querySelector(".day-hours"),
            job_number: wrapper.querySelector('[data-field="job_number"]'),
            phase: wrapper.querySelector('[data-field="phase"]'),
            category: wrapper.querySelector('[data-field="category"]'),
            description: wrapper.querySelector('[data-field="description"]'),
            straight_time: wrapper.querySelector('[data-field="straight_time"]'),
            overtime: wrapper.querySelector('[data-field="overtime"]'),
            day_st: {},
            day_ot: {},
            vacation: wrapper.querySelector('[data-field="vacation"]'),
            holiday: wrapper.querySelector('[data-field="holiday"]'),
            comp_time: wrapper.querySelector('[data-field="comp_time"]'),
            funeral_bereavement: wrapper.querySelector('[data-field="funeral_bereavement"]'),
            jury_duty: wrapper.querySelector('[data-field="jury_duty"]'),
        };

        dayKeys.forEach((day) => {
            row.day_st[day] = wrapper.querySelector(`[data-field="${day}_st"]`);
            row.day_ot[day] = wrapper.querySelector(`[data-field="${day}_ot"]`);
        });

        rows.push(row);

        [
            row.job_number,
            row.phase,
            row.category,
            row.description,
            row.vacation,
            row.holiday,
            row.comp_time,
            row.funeral_bereavement,
            row.jury_duty,
        ].forEach((input) => {
            input.addEventListener("input", updateSummary);
        });

        dayKeys.forEach((day) => {
            row.day_st[day].addEventListener("input", updateSummary);
            row.day_ot[day].addEventListener("input", updateSummary);
        });

        wrapper.querySelector(".remove-line").addEventListener("click", () => {
            const index = rows.indexOf(row);
            if (index >= 0) {
                rows.splice(index, 1);
                wrapper.remove();
                updateSummary();
            }
        });

        lineItems.appendChild(wrapper);
    }

    function setStep(stepNumber) {
        currentStep = stepNumber;
        stepButtons.forEach((button) => {
            button.classList.toggle("is-active", Number(button.dataset.stepTarget) === currentStep);
        });

        panels.forEach((panel) => {
            panel.classList.toggle("is-active", Number(panel.dataset.step) === currentStep);
        });
    }

    function buildPayload() {
        return rows.map((row) => {
            const vacation = toNumber(row.vacation.value);
            const holiday = toNumber(row.holiday.value);
            const comp_time = toNumber(row.comp_time.value);
            const funeral_bereavement = toNumber(row.funeral_bereavement.value);
            const jury_duty = toNumber(row.jury_duty.value);

            let straight_time = 0;
            let overtime = 0;
            const payload = {
                job_number: row.job_number.value.trim(),
                phase: row.phase.value.trim(),
                category: row.category.value.trim(),
                description: row.description.value.trim(),
                vacation,
                holiday,
                comp_time,
                funeral_bereavement,
                jury_duty,
            };
            dayKeys.forEach((day) => {
                const st = toNumber(row.day_st[day].value);
                const ot = toNumber(row.day_ot[day].value);
                payload[`${day}_st`] = st;
                payload[`${day}_ot`] = ot;
                straight_time += st;
                overtime += ot;
            });

            payload.straight_time = straight_time;
            payload.overtime = overtime;
            return {
                ...payload,
            };
        });
    }

    function updateSummary() {
        const payload = buildPayload();
        const totals = payload.reduce(
            (acc, row) => {
                acc.straight_time += row.straight_time;
                acc.overtime += row.overtime;
                acc.vacation += row.vacation;
                acc.holiday += row.holiday;
                acc.comp_time += row.comp_time;
                acc.funeral_bereavement += row.funeral_bereavement;
                acc.jury_duty += row.jury_duty;
                return acc;
            },
            {
                straight_time: 0,
                overtime: 0,
                vacation: 0,
                holiday: 0,
                comp_time: 0,
                funeral_bereavement: 0,
                jury_duty: 0,
                mon: 0,
                tue: 0,
                wed: 0,
                thu: 0,
                fri: 0,
                sat: 0,
                sun: 0,
            }
        );

        rows.forEach((row) => {
            let weeklySt = 0;
            let weeklyOt = 0;
            dayKeys.forEach((day) => {
                const daily = toNumber(row.day_st[day].value) + toNumber(row.day_ot[day].value);
                totals[day] += daily;
                weeklySt += toNumber(row.day_st[day].value);
                weeklyOt += toNumber(row.day_ot[day].value);
            });
            row.straight_time.value = weeklySt.toFixed(2);
            row.overtime.value = weeklyOt.toFixed(2);

            const lineHours =
                weeklySt
                + weeklyOt
                + toNumber(row.vacation.value)
                + toNumber(row.holiday.value)
                + toNumber(row.comp_time.value)
                + toNumber(row.funeral_bereavement.value)
                + toNumber(row.jury_duty.value);
            row.dayTotal.textContent = `${lineHours.toFixed(2)} hrs`;
        });

        metricStraightTime.textContent = totals.straight_time.toFixed(2);
        metricOvertime.textContent = totals.overtime.toFixed(2);
        metricVacation.textContent = totals.vacation.toFixed(2);
        metricHoliday.textContent = totals.holiday.toFixed(2);
        metricCompTime.textContent = totals.comp_time.toFixed(2);
        metricFuneral.textContent = totals.funeral_bereavement.toFixed(2);
        metricJury.textContent = totals.jury_duty.toFixed(2);
        dayKeys.forEach((day) => {
            dayMetric[day].textContent = totals[day].toFixed(2);
        });
        metricGrand.textContent = (
            totals.straight_time
            + totals.overtime
            + totals.vacation
            + totals.holiday
            + totals.comp_time
            + totals.funeral_bereavement
            + totals.jury_duty
        ).toFixed(2);

        const activeLines = payload.filter(
            (x) =>
                x.straight_time
                + x.overtime
                + x.vacation
                + x.holiday
                + x.comp_time
                + x.funeral_bereavement
                + x.jury_duty
                > 0
        ).length;
        reviewBox.innerHTML = `
            <strong>${activeLines}</strong> labor line(s) with reported hours.<br>
            <span>Prepared and approval fields complete the workflow before submission.</span>
        `;

        hiddenEntries.value = JSON.stringify(payload);
    }

    addLineButton.addEventListener("click", () => {
        createLineCard();
        updateSummary();
    });

    createLineCard();
    createLineCard();

    nextButtons.forEach((button) => {
        button.addEventListener("click", () => setStep(Math.min(3, currentStep + 1)));
    });

    prevButtons.forEach((button) => {
        button.addEventListener("click", () => setStep(Math.max(1, currentStep - 1)));
    });

    stepButtons.forEach((button) => {
        button.addEventListener("click", () => setStep(Number(button.dataset.stepTarget)));
    });

    form.addEventListener("submit", updateSummary);

    setStep(1);
    updateSummary();
})();
