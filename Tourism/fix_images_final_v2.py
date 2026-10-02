#!/usr/bin/env python
"""
Fix images in data.json by copying from verified_tourism_data.json
"""
import json

def main():
    # Load verified snapshot
    with open(r'C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\verified_tourism_data.json', 'r', encoding='utf-8') as f:
        verified = json.load(f)
    
    # Load current data.json
    with open(r'C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    verified_records = verified['records']
    
    # Build verified destination lookup by pk
    dest_names = {}  # pk -> name
    dest_by_slug = {}  # slug -> pk
    for r in verified['records']:
        if r.get('model') == 'tourist.destination':
            pk = str(r['pk'])
            name = r['fields'].get('name', '').lower().strip()
            slug = r['fields'].get('slug', '').lower().strip()
            if name:
                dest_names[pk] = name
            if slug:
                dest_by_slug[slug] = pk
    
    # Build verified images by destination pk
    images_by_dest = {}
    for r in verified['records']:
        if r.get('model') == 'tourist.destinationimage':
            dest_pk = str(r['fields']['destination'])
            if dest_pk not in images_by_dest:
                images_by_dest[dest_pk] = []
            images_by_dest[dest_pk].append(r['fields'])
    
    # Build reverse lookup: destination name -> verified images
    images_by_name = {}
    for pk, images in images_by_dest.items():
        name = dest_names.get(pk, '').lower()
        if name:
            images_by_name[name] = images
    
    print(f"Verified images for {len(images_by_dest)} destination IDs")
    print(f"Mapped by name: {len(images_by_name)} destinations")
    
    # Load current data.json
    with open(r'C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    destinations = data.get('destinations', {})
    print(f"Total destinations in data.json: {len(destinations)}")
    
    # Build lookup by name and slug
    dest_by_name = {}
    dest_by_slug = {}
    for pk, dest in destinations.items():
        name = dest.get('name', '').lower().strip()
        slug = dest.get('slug', '').lower().strip()
        if name:
            dest_by_name[name.lower()] = dest
        if slug:
            dest_by_slug[slug.lower()] = dest
    
    updated = 0
    for pk, dest in destinations.items():
        name = dest.get('name', '').lower().strip()
        slug = dest.get('slug', '').lower().strip()
        
        # Try to find verified images
        verified_imgs = None
        
        # Try by name
        if name in images_by_name:
            verified_imgs = images_by_name[name]
        elif slug in images_by_name:
            verified_imgs = images_by_name[slug]
        else:
            # Fuzzy match
            for vn, imgs in images_by_name.items():
                if name and name in vn:
                    verified_imgs = imgs
                    break
                if slug and slug in vn:
                    verified_imgs = imgs
                    break
        
        if verified_imgs:
            # Convert verified images to data.json format
            new_images = []
            for img in verified_imgs[:3]:
                if img.get('external_url'):
                    new_images.append({
                        'id': int(pk) * 1000 + len(dest.get('images', [])),
                        'url': img['external_url'],
                        'caption': img.get('caption', ''),
                        'is_cover': img.get('is_cover', False),
                        'status': 'approved'
                    })
            if new_images:
                dest['images'] = new_images
                name_safe = dest.get('name', 'Unknown').encode('ascii', 'ignore').decode('ascii')
                print(f"  Updated {name_safe} with {len(new_images)} verified images")
                updated += 1
    
    print(f"Updated {updated} destinations with verified images")
    
    # For remaining destinations without images, add placeholder
    for pk, dest in destinations.items():
        if not dest.get('images'):
            dest['images'] = [{
                'id': int(pk) * 1000,
                'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Nepal_Mount_Everest.jpg/960px-Nepal_Mount_Everest.jpg',
                'caption': f"{dest.get('name', 'Nepal')} - View",
                'is_cover': True,
                'status': 'approved'
            }]
    
    # Save
    with open(r'C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Saved!")

if __name__ == '__main__':
    main()