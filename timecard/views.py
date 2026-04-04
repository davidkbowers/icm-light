from io import BytesIO

from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas

from .forms import TimeCardForm
from .models import TimeCard, TimeCardLine

DAY_KEYS = [
	("mon", "Mon"),
	("tue", "Tue"),
	("wed", "Wed"),
	("thu", "Thu"),
	("fri", "Fri"),
	("sat", "Sat"),
	("sun", "Sun"),
]


def _pdf_columns():
	columns = [
		("Job", 38),
		("Phase", 34),
		("Category", 56),
		("Description", 110),
	]
	for _, day_label in DAY_KEYS:
		columns.append((f"{day_label} ST", 24))
		columns.append((f"{day_label} OT", 24))
	columns += [
		("Vac", 22),
		("Hol", 22),
		("Comp", 24),
		("Fun", 22),
		("Jury", 22),
		("Tot", 26),
	]
	return columns


def _pdf_row_values(row):
	values = [
		row["job_number"],
		row["phase"],
		row["category"],
		row["description"],
	]
	for day_key, _ in DAY_KEYS:
		values.append(f"{row[f'{day_key}_st']:.2f}")
		values.append(f"{row[f'{day_key}_ot']:.2f}")

	line_total = row["straight_time"] + row["overtime"] + row["vacation"] + row["holiday"] + row["comp_time"] + row["funeral_bereavement"] + row["jury_duty"]
	values += [
		f"{row['vacation']:.2f}",
		f"{row['holiday']:.2f}",
		f"{row['comp_time']:.2f}",
		f"{row['funeral_bereavement']:.2f}",
		f"{row['jury_duty']:.2f}",
		f"{line_total:.2f}",
	]
	return values


def _build_totals(entries):
	straight_time = sum(row["straight_time"] for row in entries)
	overtime = sum(row["overtime"] for row in entries)
	vacation = sum(row["vacation"] for row in entries)
	holiday = sum(row["holiday"] for row in entries)
	comp_time = sum(row["comp_time"] for row in entries)
	funeral_bereavement = sum(row["funeral_bereavement"] for row in entries)
	jury_duty = sum(row["jury_duty"] for row in entries)
	grand = (
		straight_time
		+ overtime
		+ vacation
		+ holiday
		+ comp_time
		+ funeral_bereavement
		+ jury_duty
	)

	daily = {}
	for day_key, day_label in DAY_KEYS:
		st = sum(row[f"{day_key}_st"] for row in entries)
		ot = sum(row[f"{day_key}_ot"] for row in entries)
		daily[day_key] = {"label": day_label, "st": round(st, 2), "ot": round(ot, 2), "total": round(st + ot, 2)}

	return {
		"straight_time": round(straight_time, 2),
		"overtime": round(overtime, 2),
		"vacation": round(vacation, 2),
		"holiday": round(holiday, 2),
		"comp_time": round(comp_time, 2),
		"funeral_bereavement": round(funeral_bereavement, 2),
		"jury_duty": round(jury_duty, 2),
		"grand": round(grand, 2),
		"daily": daily,
	}


def _card_entries(card):
	entries = []
	for line in card.lines.all():
		row = {
			"job_number": line.job_number,
			"phase": line.phase,
			"category": line.category,
			"description": line.description,
			"vacation": float(line.vacation),
			"holiday": float(line.holiday),
			"comp_time": float(line.comp_time),
			"funeral_bereavement": float(line.funeral_bereavement),
			"jury_duty": float(line.jury_duty),
		}
		straight_time = 0.0
		overtime = 0.0
		for day_key, _ in DAY_KEYS:
			st = float(getattr(line, f"{day_key}_st"))
			ot = float(getattr(line, f"{day_key}_ot"))
			row[f"{day_key}_st"] = st
			row[f"{day_key}_ot"] = ot
			straight_time += st
			overtime += ot
		row["straight_time"] = round(straight_time, 2)
		row["overtime"] = round(overtime, 2)
		entries.append(row)
	return entries


def _save_lines(card, entries):
	for index, row in enumerate(entries, start=1):
		line = TimeCardLine(
			timecard=card,
			line_order=index,
			job_number=row["job_number"],
			phase=row["phase"],
			category=row["category"],
			description=row["description"],
			vacation=row["vacation"],
			holiday=row["holiday"],
			comp_time=row["comp_time"],
			funeral_bereavement=row["funeral_bereavement"],
			jury_duty=row["jury_duty"],
		)
		for day_key, _ in DAY_KEYS:
			setattr(line, f"{day_key}_st", row[f"{day_key}_st"])
			setattr(line, f"{day_key}_ot", row[f"{day_key}_ot"])
		line.save()


def timecard_view(request):
	form = TimeCardForm(request.POST or None)
	context = {"form": form, "submitted": False}

	if request.method == "POST" and form.is_valid():
		entries = form.cleaned_data["entries"]
		with transaction.atomic():
			card = TimeCard.objects.create(
				employee_name=form.cleaned_data["employee_name"],
				week_ending=form.cleaned_data["week_ending"],
				project_name_location=form.cleaned_data["project_name_location"],
				prepared_by=form.cleaned_data["prepared_by"],
				prepared_date=form.cleaned_data["prepared_date"],
				approved_by=form.cleaned_data["approved_by"],
				approved_date=form.cleaned_data["approved_date"],
				entered_by=form.cleaned_data["entered_by"],
				entered_date=form.cleaned_data["entered_date"],
				notes=form.cleaned_data["notes"],
				certified=form.cleaned_data["certify"],
			)
			_save_lines(card, entries)

		context.update(
			{
				"submitted": True,
				"form": TimeCardForm(),
				"saved": {
					"employee_name": card.employee_name,
					"week_ending": card.week_ending,
					"project_name_location": card.project_name_location,
					"prepared_by": card.prepared_by,
					"prepared_date": card.prepared_date,
					"approved_by": card.approved_by,
					"approved_date": card.approved_date,
					"entered_by": card.entered_by,
					"entered_date": card.entered_date,
					"notes": card.notes,
					"entries": entries,
					"totals": _build_totals(entries),
					"card_id": card.id,
				},
			}
		)

	return render(request, "timecard/timecard_form.html", context)


def dashboard_view(request):
	status_filter = request.GET.get("status", "all")
	cards = TimeCard.objects.prefetch_related("lines").all()
	if status_filter in {TimeCard.Status.PENDING, TimeCard.Status.APPROVED, TimeCard.Status.REJECTED}:
		cards = cards.filter(status=status_filter)

	card_rows = []
	for card in cards:
		entries = _card_entries(card)
		card_rows.append({"card": card, "totals": _build_totals(entries), "line_count": len(entries)})

	return render(
		request,
		"timecard/dashboard.html",
		{
			"card_rows": card_rows,
			"status_filter": status_filter,
			"status_choices": ["all", TimeCard.Status.PENDING, TimeCard.Status.APPROVED, TimeCard.Status.REJECTED],
		},
	)


def dashboard_detail_view(request, pk):
	card = get_object_or_404(TimeCard.objects.prefetch_related("lines"), pk=pk)

	if request.method == "POST":
		action = request.POST.get("action")
		comment = request.POST.get("approver_comment", "").strip()
		if action in {"approve", "reject"}:
			card.status = TimeCard.Status.APPROVED if action == "approve" else TimeCard.Status.REJECTED
			card.approver_comment = comment
			card.reviewed_at = timezone.now()
			card.save(update_fields=["status", "approver_comment", "reviewed_at", "updated_at"])
			return redirect("timecard:dashboard-detail", pk=card.pk)

	entries = _card_entries(card)
	return render(
		request,
		"timecard/dashboard_detail.html",
		{
			"card": card,
			"entries": entries,
			"totals": _build_totals(entries),
			"day_keys": DAY_KEYS,
		},
	)


def timecard_print_preview_view(request, pk):
	card = get_object_or_404(TimeCard.objects.prefetch_related("lines"), pk=pk)
	entries = _card_entries(card)
	totals = _build_totals(entries)
	columns = _pdf_columns()
	rows = [_pdf_row_values(row) for row in entries[:20]]
	total_width = sum(width for _, width in columns)

	return render(
		request,
		"timecard/print_preview.html",
		{
			"card": card,
			"totals": totals,
			"columns": columns,
			"rows": rows,
			"total_width": total_width,
		},
	)


def timecard_pdf_view(request, pk):
	card = get_object_or_404(TimeCard.objects.prefetch_related("lines"), pk=pk)
	entries = _card_entries(card)
	totals = _build_totals(entries)

	buffer = BytesIO()
	pdf = canvas.Canvas(buffer, pagesize=landscape(letter))
	width, height = landscape(letter)

	pdf.setTitle(f"TimeCard_{card.id}")
	pdf.setFont("Helvetica-Bold", 13)
	pdf.drawCentredString(width / 2, height - 28, "WEEKLY EMPLOYEE TIME SHEET")

	pdf.setFont("Helvetica", 8)
	pdf.drawString(18, height - 50, f"Employee Name: {card.employee_name}")
	pdf.drawString(260, height - 50, f"Week Ending: {card.week_ending}")
	pdf.drawString(430, height - 50, f"Project Name and Location: {card.project_name_location or '-'}")

	y_top = height - 72
	row_h = 16
	x = 12

	columns = _pdf_columns()

	total_width = sum(w for _, w in columns)
	x = (width - total_width) / 2
	pdf.rect(x, y_top - row_h, total_width, row_h)

	curr_x = x
	pdf.setFont("Helvetica-Bold", 6)
	for label, col_w in columns:
		pdf.line(curr_x, y_top - row_h, curr_x, y_top)
		pdf.drawCentredString(curr_x + col_w / 2, y_top - 11, label)
		curr_x += col_w
	pdf.line(curr_x, y_top - row_h, curr_x, y_top)

	y = y_top - row_h
	pdf.setFont("Helvetica", 6)
	for row in entries[:20]:
		y -= row_h
		pdf.rect(x, y, total_width, row_h)
		values = _pdf_row_values(row)

		curr_x = x
		for idx, (_, col_w) in enumerate(columns):
			pdf.line(curr_x, y, curr_x, y + row_h)
			text = str(values[idx])
			if idx <= 3:
				pdf.drawString(curr_x + 1.5, y + 5, text[: int(col_w / 3)])
			else:
				pdf.drawRightString(curr_x + col_w - 1.5, y + 5, text)
			curr_x += col_w
		pdf.line(curr_x, y, curr_x, y + row_h)

	y -= 24
	pdf.setFont("Helvetica-Bold", 8)
	pdf.drawString(18, y, "Daily Totals / Current")
	pdf.setFont("Helvetica", 8)
	pdf.drawString(18, y - 12, f"Straight Time: {totals['straight_time']:.2f}    Overtime: {totals['overtime']:.2f}    Vacation: {totals['vacation']:.2f}")
	pdf.drawString(18, y - 24, f"Holiday: {totals['holiday']:.2f}    Comp Time: {totals['comp_time']:.2f}    Funeral/Bereavement: {totals['funeral_bereavement']:.2f}")
	pdf.drawString(18, y - 36, f"Jury Duty: {totals['jury_duty']:.2f}    Grand Total: {totals['grand']:.2f}")

	pdf.drawString(430, y - 12, f"Prepared By: {card.prepared_by} ({card.prepared_date})")
	pdf.drawString(430, y - 24, f"Approved By: {card.approved_by or '-'} ({card.approved_date or '-'})")
	pdf.drawString(430, y - 36, f"Entered By: {card.entered_by or '-'} ({card.entered_date or '-'})")

	pdf.showPage()
	pdf.save()

	buffer.seek(0)
	response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
	response["Content-Disposition"] = f'attachment; filename="timecard-{card.id}.pdf"'
	return response
