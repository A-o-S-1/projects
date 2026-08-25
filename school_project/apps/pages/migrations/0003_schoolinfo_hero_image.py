from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0002_aboutpage_admissioninquiry_admissionspage_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="schoolinfo",
            name="hero_image",
            field=models.ImageField(blank=True, help_text="Optional school/campus photograph shown inside the homepage hero arch.", null=True, upload_to="site/hero/"),
        ),
    ]
