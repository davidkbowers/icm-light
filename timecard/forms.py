import json
from decimal import Decimal, InvalidOperation

from django import forms
from django.core.exceptions import ValidationError


class TimeCardForm(forms.Form):
    employee_name = forms.CharField(max_length=120, label="Employee Name")
    week_ending = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Week Ending",
    )
    project_name_location = forms.CharField(max_length=180, label="Project Name and Location", required=False)
    entries_json = forms.CharField(widget=forms.HiddenInput())
    prepared_by = forms.CharField(max_length=120, label="Prepared By")
    prepared_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), label="Prepared Date")
    approved_by = forms.CharField(max_length=120, label="Approved By", required=False)
    approved_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), label="Approved Date", required=False)
    entered_by = forms.CharField(max_length=120, label="Approved and Entered By", required=False)
    entered_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), label="Entered Date", required=False)
    notes = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Comments for payroll or approvals"}),
        required=False,
    )
    certify = forms.BooleanField(
        label="I certify that this time card is accurate.",
    )

    DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

    @staticmethod
    def _decimal_value(value):
        try:
            return Decimal(str(value or 0))
        except (InvalidOperation, TypeError, ValueError):
            raise ValidationError("Hour values must be numeric.")

    def clean(self):
        cleaned_data = super().clean()
        entries_raw = cleaned_data.get("entries_json")
        if not entries_raw:
            raise ValidationError("Please add at least one labor line before submitting.")

        try:
            entries = json.loads(entries_raw)
        except json.JSONDecodeError as exc:
            raise ValidationError("Could not read the entered hours.") from exc

        if not isinstance(entries, list) or len(entries) < 1:
            raise ValidationError("At least one labor line is required.")

        has_hours = False
        sanitized_entries = []
        for item in entries:
            job_number = str(item.get("job_number", "")).strip()[:30]
            phase = str(item.get("phase", "")).strip()[:30]
            category = str(item.get("category", "")).strip()[:60]
            description = str(item.get("description", "")).strip()[:120]

            values = {}
            for day in self.DAY_KEYS:
                st_key = f"{day}_st"
                ot_key = f"{day}_ot"
                values[st_key] = self._decimal_value(item.get(st_key))
                values[ot_key] = self._decimal_value(item.get(ot_key))

            values["vacation"] = self._decimal_value(item.get("vacation"))
            values["holiday"] = self._decimal_value(item.get("holiday"))
            values["comp_time"] = self._decimal_value(item.get("comp_time"))
            values["funeral_bereavement"] = self._decimal_value(item.get("funeral_bereavement"))
            values["jury_duty"] = self._decimal_value(item.get("jury_duty"))

            if any(value < 0 for value in values.values()):
                raise ValidationError("Hour values cannot be negative.")

            straight_time = sum(values[f"{day}_st"] for day in self.DAY_KEYS)
            overtime = sum(values[f"{day}_ot"] for day in self.DAY_KEYS)
            line_total = (
                straight_time
                + overtime
                + values["vacation"]
                + values["holiday"]
                + values["comp_time"]
                + values["funeral_bereavement"]
                + values["jury_duty"]
            )

            if line_total > 0:
                has_hours = True

            sanitized = {
                "job_number": job_number,
                "phase": phase,
                "category": category,
                "description": description,
                "straight_time": float(round(straight_time, 2)),
                "overtime": float(round(overtime, 2)),
                "vacation": float(round(values["vacation"], 2)),
                "holiday": float(round(values["holiday"], 2)),
                "comp_time": float(round(values["comp_time"], 2)),
                "funeral_bereavement": float(round(values["funeral_bereavement"], 2)),
                "jury_duty": float(round(values["jury_duty"], 2)),
            }
            for day in self.DAY_KEYS:
                sanitized[f"{day}_st"] = float(round(values[f"{day}_st"], 2))
                sanitized[f"{day}_ot"] = float(round(values[f"{day}_ot"], 2))

            sanitized_entries.append(sanitized)

        if not has_hours:
            raise ValidationError("Please enter at least one hour on the time card.")

        cleaned_data["entries"] = sanitized_entries
        return cleaned_data
