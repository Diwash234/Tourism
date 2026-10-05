import django, os, sys, re
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tourism.settings')
sys.path.insert(0, r'C:\Users\ADMIN\Desktop\Chatbot\Tourism')
django.setup()
from tourist.models import Destination, DestinationImage

adjusted = 0
for d in Destination.objects.all().iterator():
    photos = list(d.gallery.filter(verification_status=DestinationImage.ImageStatus.APPROVED, is_verified=True).order_by('-is_cover', 'ordering', 'id'))
    if not photos:
        continue
    # ensure exactly one cover flag on the first approved verified photo
    if not photos[0].is_cover:
        for p in photos:
            if p.is_cover:
                p.is_cover = False
                p.save(update_fields=['is_cover', 'updated_at'])
        photos[0].is_cover = True
        photos[0].save(update_fields=['is_cover', 'updated_at'])
        adjusted += 1
print('destinations cover-flag corrected:', adjusted)
