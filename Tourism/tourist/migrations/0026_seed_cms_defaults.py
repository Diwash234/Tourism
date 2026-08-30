from django.db import migrations


def seed(apps, schema_editor):
    Page=apps.get_model('tourist','ManagedPage'); Section=apps.get_model('tourist','ContentSection'); Setting=apps.get_model('tourist','SiteSetting'); Nav=apps.get_model('tourist','ManagedNavigationItem')
    Setting.objects.get_or_create(key='branding',defaults={'value':{'site_title':'Digital Nepal Tourism Platform','tagline':'Explore the Heart of the Himalayas','primary_color':'#1f6b4d','secondary_color':'#c2603a','footer_text':'Digital Nepal Tourism Platform'}})
    page,_=Page.objects.get_or_create(key='home',defaults={'route':'/','title':'Digital Nepal Tourism Platform','meta_description':'Explore Nepal safely and intelligently.'})
    Section.objects.get_or_create(page=page,key='hero',defaults={'title':'Explore Local Wonders, Travel Smart & Safe','subtitle':'Discover destinations across all 7 provinces.','display_order':1})
    defaults=[('Home','/'),('Destinations','/destinations'),('Travel Planning','/trip-planner'),('Budget','/budget-estimator'),('Safety','/emergency'),('Recommendations','/recommendation'),('About','/about')]
    for i,(label,route) in enumerate(defaults): Nav.objects.get_or_create(location='navbar',route=route,defaults={'label':label,'display_order':i})


def reverse(apps,schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies=[('tourist','0025_feedbackmessage_managednavigationitem_managedpage_and_more')]
    operations=[migrations.RunPython(seed,reverse)]
