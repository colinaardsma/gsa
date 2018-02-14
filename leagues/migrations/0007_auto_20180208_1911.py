# Generated by Django 2.0.2 on 2018-02-08 19:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leagues', '0006_auto_20180206_2313'),
    ]

    operations = [
        migrations.AlterField(
            model_name='league',
            name='avg_sgp',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='avg_sgp_avg',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='b_dollar_per_fvaaz',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='b_dollar_per_fvaaz_avg',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='b_player_pool_mult',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='b_player_pool_mult_avg',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='batter_budget_pct',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='batter_budget_pct_avg',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='batters_over_zero_dollars',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='batters_over_zero_dollars_avg',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='era_sgp',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='era_sgp_avg',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='hr_sgp',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='hr_sgp_avg',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='k_sgp',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='k_sgp_avg',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='money_spent_on_batters',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='money_spent_on_batters_avg',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='money_spent_on_pitchers',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='money_spent_on_pitchers_avg',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='one_dollar_batters',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='one_dollar_batters_avg',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='one_dollar_pitchers',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='one_dollar_pitchers_avg',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='ops_sgp',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='ops_sgp_avg',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='p_dollar_per_fvaaz',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='p_dollar_per_fvaaz_avg',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='p_player_pool_mult',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='p_player_pool_mult_avg',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='pitcher_budget_pct',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='pitcher_budget_pct_avg',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='pitchers_over_zero_dollars',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='pitchers_over_zero_dollars_avg',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='r_sgp',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='r_sgp_avg',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='rbi_sgp',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='rbi_sgp_avg',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='sb_sgp',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='sb_sgp_avg',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='sv_sgp',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='sv_sgp_avg',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='total_money_spent',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='total_money_spent_avg',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='w_sgp',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='w_sgp_avg',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='whip_sgp',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='whip_sgp_avg',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
