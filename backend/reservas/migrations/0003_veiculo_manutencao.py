from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reservas", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="veiculo",
            name="em_manutencao",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="veiculo",
            name="motivo_manutencao",
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
