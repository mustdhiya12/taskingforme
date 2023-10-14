# Generated by Django 4.1.3 on 2023-10-11 07:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ojinvoice',
            name='transaction_model',
            field=models.CharField(default='', max_length=30),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ojinvoice',
            name='transaction_ref_id',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='paymentoption',
            name='category',
            field=models.CharField(choices=[('va', 'virtual account'), ('emoney', 'e-money'), ('cc', 'credit card'), ('qris', 'qris'), ('otc', 'over the counter')], max_length=12),
        ),
    ]
