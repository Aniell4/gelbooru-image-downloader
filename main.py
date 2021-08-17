import os
import asyncio

try:
 from pygelbooru import Gelbooru
except ImportError:
 os.system('pip install pygelbooru')
 from pygelbooru import Gelbooru

try:
 import aiosonic
except ImportError:
 os.system('pip install aiosonic')
 import aiosonic

async def get_images(tag_list):
    gelbooru = Gelbooru('API_KEY', 'USER_ID')
    result = await gelbooru.search_posts(tags=tag_list, limit = 1000)
    return result

async def main():
    tags = input("Enter Gelbooru Tags: ")
    tag_list = tags.split(' ')
   
    client = aiosonic.HTTPClient()
    for image in await get_images(tag_list):
        image_url = str(image)
        filename = image_url.split("/")[-1]

        r = await client.get(image_url)

        if r.status_code == 200:
            
            newpath = str(tags) 
            if not os.path.exists(newpath):
                os.makedirs(newpath)
            with open(newpath+'/'+filename,'wb') as f:
                f.write(await r.content())
                
            print('Image sucessfully Downloaded: ',filename)
        else:
            print('Image Couldn\'t be retreived')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
