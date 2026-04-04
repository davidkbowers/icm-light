from django.db import models


class TimeCard(models.Model):
	class Status(models.TextChoices):
		PENDING = "pending", "Pending"
		APPROVED = "approved", "Approved"
		REJECTED = "rejected", "Rejected"

	employee_name = models.CharField(max_length=120)
	week_ending = models.DateField()
	project_name_location = models.CharField(max_length=180, blank=True)

	prepared_by = models.CharField(max_length=120)
	prepared_date = models.DateField()
	approved_by = models.CharField(max_length=120, blank=True)
	approved_date = models.DateField(null=True, blank=True)
	entered_by = models.CharField(max_length=120, blank=True)
	entered_date = models.DateField(null=True, blank=True)

	notes = models.TextField(blank=True)
	certified = models.BooleanField(default=False)

	status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
	approver_comment = models.TextField(blank=True)
	reviewed_at = models.DateTimeField(null=True, blank=True)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"{self.employee_name} - Week Ending {self.week_ending}"


class TimeCardLine(models.Model):
	timecard = models.ForeignKey(TimeCard, on_delete=models.CASCADE, related_name="lines")
	line_order = models.PositiveIntegerField(default=1)

	job_number = models.CharField(max_length=30, blank=True)
	phase = models.CharField(max_length=30, blank=True)
	category = models.CharField(max_length=60, blank=True)
	description = models.CharField(max_length=120, blank=True)

	mon_st = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	mon_ot = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	tue_st = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	tue_ot = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	wed_st = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	wed_ot = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	thu_st = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	thu_ot = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	fri_st = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	fri_ot = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	sat_st = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	sat_ot = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	sun_st = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	sun_ot = models.DecimalField(max_digits=6, decimal_places=2, default=0)

	vacation = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	holiday = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	comp_time = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	funeral_bereavement = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	jury_duty = models.DecimalField(max_digits=6, decimal_places=2, default=0)

	class Meta:
		ordering = ["line_order", "id"]

	def __str__(self):
		return f"{self.timecard_id} Line {self.line_order}"
