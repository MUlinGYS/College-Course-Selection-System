from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("applications", "0001_initial"),
        ("rounds", "0002_round_indexes"),
    ]

    operations = [
        migrations.AddField(
            model_name="courseapplication",
            name="round",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="course_applications",
                to="rounds.round",
            ),
        ),
        migrations.AddIndex(
            model_name="courseapplication",
            index=models.Index(fields=["round", "status"], name="app_round_status_idx"),
        ),
    ]
